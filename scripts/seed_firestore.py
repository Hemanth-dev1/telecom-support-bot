from google.cloud import firestore

db = firestore.Client()

subscribers = [
    {"phone": "+919000000001", "name": "Priya Sharma",
     "plan": "Unlimited Pro", "data_used_gb": 18.4,
     "total_data_gb": 100, "renewal_date": "2026-05-15", "status": "active"},
    {"phone": "+919000000002", "name": "Rahul Verma",
     "plan": "Basic Plan", "data_used_gb": 4.1,
     "total_data_gb": 20, "renewal_date": "2026-04-01", "status": "active"},
    {"phone": "+919000000003", "name": "Anjali Nair",
     "plan": "Family Pack", "data_used_gb": 67.2,
     "total_data_gb": 150, "renewal_date": "2026-03-31", "status": "expiring"},
]

plans = [
    {"id": "basic-plan", "name": "Basic Plan", "price_inr": 199,
     "data_gb": 20, "speed_mbps": 10, "validity_days": 30,
     "features": ["20GB data", "10Mbps speed", "100 SMS/day"]},
    {"id": "unlimited-pro", "name": "Unlimited Pro", "price_inr": 599,
     "data_gb": 100, "speed_mbps": 100, "validity_days": 30,
     "features": ["100GB data", "100Mbps speed", "Unlimited SMS", "Free roaming - 5 countries"]},
    {"id": "family-pack", "name": "Family Pack", "price_inr": 999,
     "data_gb": 150, "speed_mbps": 100, "validity_days": 30,
     "features": ["150GB shared", "Up to 4 connections", "100Mbps speed", "Parental controls"]},
]

for s in subscribers:
    db.collection("subscribers").document(s["phone"]).set(s)
    print(f"Seeded subscriber: {s['name']}")

for plan in plans:
    plan_id = plan.pop("id")
    db.collection("plans").document(plan_id).set(plan)
    print(f"Seeded plan: {plan['name']}")

print("Done! Firestore seeded successfully.")
