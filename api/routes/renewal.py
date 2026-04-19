from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date, timedelta
from services.firestore_client import get_subscriber, update_subscriber, get_plan

router = APIRouter()

class RenewRequest(BaseModel):
    phone: str
    months: int = 1

class UpgradeRequest(BaseModel):
    phone: str
    new_plan: str

@router.post("/renew")
async def renew_plan(req: RenewRequest):
    subscriber = get_subscriber(req.phone)
    if not subscriber:
        raise HTTPException(404, f"No account found for {req.phone}")
    new_date = date.today() + timedelta(days=30 * req.months)
    update_subscriber(req.phone, {"renewal_date": str(new_date), "status": "active"})
    return {
        "message": "Plan renewed successfully",
        "plan": subscriber["plan"],
        "new_renewal_date": str(new_date),
        "months_added": req.months
    }

@router.post("/upgrade")
async def upgrade_plan(req: UpgradeRequest):
    subscriber = get_subscriber(req.phone)
    if not subscriber:
        raise HTTPException(404, f"No account found for {req.phone}")
    plan = get_plan(req.new_plan)
    if not plan:
        raise HTTPException(404, f"Plan '{req.new_plan}' not found")
    update_subscriber(req.phone, {
        "plan": plan["name"],
        "total_data_gb": plan["data_gb"]
    })
    return {
        "message": f"Upgraded to {plan['name']}",
        "old_plan": subscriber["plan"],
        "new_plan": plan["name"],
        "new_data_gb": plan["data_gb"]
    }
