"""Command line interface for the streaming toolkit."""
from __future__ import annotations

import argparse
import asyncio
from typing import List

from .config import CredentialSet, Instrument, StreamConfig
from .factory import STREAMER_REGISTRY, create_auth_service, create_streamer


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified data streaming CLI")
    parser.add_argument("provider", choices=sorted(STREAMER_REGISTRY.keys()), help="Provider to use")
    parser.add_argument("symbols", nargs="*", help="Symbols or instrument tokens to subscribe")
    parser.add_argument("--exchange", dest="exchange", help="Exchange segment to use for all symbols")
    parser.add_argument("--token", dest="use_token", action="store_true", help="Treat symbols as instrument tokens")
    parser.add_argument("--generate-token", action="store_true", help="Only generate the access token and exit")
    parser.add_argument("--api-key", required=True, help="API key for the provider")
    parser.add_argument("--api-secret", required=True, help="API secret for the provider")
    parser.add_argument("--client-id", help="Client identifier when required (e.g. Dhan)")
    parser.add_argument("--redirect-uri", help="Redirect URI for OAuth based providers")
    parser.add_argument("--username", help="Login username")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--totp-secret", help="TOTP secret for MFA flows")
    return parser


def _build_credentials(args: argparse.Namespace) -> CredentialSet:
    return CredentialSet(
        api_key=args.api_key,
        api_secret=args.api_secret,
        client_id=args.client_id,
        redirect_uri=args.redirect_uri,
        username=args.username,
        password=args.password,
        totp_secret=args.totp_secret,
    )


def _build_instruments(args: argparse.Namespace) -> List[Instrument]:
    instruments = []
    for symbol in args.symbols:
        instrument = Instrument(symbol=symbol)
        if args.use_token:
            instrument.token = symbol
        elif args.exchange:
            instrument.exchange = args.exchange
        instruments.append(instrument)
    return instruments


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI utility
    parser = _build_parser()
    args = parser.parse_args(argv)

    credentials = _build_credentials(args)
    auth_service = create_auth_service(args.provider, credentials)
    token_bundle = auth_service.generate_access_token()
    print(f"Access token: {token_bundle.access_token}")

    if args.generate_token:
        return

    instruments = _build_instruments(args)

    async def _run() -> None:
        streamer = create_streamer(args.provider, credentials)
        config = StreamConfig(
            instruments=instruments,
            on_message=lambda payload: print(payload),
        )
        await streamer.stream(config)

    asyncio.run(_run())


if __name__ == "__main__":  # pragma: no cover
    main()
