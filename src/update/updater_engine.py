from pathlib import Path
import shutil
import time
from typing import Callable
import zipfile

from src.update.artifacts import validate_update_archive


REQUIRED_INSTALL_FILES = ("PoENavi.exe", "PoENaviUpdater.exe")


class UpdateApplyError(RuntimeError):
    def __init__(self, message: str, backup: Path | None = None):
        super().__init__(message)
        self.backup = backup

    def user_message(self) -> str:
        if self.backup is None:
            return str(self)
        return f"{self}\n\nTarget folder:\n{self.backup}"


def retry_transient_file_operation(
    operation: Callable[[], object],
    attempts: int = 10,
    delay: float = 1.0,
    sleep=time.sleep,
):
    """Retry Windows file operations that can briefly fail during AV scans."""
    for attempt in range(attempts):
        try:
            return operation()
        except PermissionError:
            if attempt == attempts - 1:
                raise
            sleep(delay)


def wait_for_process_exit(
    pid: int,
    timeout: float,
    process_running: Callable[[int], bool],
    sleep=time.sleep,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_running(pid):
            return True
        sleep(0.2)
    return not process_running(pid)


def _validate_install_directory(path: Path, label: str) -> None:
    if not path.is_dir():
        detail = "is not a folder"
    else:
        missing = [name for name in REQUIRED_INSTALL_FILES if not (path / name).is_file()]
        if not missing:
            return
        detail = f"Missing files: {', '.join(missing)}"

    if label == "The existing backup":
        message = (
            f"{label} could not be safely verified, so the update was cancelled."
            f"\n({detail})\n\n"
            "How to fix:\n"
            "1. Close this window.\n"
            "2. Move the target folder below out of the PoENavi folder."
            " You do not need to delete it.\n"
            "3. Start PoENavi and run the update again.\n\n"
            "Because safety could not be confirmed, no files were deleted or changed."
        )
    else:
        message = (
            f"{label} could not be verified, so the update was cancelled."
            f"\n({detail})\n\n"
            "How to fix:\n"
            "1. Close this window.\n"
            "2. Download the official PoENavi.zip again.\n"
            "3. Extract the ZIP to a new folder and run PoENavi.exe.\n\n"
            "The current folder has not been changed."
        )
    raise UpdateApplyError(message, path)


def _next_stale_backup_path(backup: Path, timestamp: str) -> Path:
    base = backup.with_name(f"{backup.name}-old-{timestamp}")
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = backup.with_name(f"{base.name}-{suffix}")
        suffix += 1
    return candidate


def apply_update(
    archive: Path,
    install_dir: Path,
    work_dir: Path,
    launcher: Callable[[Path], object],
    startup_check: Callable[[object], bool] = lambda _process: True,
    timestamp: Callable[[], str] = lambda: time.strftime("%Y%m%d-%H%M%S"),
) -> Path:
    archive = archive.resolve()
    install_dir = install_dir.resolve()
    work_dir = work_dir.resolve()
    validate_update_archive(archive)

    stage = work_dir / "stage"
    backup = install_dir.with_name(f"{install_dir.name}.backup")
    failed = install_dir.with_name(f"{install_dir.name}.failed")
    shutil.rmtree(stage, ignore_errors=True)
    _validate_install_directory(install_dir, "Current install location")
    if failed.exists():
        raise UpdateApplyError(
            "A failure folder from a previous update still exists, "
            "so the update was cancelled.\n\n"
            "How to fix:\n"
            "1. Close this window.\n"
            "2. Move the target folder below out of the PoENavi folder."
            " You do not need to delete it.\n"
            "3. Start PoENavi and run the update again.\n\n"
            "For safety, the failure folder was not deleted automatically.",
            failed,
        )

    stage.mkdir(parents=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(stage)

    wrapped_replacement = stage / "PoENavi"
    replacement = (
        wrapped_replacement
        if (wrapped_replacement / "PoENavi.exe").is_file()
        else stage
    )
    if not (replacement / "PoENavi.exe").is_file():
        raise UpdateApplyError("Updated PoENavi.exe is missing")

    stale_backup = None
    if backup.exists():
        _validate_install_directory(backup, "The existing backup")
        stale_backup = _next_stale_backup_path(backup, timestamp())
        try:
            retry_transient_file_operation(lambda: backup.rename(stale_backup))
        except Exception as exc:
            raise UpdateApplyError(
                "The update was cancelled because the existing backup could not be moved."
                f"\n(Details from Windows: {exc})\n\n"
                "How to fix:\n"
                "1. Close this window.\n"
                "2. Wait for OneDrive sync or security software scans to finish.\n"
                "3. Start PoENavi and run the update again.\n"
                "4. If this keeps happening, restart Windows and try again.\n\n"
                "No files were deleted or changed.",
                backup,
            ) from exc

    backup_created = False
    try:
        retry_transient_file_operation(lambda: install_dir.rename(backup))
        backup_created = True
        shutil.move(str(replacement), str(install_dir))
        process = launcher(install_dir / "PoENavi.exe")
        if not startup_check(process):
            raise RuntimeError("The updated PoENavi exited right after starting")
        if stale_backup is not None:
            shutil.rmtree(stale_backup, ignore_errors=True)
        return backup
    except Exception as exc:
        if backup_created and install_dir.exists():
            if failed.exists():
                shutil.rmtree(failed)
            retry_transient_file_operation(lambda: install_dir.rename(failed))
        if backup_created and backup.exists():
            retry_transient_file_operation(lambda: backup.rename(install_dir))
        if stale_backup is not None and stale_backup.exists() and not backup.exists():
            retry_transient_file_operation(lambda: stale_backup.rename(backup))
        raise UpdateApplyError(
            "The update failed, so the previous version of PoENavi was restored."
            f"\n(Details: {exc})\n\n"
            "How to fix:\n"
            "1. Close this window.\n"
            "2. Check that the current PoENavi.exe starts.\n"
            "3. If it starts, run the update again.\n"
            "4. If it keeps failing, please report it along with the contents of this window.",
            install_dir,
        ) from exc
