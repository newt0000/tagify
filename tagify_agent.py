from __future__ import annotations

import json
import os
import socket
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import requests

from config_source import get_active_config

APP_NAME = "Tagify"
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

STATE_PATH = CONFIG_DIR / "agent_state.json"

DEFAULT_INTERVAL_SECONDS = 15


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_state() -> dict[str, Any]:
    state = load_json(STATE_PATH, {})
    changed = False

    if "app_id" not in state:
        state["app_id"] = f"tagify-{uuid.uuid4().hex[:12]}"
        changed = True

    if changed or not STATE_PATH.exists():
        save_json(STATE_PATH, state)

    return state


def sync_location_from_server(config: dict[str, Any], source_path: Path) -> dict[str, Any]:
    server_url = str(config.get("server_url", "")).rstrip("/")
    api_key = str(config.get("api_key", "")).strip()

    if not server_url or not api_key:
        return config

    headers = {
        "X-API-Key": api_key
    }

    try:
        resp = requests.get(
            f"{server_url}/api/key-info",
            headers=headers,
            timeout=10
        )

        if resp.status_code != 200:
            print("[agent] key-info request failed:", resp.status_code, resp.text)
            return config

        data = resp.json()
        if not data.get("ok"):
            print("[agent] key-info response not ok:", data)
            return config

        changed = False

        if config.get("location_name") != data.get("location_name"):
            config["location_name"] = data.get("location_name", config.get("location_name", "Unknown"))
            changed = True

        if config.get("location_code") != data.get("location_code"):
            config["location_code"] = data.get("location_code", config.get("location_code", "unknown"))
            changed = True

        if changed:
            print("[agent] updating location info from server")
            save_json(source_path, config)

    except Exception as e:
        print("[agent] location sync failed:", e)

    return config


def build_payload(config: dict[str, Any]) -> dict[str, Any]:
    state = ensure_state()

    return {
        "app_id": state["app_id"],
        "location_name": config.get("location_name", "Unknown"),
        "location_code": config.get("location_code", "unknown"),
        "machine_name": socket.gethostname(),
        "app_version": config.get("app_version", "1.0.0"),
        "printer_name": config.get("printer_name", ""),
        "printer_connected": bool(config.get("printer_connected", False)),
        "running": True,
        "timestamp": utc_now_iso(),
    }


def send_heartbeat(config: dict[str, Any], payload: dict[str, Any]) -> None:
    server_url = str(config.get("server_url", "")).rstrip("/")
    api_key = str(config.get("api_key", "")).strip()

    if not server_url or not api_key:
        print("[agent] missing server_url or api_key")
        return

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }

    try:
        print("[agent] sending heartbeat...")
        print("[agent] POST", f"{server_url}/api/heartbeat")
        print("[agent] payload =", payload)

        resp = requests.post(
            f"{server_url}/api/heartbeat",
            json=payload,
            headers=headers,
            timeout=10
        )

        print("[agent] heartbeat status =", resp.status_code)
        print("[agent] heartbeat body =", resp.text)

    except Exception as e:
        print("[agent] heartbeat exception:", e)


def main() -> None:
    print("[agent] Started...")
    ensure_state()

    while True:
        config, source_name, source_path = get_active_config()

        config = sync_location_from_server(config, source_path)

        if config.get("enabled", True):
            payload = build_payload(config)
            print(f"[agent] config source = {source_name} ({source_path})")
            send_heartbeat(config, payload)
        else:
            print("[agent] disabled in config")

        interval = int(config.get("heartbeat_interval_seconds", DEFAULT_INTERVAL_SECONDS))
        print("[agent] loop tick")
        print("[agent] next heartbeat in", max(15, interval), "seconds")
        time.sleep(max(15, interval))


if __name__ == "__main__":
    main()