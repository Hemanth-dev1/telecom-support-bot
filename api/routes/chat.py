from fastapi import APIRouter
from google.cloud import dialogflowcx_v3 as dialogflow

import uuid
import os
import logging

router = APIRouter()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "asia")
AGENT_ID = os.getenv("AGENT_ID")


def detect_intent_text(
    message: str,
    session_id: str
):

    client = dialogflow.SessionsClient()

    session_path = client.session_path(
        PROJECT_ID,
        LOCATION,
        AGENT_ID,
        session_id
    )

    text_input = dialogflow.TextInput(
        text=message
    )

    query_input = dialogflow.QueryInput(
        text=text_input,
        language_code="en"
    )

    response = client.detect_intent(
        request={
            "session": session_path,
            "query_input": query_input,
        }
    )

    replies = []

    for msg in response.query_result.response_messages:
        # ✅ Defensive check: msg.text exists AND has content
        if hasattr(msg, "text") and msg.text and hasattr(msg.text, "text") and msg.text.text:
            replies.extend(msg.text.text)

    # ✅ Check if Dialogflow reached End Session page
    is_end_session = False
    if hasattr(response.query_result, "current_page") and response.query_result.current_page:
        # ✅ current_page is a Page object, access .name attribute to get the resource path string
        page_name = response.query_result.current_page.name.split("/")[-1].lower()
        # Common end session page indicators
        if any(x in page_name for x in ["end", "goodbye", "end_session", "exit"]):
            is_end_session = True
            logging.info(f"END_SESSION detected: page={page_name}")

    return {
        "reply_texts": replies,
        "is_end_session": is_end_session
    }


@router.post("/chat")
async def chat(payload: dict):

    message = payload.get("message")

    if not message:
        return {
            "reply": ["Message cannot be empty."],
            "session_id": None,
            "end_session": False
        }

    # ✅ CRITICAL: Use session_id from frontend to maintain conversation context
    session_id = payload.get("session_id")

    if not session_id:
        # Generate new session only on first turn
        session_id = str(uuid.uuid4())
        logging.info(f"NEW_SESSION: {session_id}")
    else:
        logging.info(f"EXISTING_SESSION: {session_id}")

    logging.info(f"CHAT_REQUEST session_id={session_id} message={message[:100]}")

    result = detect_intent_text(
        message,
        session_id
    )

    is_end = result.get("is_end_session", False)

    logging.info(f"CHAT_RESPONSE session_id={session_id} replies={result['reply_texts']} end_session={is_end}")

    return {
        "reply": result["reply_texts"],
        "session_id": session_id,
        "end_session": is_end
    }
