"""Authentication service abstractions."""
from __future__ import annotations

import abc
from contextlib import contextmanager
from typing import Iterator, Optional

import httpx
import pyotp

from ..config import CredentialSet, TokenBundle


class AuthService(abc.ABC):
    """Base class for provider specific authentication flows."""

    def __init__(self, credentials: CredentialSet) -> None:
        self.credentials = credentials

    def _generate_totp(self) -> Optional[str]:
        secret = self.credentials.totp_secret
        if not secret:
            return None
        return pyotp.TOTP(secret).now()

    @contextmanager
    def _client(self) -> Iterator[httpx.Client]:
        with httpx.Client(timeout=20.0) as client:
            yield client

    @abc.abstractmethod
    def generate_access_token(self) -> TokenBundle:
        """Automate the login flow and return the generated tokens."""
