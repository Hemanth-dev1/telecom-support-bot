"""
API key authentication.

Every request to protected routes must include:
    X-API-Key: <value of API_SECRET_KEY env var>

The webhook route (/webhook) is intentionally excluded —
it is protected separately by Dialogflow's own request origin
and should be placed behind a VPC or verified via Dialogflow
service account in production.

Usage in routes:
    from auth import require_api_key
    @router.post("/chat")
    async def chat(payload: dict, _: None = Depends(require_api_key)):
        ...
"""
import secrets
import logging
from fastapi import Header, HTTPException, status
from config import API_SECRET_KEY


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """
    FastAPI dependency — raises 401 if the header is missing or wrong.
    Uses `secrets.compare_digest` to prevent timing attacks.
    """
    if not API_SECRET_KEY:
        # If no key is configured (e.g. local dev without .env), skip auth.
        # Log a warning so it's visible in Cloud Logging.
        logging.getLogger("app").warning(
            "API_SECRET_KEY is not set — authentication is DISABLED. "
            "Set this variable before deploying to production."
        )
        return

    if not x_api_key or not secrets.compare_digest(x_api_key, API_SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
