from fastapi import APIRouter, HTTPException
from services.firestore_client import get_subscriber, get_all_plans

router = APIRouter()

@router.get("/subscriber/{phone}")
async def get_subscriber_info(phone: str):
    subscriber = get_subscriber(phone)
    if not subscriber:
        raise HTTPException(status_code=404, detail=f"No account found for {phone}")
    return {
        "phone": phone,
        "name": subscriber["name"],
        "plan": subscriber["plan"],
        "data_used_gb": subscriber["data_used_gb"],
        "total_data_gb": subscriber.get("total_data_gb", 0),
        "renewal_date": subscriber["renewal_date"],
        "status": subscriber["status"]
    }

@router.get("/plans")
async def list_plans():
    plans = get_all_plans()
    return {"plans": plans, "count": len(plans)}
