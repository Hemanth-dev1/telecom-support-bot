from fastapi import APIRouter, Request
from services.firestore_client import get_subscriber, get_plan, update_subscriber
from services.knowledge_search import search_knowledge_base
from services.gemini_client import generate_friendly_response
from datetime import date, timedelta
import logging, time, json

router = APIRouter()

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
        for key in ["originalValue", "resolvedValue", "original", "stringValue"]:
            v = val.get(key, "")
            if v:
                return str(v).strip()
    return str(val).strip()

@router.post("/webhook")
async def dialogflow_webhook(request: Request):
    start = time.time()
    body = await request.json()
    logging.info(f"FULL_BODY: {json.dumps(body)}")

    tag = body.get("fulfillmentInfo", {}).get("tag", "")
    session_params = body.get("sessionInfo", {}).get("parameters", {})
    logging.info(f"SESSION_PARAMS: {json.dumps(session_params)}")

    phone = normalize_phone(get_string_value(session_params.get("phone", "")))

    plan_name = ""
    for key in ["plan", "telecom-plan"]:
        val = session_params.get(key, "")
        if val:
            plan_name = get_string_value(val)
            if plan_name and not plan_name.startswith("+") and not plan_name.startswith("91"):
                break
            else:
                plan_name = ""

    logging.info(f"EXTRACTED tag={tag} phone={phone} plan={plan_name}")

    try:
        response = await dispatch(tag, session_params, phone, plan_name, body)
        ms = int((time.time() - start) * 1000)
        logging.info(f"webhook_ok tag={tag} ms={ms}")
        return response
    except Exception as e:
        logging.error(f"webhook_error tag={tag} error={str(e)}")
        return _msg("Something went wrong. Please try again.")

async def dispatch(tag: str, params: dict, phone: str, plan_name: str, body: dict) -> dict:
    if tag == "check-plan":
        if not phone:
            return _msg("Phone not found. Please try again.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg(f"No account found for {phone}.")
        return _msg(f"Your current plan is {sub['plan']}. "
                    f"It renews on {sub['renewal_date']}. "
                    f"Status: {sub['status']}.")

    elif tag == "check-data":
        if not phone:
            return _msg("Phone not found. Please try again.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")
        used = sub.get("data_used_gb", 0)
        total = sub.get("total_data_gb", 0)
        remaining = max(0, total - used)
        pct = int((used / total) * 100) if total > 0 else 0
        return _msg(f"Data usage for {sub['name']}:\n"
                    f"Used: {used:.1f} GB of {total} GB ({pct}%)\n"
                    f"Remaining: {remaining:.1f} GB\n"
                    f"Resets on: {sub['renewal_date']}")

    elif tag == "renew-plan":
        if not phone:
            return _msg("Phone not found. Please try again.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")
        new_date = date.today() + timedelta(days=30)
        update_subscriber(phone, {"renewal_date": str(new_date), "status": "active"})
        return _msg(f"Done! Your {sub['plan']} plan is renewed until {new_date}.")

    elif tag == "upgrade-plan":
        if not phone:
            return _msg("Phone not found. Please try again.")
        if not plan_name:
            return _msg("Plan name not received. Try: Basic Plan, Unlimited Pro, Family Pack.")
        plan = get_plan(plan_name)
        if not plan:
            return _msg(f"Plan '{plan_name}' not found. Try: Basic Plan, Unlimited Pro, Family Pack.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")
        update_subscriber(phone, {"plan": plan["name"], "total_data_gb": plan["data_gb"]})
        return _msg(f"Upgraded to {plan['name']}! "
                    f"You now have {plan['data_gb']}GB at Rs.{plan['price_inr']}/month.")

    elif tag == "knowledge-query":
        # Try session params first
        user_query = ""
        for key in ["user_query", "user-query", "query"]:
            val = get_string_value(params.get(key, ""))
            if val and not val.startswith("$"):
                user_query = val
                break
        # Fallback to raw text from Dialogflow body
        if not user_query:
            user_query = body.get("text", "")
        logging.info(f"knowledge_query: {user_query}")
        if not user_query:
            return _msg(f"Query not found. Keys: {list(params.keys())}")
        kb_answer = search_knowledge_base(user_query)
        friendly = generate_friendly_response(kb_answer, user_query)
        return _msg(friendly)

    return _msg(f"Unknown tag: {tag}")

def _msg(text: str) -> dict:
    return {"fulfillment_response": {"messages": [{"text": {"text": [text]}}]}}
