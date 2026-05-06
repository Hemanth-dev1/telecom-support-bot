"""
/chat route — API key + rate limiting + server-side session ID validation.
"""
import uuid, time, re, logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.cloud import dialogflowcx_v3 as dialogflow
from google.api_core.exceptions import GoogleAPICallError, DeadlineExceeded

from config       import PROJECT_ID, LOCATION, AGENT_ID, DIALOGFLOW_TIMEOUT_SECONDS
from auth         import require_api_key
from rate_limiter import rate_limit_chat
from logger       import log_request, log_response, log_error

router = APIRouter()
_log   = logging.getLogger("app")

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

def _validate_session_id(raw) -> str:
    """Accept only valid UUID v4 from client; generate fresh one otherwise."""
    if raw and _UUID_RE.match(str(raw).strip()):
        return str(raw).strip()
    new_id = str(uuid.uuid4())
    if raw:
        _log.warning("session_id_rejected", extra={"supplied": str(raw)[:64], "assigned": new_id})
    return new_id

def detect_intent_text(message: str, session_id: str) -> dict:
    client       = dialogflow.SessionsClient()
    session_path = client.session_path(PROJECT_ID, LOCATION, AGENT_ID, session_id)
    query_input  = dialogflow.QueryInput(
        text=dialogflow.TextInput(text=message), language_code="en"
    )
    try:
        response = client.detect_intent(
            request={"session": session_path, "query_input": query_input},
            timeout=DIALOGFLOW_TIMEOUT_SECONDS,
        )
    except DeadlineExceeded:
        _log.error("dialogflow_timeout", extra={"session_id": session_id})
        raise

    replies = []
    for msg in response.query_result.response_messages:
        if hasattr(msg, "text") and msg.text and hasattr(msg.text, "text") and msg.text.text:
            replies.extend(msg.text.text)

    is_end = False
    if hasattr(response.query_result, "current_page") and response.query_result.current_page:
        page_name = response.query_result.current_page.name.split("/")[-1].lower()
        if any(x in page_name for x in ["end", "goodbye", "end_session", "exit"]):
            is_end = True

    intent_name, confidence = "", 0.0
    if hasattr(response.query_result, "intent") and response.query_result.intent:
        intent_name = response.query_result.intent.display_name
    if hasattr(response.query_result, "intent_detection_confidence"):
        confidence = round(float(response.query_result.intent_detection_confidence), 3)

    return {"reply_texts": replies, "is_end_session": is_end,
            "intent": intent_name, "confidence": confidence}


@router.post("/chat")
async def chat(
    request: Request,
    payload: dict,
    _auth: None = Depends(require_api_key),
    _rate: None = Depends(rate_limit_chat),
):
    message = (payload.get("message") or "").strip()
    if not message:
        return {"reply": ["Message cannot be empty."], "session_id": str(uuid.uuid4()),
                "end_session": False, "subscriber_data": None, "intent": "", "confidence": 0.0}

    session_id = _validate_session_id(payload.get("session_id"))
    log_request("chat", session_id, message_len=len(message))
    t0 = time.time()

    try:
        result = detect_intent_text(message, session_id)
    except DeadlineExceeded:
        log_error("chat", session_id, "dialogflow_timeout")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                            detail="Dialogflow did not respond in time.")
    except GoogleAPICallError as e:
        log_error("chat", session_id, str(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Upstream Dialogflow error.")

    ms = int((time.time() - t0) * 1000)
    log_response("chat", session_id, ms, intent=result["intent"],
                 confidence=result["confidence"], end_session=result["is_end_session"])

    return {
        "reply":           result["reply_texts"],
        "session_id":      session_id,
        "end_session":     result["is_end_session"],
        "intent":          result["intent"],
        "confidence":      result["confidence"],
        "subscriber_data": None,
    }
