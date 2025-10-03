"""Access token automation for DhanHQ."""
from __future__ import annotations

from .base import AuthService
from ..config import TokenBundle


class DhanHQAuthService(AuthService):
    """Automates the DhanHQ login flow to obtain an access token."""

    LOGIN_URL = "https://api.dhan.co/login"
    OTP_URL = "https://api.dhan.co/verify"
    TOKEN_URL = "https://api.dhan.co/token"

    def generate_access_token(self) -> TokenBundle:  # pragma: no cover - network heavy
        if not (self.credentials.client_id and self.credentials.username and self.credentials.password):
            raise ValueError("Client ID, username and password are required for Dhan login")

        with self._client() as client:
            login_payload = {
                "client_id": self.credentials.client_id,
                "email": self.credentials.username,
                "password": self.credentials.password,
            }
            login_response = client.post(self.LOGIN_URL, json=login_payload)
            login_response.raise_for_status()
            login_json = login_response.json()
            request_id = login_json.get("request_id")
            if not request_id:
                raise RuntimeError("Dhan login failed to provide a request ID")

            otp = self._generate_totp()
            if not otp:
                raise RuntimeError("Dhan login requires a TOTP secret")

            otp_payload = {"client_id": self.credentials.client_id, "request_id": request_id, "otp": otp}
            otp_response = client.post(self.OTP_URL, json=otp_payload)
            otp_response.raise_for_status()
            otp_json = otp_response.json()

            authorization_code = otp_json.get("authorization_code")
            if not authorization_code:
                raise RuntimeError("Authorization code missing in Dhan verification response")

            token_payload = {
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.api_secret,
                "grant_type": "authorization_code",
                "code": authorization_code,
            }
            token_response = client.post(self.TOKEN_URL, json=token_payload)
            token_response.raise_for_status()
            token_json = token_response.json()

        access_token = token_json.get("access_token")
        if not access_token:
            raise RuntimeError("Failed to obtain Dhan access token")

        bundle = TokenBundle(
            access_token=access_token,
            refresh_token=token_json.get("refresh_token"),
            expires_in=token_json.get("expires_in"),
            meta=token_json,
        )
        self.credentials.access_token = bundle.access_token
        self.credentials.refresh_token = bundle.refresh_token
        return bundle
