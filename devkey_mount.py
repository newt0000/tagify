from __future__ import annotations

import ctypes
import sys
import json
import os
import subprocess
import time
from pathlib import Path

from PySide6.QtWidgets import QMessageBox, QWidget

IS_WINDOWS = os.name == "nt"

def is_admin() -> bool:
    if not IS_WINDOWS:
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        None,
        1
    )
def _creationflags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run_powershell(ps_script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_script,
        ],
        capture_output=True,
        text=True,
        creationflags=_creationflags(),
    )


def find_devkey_volumes() -> list[dict]:
    """
    Returns a list like:
    [
      {"DriveLetter": "E", "Label": "DEVKEY", "DriveType": "Removable"}
    ]
    """
    if not IS_WINDOWS:
        return []

    ps = r"""
$vols = Get-Volume | Where-Object { $_.FileSystemLabel -eq 'DEVKEY' -and $_.DriveLetter } |
    Select-Object DriveLetter, FileSystemLabel, DriveType
$vols | ConvertTo-Json -Compress
"""
    result = run_powershell(ps)

    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        data = json.loads(result.stdout.strip())
    except Exception:
        return []

    if isinstance(data, dict):
        data = [data]

    out = []
    for row in data:
        out.append({
            "DriveLetter": row.get("DriveLetter", ""),
            "Label": row.get("FileSystemLabel", ""),
            "DriveType": row.get("DriveType", ""),
        })
    return out


def find_vhd_on_volume(drive_letter: str) -> Path | None:
    root = Path(f"{drive_letter}:/")
    if not root.exists():
        return None

    # Prefer root-level VHD/VHDX first
    for ext in ("*.vhd", "*.vhdx"):
        matches = list(root.glob(ext))
        if matches:
            return matches[0]

    # Then search one level down if needed
    for ext in ("**/*.vhd", "**/*.vhdx"):
        matches = list(root.glob(ext))
        if matches:
            return matches[0]

    return None


def is_vhd_attached(vhd_path: Path) -> bool:
    ps = rf"""
$img = Get-DiskImage -ImagePath '{str(vhd_path)}' -ErrorAction SilentlyContinue
if ($img -and $img.Attached) {{ 'true' }} else {{ 'false' }}
"""
    result = run_powershell(ps)
    return result.stdout.strip().lower() == "true"


def mount_vhd(vhd_path: Path) -> tuple[bool, str]:
    if is_vhd_attached(vhd_path):
        return True, "VHD already mounted."

    ps = rf"""
try {{
    Mount-DiskImage -ImagePath '{str(vhd_path)}' -ErrorAction Stop
    'ok'
}} catch {{
    $_.Exception.Message
    exit 1
}}
"""
    result = run_powershell(ps)

    if result.returncode != 0:
        msg = result.stdout.strip() or result.stderr.strip() or "Unknown mount failure."
        return False, msg

    # Wait briefly for Windows to finish attaching
    for _ in range(20):
        if is_vhd_attached(vhd_path):
            return True, "VHD mounted successfully."
        time.sleep(0.25)

    return False, "VHD mount command ran, but attachment was not confirmed."


def _confirm_mount(parent: QWidget | None) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle("Developer Key Found")
    box.setText("Developer tools key has been found would you like to mount this key?")
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.Yes)
    return box.exec() == QMessageBox.Yes


def _show_remove_message(parent: QWidget | None) -> None:
    QMessageBox.information(
        parent,
        "Developer Key Present",
        "Please remove the DEVKEY flash device to open Tagify as client."
    )


def _show_mount_error(parent: QWidget | None, details: str) -> None:
    QMessageBox.critical(
        parent,
        "Mount Failed",
        f"Tagify found a DEVKEY device but could not mount its VHD.\n\nDetails:\n{details}"
    )


def handle_devkey_mount_gate(parent: QWidget | None = None) -> bool:
    """
    Returns:
      True  -> safe to continue launching Tagify
      False -> stop launch
    """
    if not IS_WINDOWS:
        return True

    dev_vols = find_devkey_volumes()
    if not dev_vols:
        return True

    # Pick the first DEVKEY volume that contains a VHD/VHDX
    chosen_vhd = None
    for vol in dev_vols:
        drive_letter = vol.get("DriveLetter", "").strip()
        if not drive_letter:
            continue
        found = find_vhd_on_volume(drive_letter)
        if found is not None:
            chosen_vhd = found
            break

    # DEVKEY volume exists but no VHD found
    if chosen_vhd is None:
        _show_mount_error(parent, "No .vhd or .vhdx file was found on the DEVKEY device.")
        return False

    if not _confirm_mount(parent):
        _show_remove_message(parent)
        return False

    if not is_admin():
        relaunch_as_admin()
        return False

    ok, msg = mount_vhd(chosen_vhd)
    if not ok:
        _show_mount_error(parent, "Administrator permission is required to mount the DEVKEY VHD.")
        return False

    return True