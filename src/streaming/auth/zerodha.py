"""Access token automation for Zerodha Kite Connect."""
from __future__ import annotations

import hashlib

from .base import AuthService
from ..config import TokenBundle


class ZerodhaAuthService(AuthService):
    """Automates the Zerodha login flow to retrieve the request token and access token."""

    LOGIN_URL = "https://kite.zerodha.com/api/login"
    TWO_FA_URL = "https://kite.zerodha.com/api/twofa"
    SESSION_TOKEN_URL = "https://api.kite.trade/session/token"

    def generate_access_token(self) -> TokenBundle:  # pragma: no cover - network heavy
        if not (self.credentials.username and self.credentials.password and self.credentials.api_secret):
            raise ValueError("Username, password and API secret are required for Zerodha login")

        with self._client() as client:
            login_payload = {
                "user_id": self.credentials.username,
                "password": self.credentials.password,
            }
            login_response = client.post(self.LOGIN_URL, data=login_payload)
            login_response.raise_for_status()
            login_json = login_response.json()
            data = login_json.get("data") or {}
            request_id = data.get("request_id")
            if not request_id:
                raise RuntimeError("Zerodha login failed to provide request_id")

            totp = self._generate_totp()
            if not totp:
                raise RuntimeError("Zerodha login requires a TOTP secret")

            twofa_payload = {
                "user_id": self.credentials.username,
                "request_id": request_id,
                "twofa_type": "app",
                "twofa_value": totp,
            }
            twofa_response = client.post(self.TWO_FA_URL, data=twofa_payload)
            twofa_response.raise_for_status()
            twofa_json = twofa_response.json()
            twofa_data = twofa_json.get("data") or {}
            request_token = twofa_data.get("request_token")
            if not request_token:
                raise RuntimeError("Zerodha two-factor verification failed to return request_token")

            checksum = self._checksum(request_token)
            token_payload = {
                "api_key": self.credentials.api_key,
                "request_token": request_token,
                "checksum": checksum,
            }
            token_response = client.post(self.SESSION_TOKEN_URL, data=token_payload)
            token_response.raise_for_status()
            token_json = token_response.json()

        access_token = token_json.get("data", {}).get("access_token")
        if not access_token:
            raise RuntimeError("Failed to obtain Zerodha access token")

        bundle = TokenBundle(
            access_token=access_token,
            refresh_token=None,
            expires_in=token_json.get("data", {}).get("expires_in"),
            meta=token_json,
        )
        self.credentials.access_token = bundle.access_token
        return bundle

    def _checksum(self, request_token: str) -> str:
        raw = f"{self.credentials.api_key}{request_token}{self.credentials.api_secret}".encode()
        return hashlib.sha256(raw).hexdigest()
