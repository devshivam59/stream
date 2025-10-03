"""Configuration models and utilities for the streaming services."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence


@dataclass(slots=True)
class Instrument:
    """Represents a symbol/instrument to stream."""

    symbol: str
    exchange: Optional[str] = None
    token: Optional[str] = None


@dataclass(slots=True)
class StreamConfig:
    """Configuration for a streaming session."""

    instruments: Sequence[Instrument]
    on_message: Callable[[dict], None]
    on_error: Optional[Callable[[Exception], None]] = None
    on_disconnect: Optional[Callable[[], None]] = None
    reconnect: bool = True
    max_retries: int = 5
    retry_backoff: float = 2.0


@dataclass(slots=True)
class CredentialSet:
    """Credentials used for both streaming and authentication flows."""

    api_key: str
    api_secret: str
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    totp_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


@dataclass(slots=True)
class TokenBundle:
    """Represents a bundle of tokens generated during login."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    meta: dict = field(default_factory=dict)


