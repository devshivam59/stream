"""Flask application that wraps the authentication services."""
from __future__ import annotations

import os
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, flash, redirect, render_template, request, url_for

from ..config import CredentialSet
from ..factory import AUTH_REGISTRY, create_auth_service

_TOKEN_HISTORY_LIMIT = 20


def _optional_value(form: Dict[str, str], key: str) -> Optional[str]:
    value = (form.get(key) or "").strip()
    return value or None


def _build_credentials(form: Dict[str, str]) -> CredentialSet:
    return CredentialSet(
        api_key=(form.get("api_key", "").strip()),
        api_secret=(form.get("api_secret", "").strip()),
        client_id=_optional_value(form, "client_id"),
        redirect_uri=_optional_value(form, "redirect_uri"),
        username=_optional_value(form, "username"),
        password=_optional_value(form, "password"),
        totp_secret=_optional_value(form, "totp_secret"),
    )


def create_app() -> Flask:
    """Create and configure the Flask app."""

    app = Flask(__name__, template_folder="templates")
    app.secret_key = os.environ.get("STREAMING_WEB_SECRET", "dev-secret")
    token_history: List[Dict[str, Any]] = []

    @app.context_processor
    def inject_shared_context() -> Dict[str, Any]:
        return {
            "providers": sorted(AUTH_REGISTRY.keys()),
            "token_history": token_history,
        }

    @app.route("/", methods=["GET", "POST"])
    def index() -> str:
        generated_tokens: Optional[Dict[str, Any]] = None
        if request.method == "POST":
            provider = (request.form.get("provider") or "").strip().lower()
            if provider not in AUTH_REGISTRY:
                flash("Please choose a valid provider.", "error")
                return redirect(url_for("index"))

            credentials = _build_credentials(request.form)
            if not credentials.api_key or not credentials.api_secret:
                flash("API key and secret are required to generate tokens.", "error")
                return redirect(url_for("index"))

            try:
                auth_service = create_auth_service(provider, credentials)
                token_bundle = auth_service.generate_access_token()
            except Exception as exc:  # pragma: no cover - surfaced to UI
                flash(f"Failed to generate tokens: {exc}", "error")
                return redirect(url_for("index"))

            generated_tokens = asdict(token_bundle)
            generated_tokens["provider"] = provider
            generated_tokens["generated_at"] = datetime.utcnow().isoformat() + "Z"

            token_history.insert(0, generated_tokens)
            del token_history[_TOKEN_HISTORY_LIMIT:]
            flash("Access token generated successfully.", "success")

        return render_template("index.html", generated_tokens=generated_tokens)

    return app


app = create_app()
