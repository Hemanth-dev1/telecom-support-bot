"""
Dialogflow CX webhook handler.

Changes from original:
- Structured JSON logging via logger module
- Uses transactional Firestore ops (renew_subscriber, upgrade_subscriber)
- Returns structured subscriber_data in fulfillment session params
  so the frontend AccountPanel gets data without regex parsing
- Timeout-aware (Dialogflow expects response within 10 s)
"""
import time
import logging
from fastapi import APIRouter, Depends, Request
from datetime import date, timedelta

from services.firestore_client import (
    get_subscriber,
    get_plan,
    update_subscriber,
    renew_subscriber,
    upgrade_subscriber,
)
from services.knowledge_search import search_knowledge_base
from services.gemini_client    import generate_friendly_response
from logger       import log_request, log_response, log_error
from webhook_auth import verify_dialogflow_token

router = APIRouter()
_log   = logging.getLogger("app")


# ── Param extraction helpers ──────────────────────────────────────

def normalize_phone(phone) -> str:
    if not phone:
        return ""
    phone = str(phone).strip().replace('"', '').replace("'", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def get_string_value(val) -> str:
    if not val:
        return ""
    if isinstance(val, str):
        return val.strip().replace('"', '').replace("'", "")
    if isinstance(val, dict):
        for key in ["phoneNumber", "e164", "raw", "originalValue",
                    "resolvedValue", "original", "stringValue"]:
            v = val.get(key, "")
            if v:
                return str(v).strip()
    return str(val).strip()


# ── Response builders ─────────────────────────────────────────────

def _msg(text: str, subscriber_data: dict | None = None) -> dict:
    """
    Build a Dialogflow CX fulfillment response.
    Optionally injects structured subscriber_data into session params
    so the frontend can read it directly from the /chat response
    without parsing the human-readable text.
    """
    response: dict = {
        "fulfillmentResponse": {
            "messages": [{"text": {"text": [text]}}]
        }
    }

    # Inject subscriber snapshot into session params so future turns
    # and the frontend both have access to structured account data
    if subscriber_data:
        response["sessionInfo"] = {
            "parameters": {
                "subscriber_data": subscriber_data,
            }
        }

    return response


# ── Webhook entry point ───────────────────────────────────────────

@router.post("/webhook")
async def dialogflow_webhook(
    request: Request,
    _auth: None = Depends(verify_dialogflow_token),   # ← OIDC verification
):
    t0   = time.time()
    body = await request.json()

    tag            = body.get("fulfillmentInfo", {}).get("tag", "")
    session_params = body.get("sessionInfo", {}).get("parameters", {})
    session_id     = body.get("sessionInfo", {}).get("session", "unknown").split("/")[-1]

    log_request("webhook", session_id, tag=tag)

    phone = normalize_phone(get_string_value(session_params.get("phone", "")))

    plan_name = ""
    for key in ["plan", "telecom-plan"]:
        val = session_params.get(key, "")
        if val:
            candidate = get_string_value(val)
            if candidate and not candidate.startswith("+") and not candidate.startswith("91"):
                plan_name = candidate
                break

    raw_text = body.get("text", "") or body.get("transcript", "") or ""

    _log.info(
        "webhook:extracted",
        extra={"tag": tag, "phone": phone, "plan": plan_name, "session_id": session_id},
    )

    try:
        response = await _dispatch(tag, session_params, phone, plan_name, body, raw_text)
        ms = int((time.time() - t0) * 1000)
        log_response("webhook", session_id, ms, tag=tag)
        return response
    except Exception as e:
        log_error("webhook", session_id, str(e), tag=tag)
        return _msg("Something went wrong. Please try again.")


# ── Intent dispatcher ─────────────────────────────────────────────

async def _dispatch(
    tag: str, params: dict, phone: str, plan_name: str, body: dict, raw_text: str
) -> dict:

    # ── check-plan ────────────────────────────────────────────────
    if tag == "check-plan":
        if not phone:
            return _msg("I couldn't find your phone number. Please try again.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg(f"No account found for {phone}.")

        subscriber_data = {
            "phone":        phone,
            "name":         sub.get("name", ""),
            "plan":         sub.get("plan", ""),
            "renewal_date": sub.get("renewal_date", ""),
            "status":       sub.get("status", ""),
            "data_used_gb": sub.get("data_used_gb", 0),
            "total_data_gb": sub.get("total_data_gb", 0),
        }
        return _msg(
            f"Your current plan is {sub['plan']}. "
            f"It renews on {sub['renewal_date']}. "
            f"Status: {sub['status']}.",
            subscriber_data=subscriber_data,
        )

    # ── check-data ────────────────────────────────────────────────
    elif tag == "check-data":
        if not phone:
            return _msg("I couldn't find your phone number. Please try again.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")

        used      = sub.get("data_used_gb", 0)
        total     = sub.get("total_data_gb", 0)
        remaining = max(0, total - used)
        pct       = int((used / total) * 100) if total > 0 else 0

        subscriber_data = {
            "phone":         phone,
            "name":          sub.get("name", ""),
            "plan":          sub.get("plan", ""),
            "renewal_date":  sub.get("renewal_date", ""),
            "status":        sub.get("status", ""),
            "data_used_gb":  used,
            "total_data_gb": total,
        }
        return _msg(
            f"Data usage for {sub['name']}:\n"
            f"Used: {used:.1f} GB of {total} GB ({pct}%)\n"
            f"Remaining: {remaining:.1f} GB\n"
            f"Resets on: {sub['renewal_date']}",
            subscriber_data=subscriber_data,
        )

    # ── renew-plan (confirmation prompt only) ─────────────────────
    elif tag == "renew-plan":
        if not phone:
            return _msg("I couldn't find your phone number. Please try again.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")
        return _msg(
            f"I will renew your {sub['plan']} plan for one month. Confirm? (yes / no)"
        )

    # ── confirm-renew (actual renewal — transactional) ────────────
    elif tag == "confirm-renew":
        if not phone:
            return _msg("I couldn't find your phone number. Please try again.")

        new_date = str(date.today() + timedelta(days=30))
        updated  = renew_subscriber(phone, new_date)   # ← transaction

        if not updated:
            return _msg("I couldn't process the renewal. Please try again.")

        subscriber_data = {
            "phone":         phone,
            "name":          updated.get("name", ""),
            "plan":          updated.get("plan", ""),
            "renewal_date":  new_date,
            "status":        "active",
            "data_used_gb":  updated.get("data_used_gb", 0),
            "total_data_gb": updated.get("total_data_gb", 0),
        }
        return _msg(
            f"Done! Your {updated['plan']} plan is renewed until {new_date}.",
            subscriber_data=subscriber_data,
        )

    # ── upgrade-plan (transactional) ──────────────────────────────
    elif tag == "upgrade-plan":
        if not phone:
            return _msg("I couldn't find your phone number. Please try again.")
        if not plan_name:
            return _msg("Which plan would you like? Basic Plan, Unlimited Pro, or Family Pack.")

        updated_sub, plan = upgrade_subscriber(phone, plan_name)   # ← transaction

        if updated_sub is None:
            return _msg(
                f"I couldn't find the plan '{plan_name}'. "
                f"Available plans: Basic Plan, Unlimited Pro, Family Pack."
            )

        subscriber_data = {
            "phone":         phone,
            "name":          updated_sub.get("name", ""),
            "plan":          plan["name"],
            "renewal_date":  updated_sub.get("renewal_date", ""),
            "status":        updated_sub.get("status", ""),
            "data_used_gb":  updated_sub.get("data_used_gb", 0),
            "total_data_gb": plan["data_gb"],
        }
        return _msg(
            f"Upgraded to {plan['name']}! "
            f"You now have {plan['data_gb']}GB at Rs.{plan['price_inr']}/month.",
            subscriber_data=subscriber_data,
        )

    # ── knowledge-query ───────────────────────────────────────────
    elif tag == "knowledge-query":
        user_query = ""
        for key in ["user_query", "user-query", "query"]:
            val = get_string_value(params.get(key, ""))
            if val and not val.startswith("$"):
                user_query = val
                break
        if not user_query:
            user_query = raw_text

        if not user_query:
            return _msg("I couldn't understand your query. Please rephrase.")

        kb_answer = search_knowledge_base(user_query)
        friendly  = generate_friendly_response(kb_answer, user_query)
        return _msg(friendly)

    # ── fallback ──────────────────────────────────────────────────
    return _msg("I'm not sure how to help with that. Please try again.")