"""
Firestore data access layer.

Key improvements:
- Firestore transactions for plan upgrades and renewals (prevents race conditions)
- Structured logging via logger module
- Explicit error types surfaced to callers
"""
from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from logger import log
import logging

db = firestore.Client()
_log = logging.getLogger("app")


# ── Read helpers ──────────────────────────────────────────────────

def get_subscriber(phone: str) -> dict | None:
    """Fetch a subscriber document by phone (document ID)."""
    if not phone:
        return None
    try:
        doc: DocumentSnapshot = db.collection("subscribers").document(phone).get()
        if doc.exists:
            log("info", "firestore:get_subscriber", phone=phone, found=True)
            return doc.to_dict()
        log("info", "firestore:get_subscriber", phone=phone, found=False)
        return None
    except Exception as e:
        log("error", "firestore:get_subscriber:error", phone=phone, error=str(e))
        return None


def get_plan(plan_name: str) -> dict | None:
    """Fetch a plan document by name (converts to kebab-case ID)."""
    if not plan_name:
        return None
    plan_id = plan_name.lower().replace(" ", "-").strip()
    try:
        doc: DocumentSnapshot = db.collection("plans").document(plan_id).get()
        if doc.exists:
            log("info", "firestore:get_plan", plan_id=plan_id, found=True)
            return doc.to_dict()
        log("info", "firestore:get_plan", plan_id=plan_id, found=False)
        return None
    except Exception as e:
        log("error", "firestore:get_plan:error", plan_id=plan_id, error=str(e))
        return None


def get_all_plans() -> list[dict]:
    """Return all plan documents."""
    try:
        docs = db.collection("plans").stream()
        plans = [doc.to_dict() for doc in docs]
        log("info", "firestore:get_all_plans", count=len(plans))
        return plans
    except Exception as e:
        log("error", "firestore:get_all_plans:error", error=str(e))
        return []


# ── Write helpers ─────────────────────────────────────────────────

def update_subscriber(phone: str, data: dict) -> bool:
    """
    Simple field update — use for non-critical fields only.
    For plan upgrades and renewals use the transactional versions below.
    """
    if not phone:
        return False
    try:
        db.collection("subscribers").document(phone).update(data)
        log("info", "firestore:update_subscriber", phone=phone, fields=list(data.keys()))
        return True
    except Exception as e:
        log("error", "firestore:update_subscriber:error", phone=phone, error=str(e))
        return False


# ── Transactional operations ──────────────────────────────────────

@firestore.transactional
def _renew_in_transaction(
    transaction: firestore.Transaction,
    sub_ref: firestore.DocumentReference,
    new_renewal_date: str,
) -> dict:
    """
    Atomically read the subscriber then write the new renewal date.
    Returns the subscriber dict (with updated date) or raises if not found.
    Raises ValueError if subscriber not found.
    """
    snapshot: DocumentSnapshot = sub_ref.get(transaction=transaction)
    if not snapshot.exists:
        raise ValueError("Subscriber not found")

    sub = snapshot.to_dict()
    transaction.update(sub_ref, {
        "renewal_date": new_renewal_date,
        "status": "active",
    })
    # Return the updated data so the caller can build the reply
    return {**sub, "renewal_date": new_renewal_date, "status": "active"}


def renew_subscriber(phone: str, new_renewal_date: str) -> dict | None:
    """
    Transactional renewal.
    Returns updated subscriber dict on success, None on failure.
    """
    if not phone:
        return None
    sub_ref = db.collection("subscribers").document(phone)
    try:
        transaction = db.transaction()
        updated = _renew_in_transaction(transaction, sub_ref, new_renewal_date)
        log("info", "firestore:renew_subscriber", phone=phone, new_date=new_renewal_date)
        return updated
    except ValueError as e:
        log("info", "firestore:renew_subscriber:not_found", phone=phone, error=str(e))
        return None
    except Exception as e:
        log("error", "firestore:renew_subscriber:error", phone=phone, error=str(e))
        return None


@firestore.transactional
def _upgrade_in_transaction(
    transaction: firestore.Transaction,
    sub_ref: firestore.DocumentReference,
    plan_ref: firestore.DocumentReference,
) -> tuple[dict, dict]:
    """
    Atomically read subscriber + plan then write the upgrade.
    Returns (updated_subscriber, plan) tuple.
    Raises ValueError if either document not found.
    """
    sub_snap: DocumentSnapshot  = sub_ref.get(transaction=transaction)
    plan_snap: DocumentSnapshot = plan_ref.get(transaction=transaction)

    if not sub_snap.exists:
        raise ValueError("Subscriber not found")
    if not plan_snap.exists:
        raise ValueError("Plan not found")

    sub  = sub_snap.to_dict()
    plan = plan_snap.to_dict()

    transaction.update(sub_ref, {
        "plan":          plan["name"],
        "total_data_gb": plan["data_gb"],
    })
    return {**sub, "plan": plan["name"], "total_data_gb": plan["data_gb"]}, plan


def upgrade_subscriber(phone: str, plan_name: str) -> tuple[dict, dict] | tuple[None, None]:
    """
    Transactional upgrade.
    Returns (updated_subscriber, plan) on success, (None, None) on failure.
    """
    if not phone or not plan_name:
        return None, None

    plan_id  = plan_name.lower().replace(" ", "-").strip()
    sub_ref  = db.collection("subscribers").document(phone)
    plan_ref = db.collection("plans").document(plan_id)

    try:
        transaction = db.transaction()
        updated_sub, plan = _upgrade_in_transaction(transaction, sub_ref, plan_ref)
        log("info", "firestore:upgrade_subscriber", phone=phone, plan=plan_name)
        return updated_sub, plan
    except ValueError as e:
        log("info", "firestore:upgrade_subscriber:not_found", phone=phone, error=str(e))
        return None, None
    except Exception as e:
        log("error", "firestore:upgrade_subscriber:error", phone=phone, error=str(e))
        return None, None
