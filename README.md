# TelecomSupportBot
 
> AI-powered customer support agent for telecom subscription management
 
**Live Demo**: https://telecom-api-925349905681.asia-south1.run.app/health  
**Stack**: Dialogflow CX │ FastAPI │ Cloud Run │ Firestore │ Vertex AI Search │ Gemini 1.5 Flash
 
---
 
## What it does
- Checks current plan and data usage by mobile number
- Renews or upgrades subscription plans
- Answers policy questions from knowledge base (RAG)
- Handles FAQs: roaming, billing, SIM swap, porting
 
## Architecture
 
User -> Dialogflow CX (NLU) -> Webhook -> FastAPI on Cloud Run
                                        -> Firestore (subscriber data)
                                        -> Vertex AI Search (policy docs)
                                        -> Vertex AI Gemini Flash (synthesis)
 
## Sample Conversation
 
User: What plan am I on?
Bot:  Please share your registered mobile number.
User: +91-9000000001
Bot:  You are on Unlimited Pro. It renews on 2026-05-15. Status: active.
 
User: What is your refund policy?
Bot:  Refund requests must be raised within 7 days of payment...
      [Gemini-synthesised answer from refund_policy.txt]
 
## Setup in 5 minutes
 
1. Clone repo and enable GCP APIs
2. Set up GCP project and enable APIs (see docs/setup.md)
3. Seed data: python scripts/seed_firestore.py
4. Deploy: gcloud run deploy telecom-api --source api/ --region asia-south1
5. Import Dialogflow agent: dialogflow-export/TelecomSupportBot.zip
 
## Built with
| Service | Purpose |
|---|---|
| Dialogflow CX | NLU, conversation flows |
| Cloud Run | Serverless API hosting |
| Firestore | Subscriber data store |
| Vertex AI Search | Knowledge base RAG |
| Gemini 1.5 Flash | Response synthesis |
