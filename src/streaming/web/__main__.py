"""Run the Flask development server."""
from __future__ import annotations

import os

from .app import app


if __name__ == "__main__":  # pragma: no cover - script entry point
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=False)
