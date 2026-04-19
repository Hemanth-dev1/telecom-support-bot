from fastapi import FastAPI
from routes.subscriber import router as subscriber_router
from routes.renewal import router as renewal_router
import logging

app = FastAPI(title="Telecom Support API", version="1.0.0")

app.include_router(subscriber_router, prefix="/api", tags=["Subscribers"])
app.include_router(renewal_router, prefix="/api", tags=["Renewals"])

@app.get("/health")
def health():
    return {"status": "ok"}
