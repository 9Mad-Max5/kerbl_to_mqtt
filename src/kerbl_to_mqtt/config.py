from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceSelector:
    device_type: str
    device_id: str | None = None
    name: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DeviceSelector":
        device_type = str(value.get("type", "")).strip()
        if not device_type:
            raise ValueError("Each device selector needs a non-empty 'type'")
        device_id = str(value["id"]).strip() if value.get("id") else None
        name = str(value["name"]).strip() if value.get("name") else None
        if not device_id and not name:
            raise ValueError("Each device selector needs either 'id' or 'name'")
        if device_id and name:
            raise ValueError("A device selector cannot contain both 'id' and 'name'")
        return cls(device_type=device_type, device_id=device_id, name=name)


@dataclass(frozen=True)
class Settings:
    kerbl_email: str
    kerbl_password: str
    kerbl_base_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_tls: bool
    mqtt_topic_prefix: str
    poll_interval_seconds: int
    devices: tuple[DeviceSelector, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        devices_raw = os.getenv("KERBL_DEVICES", "[]")
        try:
            devices = tuple(DeviceSelector.from_dict(item) for item in json.loads(devices_raw))
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError("KERBL_DEVICES must be a JSON array") from error
        if not devices:
            raise ValueError("KERBL_DEVICES must contain at least one device")

        poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "900"))
        if poll_interval < 10:
            raise ValueError("POLL_INTERVAL_SECONDS must be at least 10")

        return cls(
            kerbl_email=_required("KERBL_EMAIL"),
            kerbl_password=_required("KERBL_PASSWORD"),
            kerbl_base_url=os.getenv("KERBL_BASE_URL", "https://backend.kerbl-iot.com").rstrip("/"),
            mqtt_host=os.getenv("MQTT_HOST", "mqtt"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            mqtt_username=_optional("MQTT_USERNAME"),
            mqtt_password=_optional("MQTT_PASSWORD"),
            mqtt_tls=_bool_env("MQTT_TLS", False),
            mqtt_topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "kerbl").strip("/") or "kerbl",
            poll_interval_seconds=poll_interval,
            devices=devices,
        )


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
