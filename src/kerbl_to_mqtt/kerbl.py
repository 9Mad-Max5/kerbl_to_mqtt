from __future__ import annotations

from typing import Any

import requests


class KerblClient:
    API_VERSION = "/api/v0.1"
    DEVICE_TYPE_PATHS = {
        "smartcoop": "smart-coop",
        "smartenergizer": "smart-energizer",
        "smartsatellite": "smart-satellite",
        "smartweather": "weather-station",
        "smarttracker": "smart-tracker",
        "smartmousetrap": "smart-mousetrap",
        "smartsos": "smart-sos",
        "smartlight": "smart-light",
        "smartchickendoor": "smart-chickendoor",
        "smartratgun": "smart-rat-gun",
    }

    def __init__(self, email: str, password: str, base_url: str, session: requests.Session | None = None) -> None:
        self.email = email
        self.password = password
        self.api_base = f"{base_url.rstrip('/')}{self.API_VERSION}"
        self.session = session or requests.Session()
        self.access_token: str | None = None

    def login(self) -> None:
        response = self.session.post(
            f"{self.api_base}/auth/sign-in",
            json={"email": self.email, "password": self.password},
            timeout=30,
        )
        response.raise_for_status()
        self.access_token = response.json().get("accessToken")
        if not self.access_token:
            raise RuntimeError("Kerbl login did not return an access token")

    def list_devices(self) -> dict[str, Any]:
        return self._request("GET", "/device")

    def get_device(self, device_type: str, device_id: str) -> dict[str, Any]:
        path_type = self.DEVICE_TYPE_PATHS.get(device_type.replace("-", "").casefold(), device_type)
        return self._request("GET", f"/device/{path_type}/{device_id}")

    def find_device(self, device_type: str, name: str) -> dict[str, Any]:
        normalized_type = device_type.replace("-", "").casefold()
        matches: list[dict[str, Any]] = []
        for api_type, devices in self.list_devices().items():
            if api_type.replace("-", "").casefold() != normalized_type or not isinstance(devices, list):
                continue
            matches.extend(
                device for device in devices
                if str(device.get("description") or device.get("name") or "").strip().casefold() == name.casefold()
            )
        if len(matches) != 1:
            raise LookupError(f"Expected one Kerbl device named {name!r}, found {len(matches)}")
        return matches[0]

    def _request(self, method: str, endpoint: str) -> dict[str, Any]:
        if not self.access_token:
            self.login()
        response = self.session.request(
            method,
            f"{self.api_base}{endpoint}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json() if response.text else {}
