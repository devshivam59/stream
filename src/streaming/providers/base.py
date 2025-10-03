"""Base classes for streaming providers."""
from __future__ import annotations

import abc
import asyncio
import json
from typing import Any, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from ..config import CredentialSet, Instrument, StreamConfig


class StreamingError(RuntimeError):
    """Raised when a streaming provider experiences an unrecoverable error."""


class BaseDataStreamer(abc.ABC):
    """Abstract base class for all provider streamers."""

    def __init__(self, credentials: CredentialSet) -> None:
        self.credentials = credentials

    @abc.abstractmethod
    async def stream(self, config: StreamConfig) -> None:
        """Start streaming data using the supplied configuration."""


class WebsocketDataStreamer(BaseDataStreamer):
    """Helper base class for providers that use websocket feeds."""

    websocket_url: str

    def __init__(self, credentials: CredentialSet) -> None:
        super().__init__(credentials)
        self._ws: Optional[WebSocketClientProtocol] = None
        self._lock = asyncio.Lock()

    async def stream(self, config: StreamConfig) -> None:  # pragma: no cover - network heavy
        retries = 0
        while True:
            try:
                await self._connect()
                await self._subscribe(config)
                await self._listen(config)
                if config.on_disconnect:
                    config.on_disconnect()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - runtime safety
                if config.on_error:
                    config.on_error(exc)
                if not config.reconnect or retries >= config.max_retries:
                    raise StreamingError("Streaming stopped due to repeated failures") from exc
                await asyncio.sleep(config.retry_backoff * (2 ** retries))
                retries += 1
            else:
                break
            finally:
                await self._disconnect()

    async def _connect(self) -> None:
        async with self._lock:
            if self._ws and not self._ws.closed:
                return
            self._ws = await websockets.connect(self.websocket_url, extra_headers=self._headers())

    async def _disconnect(self) -> None:
        async with self._lock:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            self._ws = None

    async def _listen(self, config: StreamConfig) -> None:
        assert self._ws is not None
        async for message in self._ws:
            payload = self._parse_message(message)
            config.on_message(payload)

    async def send_json(self, payload: Dict[str, Any]) -> None:
        assert self._ws is not None
        await self._ws.send(json.dumps(payload))

    async def send_text(self, payload: str) -> None:
        assert self._ws is not None
        await self._ws.send(payload)

    def _headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "streaming-client/1.0"}
        if self.credentials.access_token:
            headers["Authorization"] = f"Bearer {self.credentials.access_token}"
        return headers

    @abc.abstractmethod
    async def _subscribe(self, config: StreamConfig) -> None:
        """Send the subscription message once connected."""

    def _parse_message(self, message: str) -> Dict[str, Any]:
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return {"raw": message}
