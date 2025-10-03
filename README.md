# Stream

Unified market data streaming toolkit that supports Upstox, DhanHQ and Zerodha Kite Connect. It provides:

* Pluggable websocket streamers for each broker with a single interface.
* Automation services that log in and fetch API access tokens for each broker.
* A lightweight CLI for generating tokens and starting live market data streams.
* A browser-based console to generate and inspect tokens without using the CLI.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Generate an access token for any provider:

```bash
python -m streaming.cli upstox \
  --api-key <API_KEY> \
  --api-secret <API_SECRET> \
  --redirect-uri <REDIRECT_URI> \
  --username <USER_ID> \
  --password <PASSWORD> \
  --totp-secret <BASE32_TOTP_SECRET> \
  --generate-token
```

Start streaming after the token is generated (for providers that require numeric tokens, pass `--token`):

```bash
python -m streaming.cli zerodha 256265 738561 \
  --token \
  --api-key <API_KEY> \
  --api-secret <API_SECRET> \
  --username <USER_ID> \
  --password <PASSWORD> \
  --totp-secret <BASE32_TOTP_SECRET>
```

The CLI prints each market data message as JSON. Custom handlers can be provided programmatically by constructing a `StreamConfig` and passing it to the streamer instances exposed in `streaming.factory`.

### Web token console

Launch the web console if you prefer a graphical interface:

```bash
python -m streaming.web
```

By default the server listens on `http://127.0.0.1:8000`. The single-page UI lets you choose the provider, fill in the required credentials, and submit the form to generate a new access token. The most recent tokens are displayed inline so you can copy them into other systems. Set the `STREAMING_WEB_SECRET` environment variable to override the default Flask session secret when deploying.

## Project Structure

```
src/
  streaming/
    auth/        # Login automation services
    providers/   # Websocket implementations for each broker
    factory.py   # Helpers to construct auth/streaming classes
    cli.py       # Command line entry point
    web/         # Flask app serving the token console
```

All authentication helpers return a `TokenBundle` that contains the generated access token, optional refresh token and metadata. The returned access token is also written back to the provided `CredentialSet` so it can immediately be used to start streaming.
