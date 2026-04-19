from google.cloud import firestore

db = firestore.Client()

def get_subscriber(phone: str):
    doc = db.collection("subscribers").document(phone).get()
    return doc.to_dict() if doc.exists else None

def update_subscriber(phone: str, data: dict) -> bool:
    try:
        db.collection("subscribers").document(phone).update(data)
        return True
    except Exception:
        return False

def get_plan(plan_name: str):
    plan_id = plan_name.lower().replace(" ", "-")
    doc = db.collection("plans").document(plan_id).get()
    return doc.to_dict() if doc.exists else None

def get_all_plans() -> list:
    docs = db.collection("plans").stream()
    return [doc.to_dict() for doc in docs]
