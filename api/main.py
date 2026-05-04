from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes.subscriber import router as subscriber_router
from routes.renewal import router as renewal_router
from routes.webhook import router as webhook_router
from routes.chat import router as chat_router
import logging

app = FastAPI(title="Telecom Support API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subscriber_router, prefix="/api", tags=["Subscribers"])
app.include_router(renewal_router, prefix="/api", tags=["Renewals"])
app.include_router(webhook_router, tags=["Webhook"])
app.include_router(chat_router, tags=["Chat"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test-search")
async def test_search(q: str):
    from services.knowledge_search import search_knowledge_base
    answer = search_knowledge_base(q)
    return {"query": q, "answer": answer}
