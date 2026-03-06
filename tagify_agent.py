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

APP_NAME = "Tagify"
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = CONFIG_DIR / "agent_config.json"
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


def ensure_config() -> dict[str, Any]:
    default = {
        "server_url": "http://24.198.181.134:2455",
        "api_key": "",
        "location_name": "Unconfigured Location",
        "location_code": "unknown",
        "app_version": "1.0.0",
        "printer_name": "",
        "printer_connected": False,
        "enabled": True,
        "heartbeat_interval_seconds": DEFAULT_INTERVAL_SECONDS,
    }

    config = load_json(CONFIG_PATH, default)
    changed = False

    for k, v in default.items():
        if k not in config:
            config[k] = v
            changed = True

    if changed or not CONFIG_PATH.exists():
        save_json(CONFIG_PATH, config)

    return config


def build_payload() -> dict[str, Any]:
    state = ensure_state()
    config = ensure_config()

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

def sync_location_from_server(config: dict[str, Any]) -> dict[str, Any]:
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
            return config

        data = resp.json()

        if not data.get("ok"):
            return config

        changed = False

        if config.get("location_name") != data["location_name"]:
            config["location_name"] = data["location_name"]
            changed = True

        if config.get("location_code") != data["location_code"]:
            config["location_code"] = data["location_code"]
            changed = True

        if changed:
            print("[agent] updating location info from server")
            save_json(CONFIG_PATH, config)

    except Exception as e:
        print("[agent] location sync failed:", e)

    return config

def main() -> None:
    print("[agent] Started...")

    ensure_state()
    ensure_config()

    while True:
        config = ensure_config()

        config = sync_location_from_server(config)

        if config.get("enabled", True):
            payload = build_payload()
            send_heartbeat(config, payload)
        else:
            print("[agent] disabled in config")

        interval = int(config.get("heartbeat_interval_seconds", DEFAULT_INTERVAL_SECONDS))
        print("[agent] loop tick")
        print("[agent] config =", config)
        print("[agent] next heartbeat in", max(15, interval), "seconds")
        time.sleep(max(15, interval))


if __name__ == "__main__":
    main()