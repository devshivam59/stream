"""Access token automation for Upstox."""
from __future__ import annotations

import urllib.parse

from bs4 import BeautifulSoup

from .base import AuthService
from ..config import TokenBundle


class UpstoxAuthService(AuthService):
    """Automates the Upstox OAuth login flow to retrieve access tokens."""

    AUTHORIZE_URL = "https://api.upstox.com/index/oauth/authorize"
    TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
    LOGIN_URL = "https://api.upstox.com/v2/login"  # credential verification
    OTP_URL = "https://api.upstox.com/v2/login/otp/verification"

    def generate_access_token(self) -> TokenBundle:  # pragma: no cover - network heavy
        if not (self.credentials.username and self.credentials.password and self.credentials.redirect_uri):
            raise ValueError("Username, password and redirect URI are required for Upstox login")

        params = {
            "client_id": self.credentials.api_key,
            "response_type": "code",
            "redirect_uri": self.credentials.redirect_uri,
        }

        with self._client() as client:
            response = client.get(self.AUTHORIZE_URL, params=params)
            response.raise_for_status()

            csrf_token = response.cookies.get("upstox_csrftoken")
            if not csrf_token:
                soup = BeautifulSoup(response.text, "html.parser")
                csrf_meta = soup.find("meta", attrs={"name": "csrf-token"})
                csrf_token = csrf_meta["content"] if csrf_meta else None
            if not csrf_token:
                raise RuntimeError("Unable to locate CSRF token for Upstox login")

            login_payload = {
                "user_id": self.credentials.username,
                "password": self.credentials.password,
            }
            headers = {"x-csrf-token": csrf_token}
            login_response = client.post(self.LOGIN_URL, json=login_payload, headers=headers)
            login_response.raise_for_status()

            otp = self._generate_totp()
            if otp:
                otp_payload = {
                    "user_id": self.credentials.username,
                    "otp": otp,
                }
                otp_response = client.post(self.OTP_URL, json=otp_payload, headers=headers)
                otp_response.raise_for_status()

            consent_response = client.post(
                self.AUTHORIZE_URL,
                params=params,
                headers=headers,
                data={"scope": "marketdata", "duration": "DAY"},
                follow_redirects=False,
            )
            consent_response.raise_for_status()

            if "location" not in consent_response.headers:
                raise RuntimeError("Authorization redirect missing for Upstox")

            redirect_url = consent_response.headers["location"]
            parsed = urllib.parse.urlparse(redirect_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            if "code" not in query_params:
                raise RuntimeError("Authorization code not present in redirect URL")
            code = query_params["code"][0]

            token_payload = {
                "code": code,
                "client_id": self.credentials.api_key,
                "client_secret": self.credentials.api_secret,
                "redirect_uri": self.credentials.redirect_uri,
                "grant_type": "authorization_code",
            }
            token_response = client.post(self.TOKEN_URL, json=token_payload)
            token_response.raise_for_status()
            token_json = token_response.json()

        access_token = token_json.get("access_token")
        if not access_token:
            raise RuntimeError("Failed to obtain Upstox access token")

        bundle = TokenBundle(
            access_token=access_token,
            refresh_token=token_json.get("refresh_token"),
            expires_in=token_json.get("expires_in"),
            meta=token_json,
        )
        self.credentials.access_token = bundle.access_token
        self.credentials.refresh_token = bundle.refresh_token
        return bundle
