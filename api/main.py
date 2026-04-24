from fastapi import FastAPI, Request
from routes.subscriber import router as subscriber_router
from routes.renewal import router as renewal_router
from routes.webhook import router as webhook_router
import logging

app = FastAPI(title="Telecom Support API", version="1.0.0")

app.include_router(subscriber_router, prefix="/api", tags=["Subscribers"])
app.include_router(renewal_router, prefix="/api", tags=["Renewals"])
app.include_router(webhook_router, tags=["Webhook"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test-search")
async def test_search(q: str):
    from services.knowledge_search import search_knowledge_base
    answer = search_knowledge_base(q)
    return {"query": q, "answer": answer}
