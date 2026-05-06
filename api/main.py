"""
Application entry point.
Security layers applied here in order:
  1. CORS         — origin whitelist
  2. API Key      — X-API-Key header (per route via Depends)
  3. Rate Limit   — 30 req/min per IP on /chat (per route via Depends)
  4. Webhook Auth — Dialogflow OIDC token on /webhook (per route via Depends)
  5. Session ID   — always generated server-side in chat.py
"""
from dotenv import load_dotenv
load_dotenv()

# ── 1. Load & validate config first ──────────────────────────────
from config import ALLOWED_ORIGINS          # raises RuntimeError if env vars missing

# ── 2. Set up structured logging ─────────────────────────────────
from logger import setup_logging
setup_logging()

# ── 3. Normal imports ─────────────────────────────────────────────
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.subscriber import router as subscriber_router
from routes.renewal    import router as renewal_router
from routes.webhook    import router as webhook_router
from routes.chat       import router as chat_router

log = logging.getLogger("app")

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(title="Telecom Support API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # driven by ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subscriber_router, prefix="/api", tags=["Subscribers"])
app.include_router(renewal_router,    prefix="/api", tags=["Renewals"])
app.include_router(webhook_router,    tags=["Webhook"])
app.include_router(chat_router,       tags=["Chat"])


@app.on_event("startup")
async def on_startup() -> None:
    log.info("startup", extra={"allowed_origins": ALLOWED_ORIGINS})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test-search")
async def test_search(q: str):
    from services.knowledge_search import search_knowledge_base
    answer = search_knowledge_base(q)
    return {"query": q, "answer": answer}
