"""
Dialogflow CX webhook request verification.

Dialogflow CX signs webhook requests with a Google-issued OIDC token
in the Authorization header:
    Authorization: Bearer <google-signed-id-token>

We verify:
1. The token is a valid Google-signed JWT
2. The token's `iss` claim is accounts.google.com
3. The token's `email` claim matches your Dialogflow service account
4. The token has not expired

Set DIALOGFLOW_SERVICE_ACCOUNT in .env to the service account email
that your Dialogflow CX agent uses to call the webhook, e.g.:
    dialogflow-cx@your-project.iam.gserviceaccount.com

If the env var is not set, verification is SKIPPED with a warning —
safe for local dev, must be set in production.

Reference:
https://cloud.google.com/dialogflow/cx/docs/concept/webhook#auth
"""
import logging
from fastapi import Request, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from config import DIALOGFLOW_SERVICE_ACCOUNT, WEBHOOK_AUDIENCE

_log = logging.getLogger("app")


async def verify_dialogflow_token(request: Request) -> None:
    """
    FastAPI dependency — verifies the Dialogflow OIDC token.
    Raises 401 if the token is missing, invalid, or from the wrong SA.
    """
    if not DIALOGFLOW_SERVICE_ACCOUNT:
        _log.warning(
            "webhook_auth_disabled",
            extra={"reason": "DIALOGFLOW_SERVICE_ACCOUNT not set"},
        )
        return   # Skip in local dev

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        _log.warning("webhook_auth_missing_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header on webhook request.",
        )

    token = auth_header.removeprefix("Bearer ").strip()

    try:
        # Verify signature + expiry against Google's public certs
        audience = WEBHOOK_AUDIENCE or None
        id_info  = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=audience,
        )

        # Check issuer
        if id_info.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            raise ValueError(f"Unexpected issuer: {id_info.get('iss')}")

        # Check the email matches our expected Dialogflow SA
        token_email = id_info.get("email", "")
        if token_email != DIALOGFLOW_SERVICE_ACCOUNT:
            raise ValueError(
                f"Token email '{token_email}' does not match "
                f"expected SA '{DIALOGFLOW_SERVICE_ACCOUNT}'"
            )

        _log.info(
            "webhook_auth_ok",
            extra={"email": token_email},
        )

    except Exception as e:
        _log.error("webhook_auth_failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook token verification failed.",
        )
