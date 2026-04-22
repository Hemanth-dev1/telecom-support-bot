from google.cloud import firestore

db = firestore.Client()

def get_subscriber(phone: str):
    if not phone:
        return None
    doc = db.collection("subscribers").document(phone).get()
    return doc.to_dict() if doc.exists else None

def update_subscriber(phone: str, data: dict) -> bool:
    try:
        db.collection("subscribers").document(phone).update(data)
        return True
    except Exception:
        return False

def get_plan(plan_name: str):
    if not plan_name:
        return None
    plan_id = str(plan_name).lower().replace(" ", "-").strip()
    if not plan_id:
        return None
    doc = db.collection("plans").document(plan_id).get()
    return doc.to_dict() if doc.exists else None

def get_all_plans() -> list:
    docs = db.collection("plans").stream()
    return [doc.to_dict() for doc in docs]
