from fastapi import FastAPI
import logging

app = FastAPI(
    title="Telecom Support API",
    description="Backend for TelecomSupportBot",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "telecom-api", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "Telecom Support API is running"}
