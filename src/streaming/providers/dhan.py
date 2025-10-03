"""Dhan HQ websocket streamer implementation."""
from __future__ import annotations

from .base import WebsocketDataStreamer
from ..config import Instrument, StreamConfig


class DhanHQStreamer(WebsocketDataStreamer):
    """Streams market data from the DhanHQ websocket feed."""

    websocket_url = "wss://api-feed.dhan.co/v1/ws/marketData"

    async def _subscribe(self, config: StreamConfig) -> None:
        instruments = [self._instrument_payload(inst) for inst in config.instruments]
        payload = {
            "authorization": self.credentials.access_token,
            "subscription": {
                "mode": "FULL",
                "instruments": instruments,
            },
        }
        await self.send_json(payload)

    def _instrument_payload(self, instrument: Instrument) -> dict:
        token = instrument.token or instrument.symbol
        exchange_segment = instrument.exchange or "NSE_EQ"
        return {
            "exchangeSegment": exchange_segment,
            "exchangeInstrumentID": token,
        }
