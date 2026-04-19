from fastapi import APIRouter, Request
from services.firestore_client import get_subscriber, get_plan, update_subscriber
from datetime import date, timedelta
import logging, time

router = APIRouter()

@router.post("/webhook")
async def dialogflow_webhook(request: Request):
    start = time.time()
    body = await request.json()

    tag = body.get("fulfillmentInfo", {}).get("tag", "")
    params = body.get("sessionInfo", {}).get("parameters", {})
    phone = params.get("phone", "")
    phone_masked = f"****{str(phone)[-4:]}" if phone else "unknown"

    try:
        response = await dispatch(tag, params)
        ms = int((time.time() - start) * 1000)
        logging.info(f"webhook_ok tag={tag} phone={phone_masked} ms={ms}")
        return response
    except Exception as e:
        logging.error(f"webhook_error tag={tag} phone={phone_masked} error={str(e)}")
        return _msg("Something went wrong. Please try again in a moment.")

async def dispatch(tag: str, params: dict) -> dict:
    phone = params.get("phone", "")

    if tag == "check-plan":
        sub = get_subscriber(phone)
        if not sub:
            return _msg("I couldn't find an account for that number.")
        return _msg(f"Your current plan is {sub['plan']}. "
                    f"It renews on {sub['renewal_date']}. "
                    f"Your account status is {sub['status']}.")

    elif tag == "check-data":
        sub = get_subscriber(phone)
        if not sub:
            return _msg("I couldn't find an account for that number.")
        used = sub.get("data_used_gb", 0)
        total = sub.get("total_data_gb", 0)
        remaining = max(0, total - used)
        pct = int((used / total) * 100) if total > 0 else 0
        return _msg(f"Data usage for {sub['name']}:\n"
                    f"Used: {used:.1f} GB of {total} GB ({pct}%)\n"
                    f"Remaining: {remaining:.1f} GB\n"
                    f"Resets on: {sub['renewal_date']}")

    elif tag == "renew-plan":
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")
        new_date = date.today() + timedelta(days=30)
        update_subscriber(phone, {"renewal_date": str(new_date), "status": "active"})
        return _msg(f"Done! Your {sub['plan']} plan is renewed until {new_date}.")

    elif tag == "upgrade-plan":
        new_plan_name = params.get("plan", "")
        plan = get_plan(new_plan_name)
        if not plan:
            return _msg(f"Sorry, I couldn't find a plan called {new_plan_name}.")
        sub = get_subscriber(phone)
        if not sub:
            return _msg("Account not found.")
        update_subscriber(phone, {"plan": plan["name"], "total_data_gb": plan["data_gb"]})
        return _msg(f"Upgraded to {plan['name']}! "
                    f"You now have {plan['data_gb']}GB at Rs.{plan['price_inr']}/month.")

    elif tag == "knowledge-query":
        return _msg("Let me check our knowledge base for that.")

    return _msg("I'm not sure how to handle that request.")

def _msg(text: str) -> dict:
    return {"fulfillment_response": {"messages": [{"text": {"text": [text]}}]}}
