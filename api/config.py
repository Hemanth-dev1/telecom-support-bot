"""
Centralised configuration with startup validation.
Raises a clear RuntimeError immediately if required env vars are missing.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"[CONFIG] Required environment variable '{name}' is missing or empty. "
            f"Set it in .env (local) or Cloud Run env vars (production)."
        )
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# ── Required ──────────────────────────────────────────────────────
PROJECT_ID    = _require("PROJECT_ID")
AGENT_ID      = _require("AGENT_ID")
DATA_STORE_ID = _require("DATA_STORE_ID")

# ── Auth ──────────────────────────────────────────────────────────
API_SECRET_KEY             = _optional("API_SECRET_KEY", "")
DIALOGFLOW_SERVICE_ACCOUNT = _optional("DIALOGFLOW_SERVICE_ACCOUNT", "")
WEBHOOK_AUDIENCE           = _optional("WEBHOOK_AUDIENCE", "")

# ── Dialogflow ────────────────────────────────────────────────────
LOCATION                   = _optional("LOCATION", "asia-south1")
DIALOGFLOW_TIMEOUT_SECONDS = int(_optional("DIALOGFLOW_TIMEOUT", "15"))

# ── Rate limiting ─────────────────────────────────────────────────
RATE_LIMIT_REQUESTS = int(_optional("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW   = int(_optional("RATE_LIMIT_WINDOW",   "60"))

# ── CORS ──────────────────────────────────────────────────────────
_raw_origins = _optional(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174",
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
