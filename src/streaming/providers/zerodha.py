"""Zerodha Kite Connect websocket streamer."""
from __future__ import annotations

from .base import WebsocketDataStreamer
from ..config import Instrument, StreamConfig


class ZerodhaStreamer(WebsocketDataStreamer):
    """Streams market data from the Zerodha Kite websocket."""

    websocket_url = "wss://ws.kite.trade/"

    async def _subscribe(self, config: StreamConfig) -> None:
        tokens = [self._instrument_token(inst) for inst in config.instruments]
        # handshake with auth token
        auth_payload = {
            "a": "authenticate",
            "v": {
                "api_key": self.credentials.api_key,
                "access_token": self.credentials.access_token,
            },
        }
        await self.send_json(auth_payload)
        payload = {
            "a": "subscribe",
            "v": tokens,
        }
        await self.send_json(payload)

    def _instrument_token(self, instrument: Instrument) -> int:
        token = instrument.token
        if token is None:
            raise ValueError("Zerodha streaming requires the numeric instrument token")
        return int(token)
