"""Factory helpers to construct streamers and auth services."""
from __future__ import annotations

from typing import Dict, Type

from .auth.base import AuthService
from .auth.dhan import DhanHQAuthService
from .auth.upstox import UpstoxAuthService
from .auth.zerodha import ZerodhaAuthService
from .config import CredentialSet
from .providers.base import BaseDataStreamer
from .providers.dhan import DhanHQStreamer
from .providers.upstox import UpstoxStreamer
from .providers.zerodha import ZerodhaStreamer

STREAMER_REGISTRY: Dict[str, Type[BaseDataStreamer]] = {
    "upstox": UpstoxStreamer,
    "dhan": DhanHQStreamer,
    "zerodha": ZerodhaStreamer,
}

AUTH_REGISTRY: Dict[str, Type[AuthService]] = {
    "upstox": UpstoxAuthService,
    "dhan": DhanHQAuthService,
    "zerodha": ZerodhaAuthService,
}


def create_streamer(provider: str, credentials: CredentialSet) -> BaseDataStreamer:
    try:
        streamer_cls = STREAMER_REGISTRY[provider.lower()]
    except KeyError as exc:  # pragma: no cover - guard
        raise ValueError(f"Unsupported provider '{provider}'") from exc
    return streamer_cls(credentials)


def create_auth_service(provider: str, credentials: CredentialSet) -> AuthService:
    try:
        auth_cls = AUTH_REGISTRY[provider.lower()]
    except KeyError as exc:  # pragma: no cover - guard
        raise ValueError(f"Unsupported provider '{provider}'") from exc
    return auth_cls(credentials)
