"""Upstox market data streamer implementation."""
from __future__ import annotations

import uuid

from .base import WebsocketDataStreamer
from ..config import Instrument, StreamConfig


class UpstoxStreamer(WebsocketDataStreamer):
    """Streams market data from the Upstox websocket feed."""

    websocket_url = "wss://socket-v2.upstox.com/feed/market-data-streamer/v2"

    async def _subscribe(self, config: StreamConfig) -> None:
        instrument_keys = [self._instrument_key(inst) for inst in config.instruments]
        payload = {
            "guid": str(uuid.uuid4()),
            "method": "sub",
            "data": {
                "mode": "full",
                "instrumentKeys": instrument_keys,
            },
        }
        await self.send_json(payload)

    def _instrument_key(self, instrument: Instrument) -> str:
        if instrument.token:
            return instrument.token
        if instrument.exchange:
            return f"{instrument.exchange}:{instrument.symbol}"
        return instrument.symbol
