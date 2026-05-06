# TelecomSupportBot - Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Directory Structure](#directory-structure)
5. [API Endpoints](#api-endpoints)
6. [Services](#services)
7. [Data Models](#data-models)
8. [Setup & Deployment](#setup--deployment)
9. [Key Features](#key-features)
10. [Development Guide](#development-guide)

---

## Project Overview

**TelecomSupportBot** is an AI-powered customer support agent designed for telecom subscription management. It provides automated responses to customer queries regarding plans, data usage, renewals, upgrades, and policy information.

### Key Capabilities
- ✅ Check current plan and data usage by mobile number
- ✅ Renew or upgrade subscription plans
- ✅ Answer policy questions using knowledge base (RAG - Retrieval Augmented Generation)
- ✅ Handle FAQs: roaming, billing, SIM swap, porting
- ✅ Provide friendly, AI-synthesized responses using Gemini

### Live Deployment
**URL**: https://telecom-api-925349905681.asia-south1.run.app/health

---

## Architecture

### System Flow Diagram
```
┌─────────────────────┐
│   End User (Chat)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Dialogflow CX      │ ◄─── NLU & Conversation Flow
│  (Agent)            │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────────────────┐
│      FastAPI Backend (Cloud Run)            │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Routes Layer                        │   │
│  │ - /webhook (Dialogflow webhook)     │   │
│  │ - /subscriber/* (Data retrieval)    │   │
│  │ - /renewal/* (Plan operations)      │   │
│  │ - /chat/* (Direct chat)             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Services Layer                      │   │
│  │ - Firestore Client                  │   │
│  │ - Gemini Client                     │   │
│  │ - Knowledge Search                  │   │
│  └─────────────────────────────────────┘   │
└────────┬────────────┬────────────┬──────────┘
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌───▼──────┐
    │Firestore│  │Vertex AI│  │Vertex AI │
    │(Subscriber                   Discovery
    │ & Plans)│  │Search   │  │Engine    │
    └────┬────┘  │(Gemini) │  │(Knowledge
         │       └────┬────┘  │ Base RAG)
         │            │       └──────────┘
    ┌────▼────────────▼──────────┐
    │   GCP Project              │
    │   (asia-south1 region)     │
    └────────────────────────────┘
```

### Data Flow
1. User sends message through Dialogflow CX
2. Dialogflow processes NLU and calls FastAPI webhook
3. Webhook extracts parameters (phone, intent, etc.)
4. API routes handle business logic:
   - Query Firestore for subscriber/plan data
   - Search knowledge base via Vertex AI Discovery Engine
   - Generate friendly response using Gemini
5. Response returned to Dialogflow
6. User receives final response

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **NLU** | Dialogflow CX | Conversation management, intent recognition |
| **Backend API** | FastAPI + Uvicorn | RESTful API server |
| **Hosting** | Google Cloud Run | Serverless deployment (auto-scaling) |
| **Database** | Firestore | Real-time subscriber & plan data |
| **Knowledge Base** | Vertex AI Search | Semantic search with RAG |
| **LLM** | Gemini 1.5 Flash | Response synthesis & generation |
| **Runtime** | Python 3.11 | Application runtime |
| **Container** | Docker | Containerization for Cloud Run |

### Key Python Libraries
```
fastapi                         # Web framework
uvicorn[standard]              # ASGI server
google-cloud-firestore         # Firestore SDK
google-cloud-aiplatform        # Vertex AI SDK
google-cloud-discoveryengine   # Discovery Engine for RAG
google-cloud-dialogflow-cx     # Dialogflow CX SDK
google-generativeai            # Gemini API
pydantic                        # Data validation
python-dotenv                  # Environment variables
google-cloud-logging           # Cloud Logging
```

---

## Directory Structure

```
telecom-support-bot/
├── README.md                          # Quick start guide
├── PROJECT_DOCUMENTATION.md           # This file
├── LICENSE                            # Project license
│
├── api/                               # FastAPI Backend
│   ├── main.py                        # Application entry point
│   ├── Dockerfile                     # Docker image specification
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── routes/                        # API endpoint handlers
│   │   ├── __init__.py
│   │   ├── subscriber.py              # GET subscriber info & plans
│   │   ├── renewal.py                 # POST plan renewal/upgrade
│   │   ├── webhook.py                 # POST Dialogflow webhook
│   │   └── chat.py                    # Direct chat endpoints
│   │
│   └── services/                      # Business logic layer
│       ├── __init__.py
│       ├── firestore_client.py        # Firestore operations
│       ├── gemini_client.py           # Gemini API wrapper
│       └── knowledge_search.py        # Vertex AI Search wrapper
│
├── dialogflow-export/                 # Dialogflow agent export
│   └── TelecomSupportBot.zip         # Agent backup (import into Dialogflow)
│
├── docs/                              # Knowledge base documents
│   ├── plans_faq.txt                 # Plan details & FAQ
│   ├── refund_policy.txt             # Refund policy documentation
│   ├── roaming_policy.txt            # International roaming policy
│   └── sample-conversations.md       # Example chat flows
│
└── scripts/                           # Utility scripts
    └── seed_firestore.py              # Initialize Firestore with sample data
```

---

## API Endpoints

### 1. Health Check
```http
GET /health
```
**Response:**
```json
{ "status": "ok" }
```

### 2. Get Subscriber Information
```http
GET /api/subscriber/{phone}
```
**Parameters:**
- `phone`: Mobile number (e.g., "+919000000001")

**Response:**
```json
{
  "phone": "+919000000001",
  "name": "Priya Sharma",
  "plan": "Unlimited Pro",
  "data_used_gb": 18.4,
  "total_data_gb": 100,
  "renewal_date": "2026-05-15",
  "status": "active"
}
```

**Error (404):**
```json
{
  "detail": "No account found for +919000000001"
}
```

### 3. List All Plans
```http
GET /api/plans
```
**Response:**
```json
{
  "plans": [
    {
      "id": "basic-plan",
      "name": "Basic Plan",
      "price_inr": 199,
      "data_gb": 20,
      "speed_mbps": 10,
      "validity_days": 30,
      "features": ["20GB data", "10Mbps speed", "100 SMS/day"]
    },
    {
      "id": "unlimited-pro",
      "name": "Unlimited Pro",
      "price_inr": 599,
      "data_gb": 100,
      "speed_mbps": 100,
      "validity_days": 30,
      "features": ["100GB data", "100Mbps speed", "Unlimited SMS"]
    },
    {
      "id": "family-pack",
      "name": "Family Pack",
      "price_inr": 999,
      "data_gb": 150,
      "speed_mbps": 100,
      "validity_days": 30,
      "features": ["150GB shared", "Up to 4 connections"]
    }
  ],
  "count": 3
}
```

### 4. Renew Plan
```http
POST /api/renew
Content-Type: application/json

{
  "phone": "+919000000001",
  "months": 1
}
```
**Response:**
```json
{
  "message": "Plan renewed successfully",
  "plan": "Unlimited Pro",
  "new_renewal_date": "2026-06-02",
  "months_added": 1
}
```

### 5. Upgrade Plan
```http
POST /api/upgrade
Content-Type: application/json

{
  "phone": "+919000000001",
  "new_plan": "Unlimited Pro"
}
```
**Response:**
```json
{
  "message": "Upgraded to Unlimited Pro",
  "old_plan": "Basic Plan",
  "new_plan": "Unlimited Pro",
  "new_data_gb": 100
}
```

### 6. Dialogflow Webhook
```http
POST /webhook
Content-Type: application/json
```
**Request Structure** (from Dialogflow):
```json
{
  "fulfillmentInfo": {
    "tag": "get_plan_info"
  },
  "sessionInfo": {
    "parameters": {
      "phone": "+919000000001"
    }
  }
}
```
**Response**: Varies by tag/intent

### 7. Knowledge Base Search
```http
GET /test-search?q=What+is+your+refund+policy
```
**Response:**
```json
{
  "query": "What is your refund policy",
  "answer": "Refund requests must be raised within 7 days of payment..."
}
```

---

## Services

### 1. Firestore Client (`firestore_client.py`)

**Purpose**: Database operations for subscribers and plans

**Key Functions**:

| Function | Purpose |
|----------|---------|
| `get_subscriber(phone)` | Fetch subscriber details by phone number |
| `update_subscriber(phone, data)` | Update subscriber information |
| `get_plan(plan_name)` | Fetch plan details by name |
| `get_all_plans()` | Fetch all available plans |

**Firestore Collections**:
- **subscribers**: Contains subscriber documents with fields:
  - `phone` (document ID)
  - `name`, `plan`, `data_used_gb`, `total_data_gb`
  - `renewal_date`, `status`

- **plans**: Contains plan documents with fields:
  - `id` (document ID)
  - `name`, `price_inr`, `data_gb`, `speed_mbps`
  - `validity_days`, `features`

### 2. Gemini Client (`gemini_client.py`)

**Purpose**: AI-powered response synthesis and natural language generation

**Key Functions**:

| Function | Purpose |
|----------|---------|
| `generate_friendly_response(kb_context, user_query)` | Generate conversational responses |

**Features**:
- Uses Gemini 1.5 Flash model
- Takes knowledge base context and user query
- Returns 2-3 conversational sentences
- Fallback to raw KB answer on error

**Configuration**:
- Project ID: From environment variable `PROJECT_ID`
- Region: us-central1
- Model: gemini-1.5-flash

### 3. Knowledge Search (`knowledge_search.py`)

**Purpose**: Semantic search and RAG (Retrieval Augmented Generation)

**Key Functions**:

| Function | Purpose |
|----------|---------|
| `search_knowledge_base(query)` | Search knowledge base and return AI-synthesized answer |

**Features**:
- Uses Vertex AI Discovery Engine
- Semantic search across policy documents
- Returns AI-generated summary with citations
- Includes adversarial query detection

**Configuration**:
- Project ID: From environment variable `PROJECT_ID`
- Data Store ID: From environment variable `DATA_STORE_ID`
- Location: global
- Page size: 3 results
- Include citations: Yes

**Fallback Strategy**:
1. Try to return AI summary from Discovery Engine
2. Fall back to first result snippet
3. Return user-friendly error message if unavailable

---

## Data Models

### Subscriber Schema
```python
{
  "phone": str,              # Mobile number (document ID)
  "name": str,               # Customer name
  "plan": str,               # Current plan name
  "data_used_gb": float,     # Data consumed in current period
  "total_data_gb": float,    # Total data allocation
  "renewal_date": str,       # YYYY-MM-DD format
  "status": str              # "active", "expiring", "expired"
}
```

### Plan Schema
```python
{
  "id": str,                 # Plan identifier (document ID)
  "name": str,               # Display name
  "price_inr": int,          # Price in Indian Rupees
  "data_gb": float,          # Monthly data allocation
  "speed_mbps": int,         # Maximum speed in Mbps
  "validity_days": int,      # Plan validity period
  "features": list[str]      # List of feature descriptions
}
```

### Webhook Request Schema
```python
{
  "fulfillmentInfo": {
    "tag": str               # Intent tag (e.g., "get_plan_info")
  },
  "sessionInfo": {
    "parameters": {
      "phone": str,          # Mobile number
      "plan": str,           # Plan name (optional)
      # ... other parameters
    }
  }
}
```

### API Request/Response Models (Pydantic)
```python
class RenewRequest(BaseModel):
    phone: str
    months: int = 1

class UpgradeRequest(BaseModel):
    phone: str
    new_plan: str
```

---

## Setup & Deployment

### Prerequisites
- Python 3.11+
- Google Cloud Project with enabled APIs
- Firestore database
- Dialogflow CX agent
- Vertex AI APIs enabled

### Local Development Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd telecom-support-bot
```

#### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
cd api
pip install -r requirements.txt
```

#### 4. Set Environment Variables
Create `.env` file:
```env
PROJECT_ID=your-gcp-project-id
DATA_STORE_ID=your-discovery-engine-datastore-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### 5. Seed Initial Data
```bash
cd ..
python scripts/seed_firestore.py
```

#### 6. Run Locally
```bash
cd api
uvicorn main:app --reload --port 8000
```

Visit: http://localhost:8000/docs (Swagger UI)

### Cloud Deployment (Google Cloud Run)

#### 1. Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  discoveryengine.googleapis.com \
  aiplatform.googleapis.com \
  dialogflow.googleapis.com
```

#### 2. Build and Push Docker Image
```bash
gcloud builds submit --region=asia-south1 \
  --config=cloudbuild.yaml
```

#### 3. Deploy to Cloud Run
```bash
gcloud run deploy telecom-api \
  --source api/ \
  --region asia-south1 \
  --platform managed \
  --memory 512Mi \
  --timeout 60 \
  --set-env-vars PROJECT_ID=your-project-id,DATA_STORE_ID=your-datastore-id
```

#### 4. Get Service URL
```bash
gcloud run services describe telecom-api \
  --region asia-south1 \
  --format 'value(status.url)'
```

#### 5. Configure Dialogflow Webhook
- Update webhook URL in Dialogflow CX agent settings
- Use the Cloud Run service URL from step 4

### Docker Build & Run

#### Build Image
```bash
cd api
docker build -t telecom-api:latest .
```

#### Run Locally
```bash
docker run -p 8080:8080 \
  -e PROJECT_ID=your-project-id \
  -e DATA_STORE_ID=your-datastore-id \
  -v ~/.config/gcloud/application_default_credentials.json:/app/credentials.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  telecom-api:latest
```

---

## Key Features

### 1. Real-Time Data Access
- Direct access to subscriber profiles
- Current data usage tracking
- Instant plan information retrieval

### 2. Intelligent Query Processing
- Natural language understanding via Dialogflow CX
- Entity extraction (phone, plan names)
- Context-aware responses

### 3. Knowledge-Based Assistance
- RAG-powered knowledge base search
- Policy document access (refund, roaming, etc.)
- Semantic search with citations

### 4. Multi-Channel Support
- Dialogflow CX integration (primary)
- Direct API endpoints (secondary)
- REST API for custom clients

### 5. AI-Powered Responses
- Gemini 1.5 Flash synthesis
- Conversational tone generation
- Context-aware answer formatting

### 6. Scalability
- Serverless architecture (Cloud Run)
- Auto-scaling based on demand
- Stateless API design

---

## Development Guide

### Project Structure Best Practices

**Routes Layer** (`routes/`)
- Each route file handles a specific domain
- Use FastAPI routers for organization
- Include proper HTTP status codes
- Implement error handling

**Services Layer** (`services/`)
- Pure business logic
- No FastAPI dependencies
- Reusable across routes
- Comprehensive error logging

**Entry Point** (`main.py`)
- CORS configuration
- Router registration
- Middleware setup
- Basic health checks

### Adding New Features

#### Example: Add New Route
```python
# routes/new_feature.py
from fastapi import APIRouter
from services.firestore_client import get_subscriber

router = APIRouter()

@router.get("/api/feature/{phone}")
async def new_feature(phone: str):
    subscriber = get_subscriber(phone)
    if not subscriber:
        raise HTTPException(404, "Not found")
    # Process logic
    return {"result": "data"}
```

Then register in `main.py`:
```python
from routes.new_feature import router as new_feature_router
app.include_router(new_feature_router, tags=["New Feature"])
```

#### Example: Add New Service
```python
# services/new_service.py
import logging

def process_data(input_data: str) -> str:
    try:
        # Implementation
        result = do_something(input_data)
        return result
    except Exception as e:
        logging.error(f"new_service_error: {e}")
        return "Fallback response"
```

Use in routes:
```python
from services.new_service import process_data

@router.post("/api/process")
async def process_endpoint(data: str):
    result = process_data(data)
    return {"result": result}
```

### Testing

#### Test Health Endpoint
```bash
curl https://telecom-api-925349905681.asia-south1.run.app/health
```

#### Test Subscriber Lookup
```bash
curl "https://telecom-api-925349905681.asia-south1.run.app/api/subscriber/%2B919000000001"
```

#### Test Knowledge Base Search
```bash
curl "https://telecom-api-925349905681.asia-south1.run.app/test-search?q=refund+policy"
```

### Debugging

**View Logs**:
```bash
gcloud run logs read telecom-api --region asia-south1 --limit 50
```

**Monitor Performance**:
```bash
gcloud run services describe telecom-api --region asia-south1
```

**Check Firestore Data**:
```bash
gcloud firestore documents list --collection-id subscribers
```

---

## Sample Conversation

### User Query 1: Check Plan
```
User: What plan am I on?
Bot:  Please share your registered mobile number.
User: +91-9000000001
Bot:  You are on Unlimited Pro. It renews on 2026-05-15. Status: active.
      You've used 18.4 GB of your 100 GB allowance.
```

### User Query 2: Policy Question
```
User: What is your refund policy?
Bot:  Refund requests must be raised within 7 days of payment.
      [AI-synthesized response from refund_policy.txt]
```

### User Query 3: Plan Upgradeimport { useState, useContext, useEffect } from "react";
import { ChatContext } from "../../context/ChatContext";
import { sendMessage } from "../../services/api";

// Parse bot reply to extract account data
function parseReply(text, verifyPhone, setAccountData) {
  // Detect phone number typed by user
  const phoneMatch = text.match(/\+?\d{10,13}/);
  if (phoneMatch) {
    const p = phoneMatch[0];
    verifyPhone(p.startsWith("+") ? p : "+" + p);
  }

  // Detect "Verified ✓ Account +91..." in bot reply
  const verifyBotMatch = text.match(/Verified.*?(\+\d{10,13})/i);
  if (verifyBotMatch) verifyPhone(verifyBotMatch[1]);

  // Extract plan info: "Your current plan is X. It renews on Y."
  const planMatch  = text.match(/Your current plan is ([^.]+)\./);
  const renewMatch = text.match(/renews on ([\d-]+)/i);
  const statusMatch = text.match(/Status:\s*(\w+)/i);

  // Extract data usage: "Used: 4.1 GB of 20 GB"
  const dataMatch = text.match(/Used:\s*([\d.]+)\s*GB of\s*([\d.]+)\s*GB/);

  if (planMatch || dataMatch) {
    setAccountData((prev) => ({
      ...(prev || {}),
      ...(planMatch  ? { plan:    planMatch[1].trim() }                            : {}),
      ...(renewMatch ? { renewal: renewMatch[1] }                                  : {}),
      ...(statusMatch ? { status: statusMatch[1] }                                 : {}),
      ...(dataMatch  ? { dataUsed: parseFloat(dataMatch[1]), dataTotal: parseFloat(dataMatch[2]) } : {}),
    }));
  }
}

export default function ChatInput() {
  const [input, setInput]   = useState("");
  const [loading, setLoading] = useState(false);

  const {
    addMessage, messages,
    sessionId, setSessionId,
    resetSession,
    verifyPhone, setAccountData,
    updateDialogflowStat,
  } = useContext(ChatContext);

  const handleSend = async (textOverride) => {
    const text = (textOverride || input).trim();
    if (!text || loading) return;

    setLoading(true);
    setInput("");

    const isFirstMessage = messages.filter((m) => m.sender === "user").length === 0;
    const effectiveSessionId = isFirstMessage ? null : sessionId;

    // Parse user message for phone detection
    parseReply(text, verifyPhone, setAccountData);

    addMessage({ sender: "user", text });

    const typingId = `typing-${Date.now()}`;
    addMessage({ id: typingId, sender: "bot", text: "", isLoading: true });

    const t0 = Date.now();

    try {
      const result = await sendMessage(text, effectiveSessionId);

      const ms = Date.now() - t0;
      updateDialogflowStat(ms + "ms");

      addMessage({ removeId: typingId });
      addMessage({
        sender: "bot",
        text: result.reply,
        meta: ["FastAPI · Cloud Run"],
      });

      // Parse bot reply for plan/data info
      parseReply(result.reply, verifyPhone, setAccountData);

      if (result.session_id && result.session_id !== sessionId) {
        setSessionId(result.session_id);
      }

      if (result.end_session) {
        setTimeout(resetSession, 2500);
      }
    } catch {
      updateDialogflowStat("err");
      addMessage({ removeId: typingId });
      addMessage({ sender: "bot", text: "Something went wrong. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handler = (e) => handleSend(e.detail);
    window.addEventListener("chip-click", handler);
    return () => window.removeEventListener("chip-click", handler);
  }, [sessionId, loading]);

  return (
    <div
      className="flex items-center gap-3 flex-shrink-0"
      style={{
        padding: "13px 16px",
        borderTop: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <input
        style={{
          flex: 1,
          background: "#18181f",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: 12,
          padding: "11px 17px",
          color: "#e8e8f0",
          fontSize: 15,
          fontFamily: "'DM Sans', sans-serif",
          outline: "none",
          transition: "border-color 0.15s",
        }}
        placeholder="Ask about your plan, renewals, or policies..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
        onFocus={(e)  => (e.target.style.borderColor = "#7c6af7")}
        onBlur={(e)   => (e.target.style.borderColor = "rgba(255,255,255,0.07)")}
        disabled={loading}
      />
      <button
        onClick={() => handleSend()}
        disabled={loading}
        style={{
          padding: "11px 22px", borderRadius: 12,
          border: "none",
          background: loading ? "rgba(124,106,247,0.45)" : "#7c6af7",
          color: "#fff",
          fontSize: 14,
          fontWeight: 500,
          fontFamily: "'DM Sans', sans-serif",
          cursor: loading ? "not-allowed" : "pointer",
          whiteSpace: "nowrap",
          transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!loading) e.target.style.background = "#a594ff"; }}
        onMouseLeave={(e) => { if (!loading) e.target.style.background = "#7c6af7"; }}
      >
        {loading ? "···" : "Send ↗"}
      </button>
    </div>
  );
}
```
User: I want to upgrade my plan
Bot:  What plan would you like to upgrade to?
User: Family Pack
Bot:  Upgraded successfully! You now have the Family Pack with 150GB data
      shared across up to 4 connections.
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROJECT_ID` | Yes | None | Google Cloud Project ID |
| `DATA_STORE_ID` | Yes | None | Vertex AI Discovery Engine Data Store ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | None | Path to GCP service account key JSON |

---

## Troubleshooting

### Issue: "No credentials found"
**Solution**: Set `GOOGLE_APPLICATION_CREDENTIALS` to your service account key file path

### Issue: "Firestore connection timeout"
**Solution**: Verify Firestore is enabled in GCP project and network has outbound access

### Issue: "Knowledge base search returns empty"
**Solution**: Check that Discovery Engine data store is populated with documents

### Issue: "Dialogflow webhook not responding"
**Solution**: Verify Cloud Run service URL in Dialogflow agent settings matches deployed URL

---

## Performance Metrics

- **Webhook Response Time**: ~500ms average (includes Gemini synthesis)
- **Subscriber Lookup**: ~100ms
- **Plan List**: ~50ms
- **Knowledge Search**: ~800ms average

---

## Security Considerations

✅ **Implemented**:
- Authentication via GCP service accounts
- CORS configured for specific origins
- Input validation via Pydantic
- Secure environment variable management

⚠️ **Recommended**:
- Add API key authentication for public endpoints
- Implement rate limiting
- Add input sanitization for user queries
- Use VPC for database connections
- Enable Cloud Armor for DDoS protection

---

## Future Enhancements

1. **Multi-language Support**: Add i18n for regional languages
2. **Analytics**: Track user interactions and bot performance
3. **Payment Integration**: Direct plan upgrade payments
4. **Advanced Personalization**: User history and preferences
5. **Mobile App**: Native mobile client
6. **Voice Support**: Voice query integration
7. **Sentiment Analysis**: Monitor customer satisfaction
8. **A/B Testing**: Test different response strategies

---

## License

See [LICENSE](LICENSE) file for details.

---

## Support & Contact

For issues, feature requests, or questions:
- Create an issue in the repository
- Check existing documentation in `/docs`
- Review sample conversations in `sample-conversations.md`

---

**Last Updated**: May 2026  
**Version**: 1.0.0  
**Status**: Production Ready
