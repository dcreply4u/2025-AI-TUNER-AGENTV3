from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, Optional

import requests


class CloudSync:
    """Minimal REST client for pushing telemetry to a cloud API."""

    def __init__(
        self,
        endpoint: str = "https://api.example.com/telemetry",
        api_key: Optional[str] = None,
        timeout: float = 5.0,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout

    def upload(self, payload: Mapping[str, Any]) -> bool:
        headers: MutableMapping[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            response = requests.post(
                self.endpoint,
                data=json.dumps(payload),
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:  # pragma: no cover - network
            print(f"[CloudSync] Error uploading payload: {exc}")
            return False


__all__ = ["CloudSync"]

