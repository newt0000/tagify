from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

APP_NAME = "Tagify"
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_CONFIG_PATH = CONFIG_DIR / "agent_config.json"
DEV_FILE_NAME = "DEVKEY.json"


def default_config() -> dict[str, Any]:
    return {
        "server_url": "http://24.198.181.134:2455",
        "api_key": "",
        "location_name": "Unconfigured Location",
        "location_code": "unknown",
        "app_version": "1.0.0",
        "printer_name": "",
        "printer_connected": False,
        "enabled": True,
        "heartbeat_interval_seconds": 15,
    }


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default.copy()


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _windows_dev_candidates() -> list[Path]:
    candidates: list[Path] = []

    # Common drive letters
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = Path(f"{letter}:/")
        if root.exists():
            candidates.append(root)

    return candidates


def find_devkey_file() -> Path | None:
    # Windows-friendly scan for a drive root containing DEVKEY.json.
    # If multiple are present, prefer one whose volume label appears to be DEV
    # based on env/path naming; otherwise first match wins.
    for root in _windows_dev_candidates():
        candidate = root / DEV_FILE_NAME
        if candidate.exists():
            return candidate
    return None


def ensure_local_config() -> dict[str, Any]:
    cfg = load_json(LOCAL_CONFIG_PATH, default_config())
    changed = False

    defaults = default_config()
    for k, v in defaults.items():
        if k not in cfg:
            cfg[k] = v
            changed = True

    if changed or not LOCAL_CONFIG_PATH.exists():
        save_json(LOCAL_CONFIG_PATH, cfg)

    return cfg


def get_active_config() -> tuple[dict[str, Any], str, Path]:
    """
    Returns:
      (config_dict, source_name, source_path)

    source_name is one of:
      - 'dev'
      - 'local'
    """
    dev_path = find_devkey_file()
    if dev_path is not None:
        cfg = load_json(dev_path, default_config())
        defaults = default_config()
        changed = False
        for k, v in defaults.items():
            if k not in cfg:
                cfg[k] = v
                changed = True

        # Only write back if it is actually the DEV file and fields are missing
        if changed:
            try:
                save_json(dev_path, cfg)
            except Exception:
                pass

        return cfg, "dev", dev_path

    cfg = ensure_local_config()
    return cfg, "local", LOCAL_CONFIG_PATH


def write_api_key(api_key: str) -> tuple[dict[str, Any], str, Path]:
    """
    Writes the key to the active config source.
    If DEVKEY.json is present, write there.
    Otherwise write to local config.
    """
    cfg, source_name, source_path = get_active_config()
    cfg["api_key"] = api_key.strip()
    save_json(source_path, cfg)
    return cfg, source_name, source_path