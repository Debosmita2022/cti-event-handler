# CTI Event Handler — Agentic AI Pipeline

An async Python microservice that processes contact center call events, generates AI-powered call summaries using chain-of-thought prompting, posts structured outputs to Salesforce CRM, and provides a natural language agent for autonomous CRM action taking — grounded in a RAG policy knowledge base.

## Architecture


CTI Event (call_started)
→ FastAPI endpoint (202 immediately)
→ [background] fetch call metadata + agent profile (concurrent)
→ CallContext stored

CTI Event (call_ended + transcript)
→ FastAPI endpoint (202 immediately)
→ [background] LLM inference (CoT) → structured summary
→ Salesforce Case created + updated (concurrent with ACW)
→ Escalation flagged if required

Natural language instruction
→ RAG retrieval (FAISS + sentence-transformers)
→ Policy context injected
→ LLM selects tool (ReAct pattern)
→ Salesforce CRM action executed
→ Policy-grounded NBA returned


## Key Features

- **Async pipeline** — BackgroundTasks, asyncio.gather, non-blocking 202 responses
- **LLM inference** — Chain-of-thought prompting with function calling for schema-enforced outputs
- **RAG pipeline** — FAISS index over policy knowledge base, policy-grounded NBA suggestions
- **Eval framework** — 10-transcript golden set (CoT 9.6 vs Direct 9.3), RAG vs no-RAG comparison
- **Salesforce integration** — SOQL queries, Case CRUD, AI summary writing to Description field
- **NL → CRM agent** — ReAct pattern, 5 tools, autonomous action taking from natural language
- **Production resilience** — Exponential backoff retry, dead letter storage, structured logging
- **Multi-site deployment** — Docker + docker-compose, runtime env injection, consistent across sites

## Stack

- Python 3.11, FastAPI, uvicorn
- OpenAI GPT-4o (function calling, chain-of-thought prompting)
- FAISS + sentence-transformers (RAG pipeline)
- Salesforce (simple-salesforce, Cases API, SOQL)
- Docker, docker-compose
- httpx, Pydantic, python-jose

## Project Structure


cti_services/
├── main.py                  # FastAPI service — CTI event endpoints
├── simulator.py             # Post-call pipeline — LLM + Salesforce
├── llm.py                   # LLM inference — CoT, function calling, evals
├── salesforce_cases.py      # Salesforce CRUD — Cases API, SOQL
├── salesforce_agent.py      # NL agent — ReAct pattern, RAG-grounded
├── rag_pipeline.py          # FAISS index, retrieval, context injection
├── knowledge_base.py        # Policy documents — cancellation, fraud, billing
├── auth.py                  # JWT issuance and validation
├── config.py                # Environment variable management
├── logger.py                # Structured logging with call_id correlation
├── eval_runner.py           # LLM-as-judge eval harness
├── eval_transcripts.py      # 10-transcript golden test set
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-site deployment
├── requirements.txt         # Dependencies
└── tests/                   # Test scripts


## Running Locally


# 1. Clone and install
git clone https://github.com/Debosmita2022/cti-event-handler.git
cd cti-event-handler
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# edit .env with your keys

# 3. Start the service
uvicorn main:app --reload

# 4. Fire a call lifecycle
# Start call
curl -X POST http://localhost:8000/call/started \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"call_id":"CALL-001","agent_id":"AGT-447","queue":"billing","phone":"+1-800-555-0192"}'

# End call with transcript
curl -X POST http://localhost:8000/call/ended \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"call_id":"CALL-001","transcript":"Agent: How can I help? Customer: I was charged twice..."}'

# 5. Run the RAG agent
python -c "from salesforce_agent import run_agent; print(run_agent('Customer wants to cancel their policy'))"


## Docker Deployment
docker-compose up -d


## Eval Results

### Prompt Engineering — CoT vs Direct (10 transcripts)

|               Dimension                   | Direct | CoT     |
|-------------------------------------------|--------|---------|
| Overall                                   | 9.3    | 9.6     |
| Sentiment correctness                     | 8.9    | 9.6     |
| NBA specificity                           | 8.4    | 8.6     |
| Issue accuracy                            | 10.0   | 10.0    |
| Escalation accuracy                       | 10.0   | 10.0    |

CoT wins on 6/10 transcripts. Biggest gap: sentiment correctness on ambiguous calls — retention events and partial resolutions where direct prompting misread lukewarm acceptance as positive.

### RAG vs No-RAG (4 policy query types)

| Query Type    |                          Without RAG    |                       With RAG                                                          |
|---------------|-----------------------------------------|-----------------------------------------------------------------------------------------|
|Cancellation   | Generic — "follow cancellation process" | POL-001 cited. 20%/30% retention discount. Mandatory disclosure. Log CANC-FULL.         |
|Reinstatement  | "Escalate to Policy Management"         | POL-002 cited. 30-day window check. Immediate reinstatement if eligible. Log REINSTATE. |
|Billing dispute| "Assign to Billing Department"          | POL-005 cited. Premium tier expedited refund. Log BILL-DISP.                            |
|Fraud alert    | "Flag and escalate"                     | POL-006 cited. Enhanced identity verification before any action. Log FRAUD-ALERT.       |

**Critical finding:** Fraud query — without RAG the agent skips identity verification. With RAG it correctly performs enhanced verification before any action. In a regulated contact center this is the difference between compliant handling and a regulatory breach.

## API Endpoints

| Method | Endpoint      | Auth      | Description                               |
|--------|---------------|-----------|-------------------------------------------|
| POST   | /call/started | X-API-Key | Receive CTI call_started event            |
| POST   | /call/ended   | X-API-Key | Receive CTI call_ended event + transcript |
| GET    | /calls        |JWT Bearer | List active calls in store                |
| GET    | /health       | None      | Service health + SRM reachability         |
| GET    | /dead-letters | X-API-Key | Failed events pending replay              |
| POST   | /token        | None      | Issue JWT via OAuth 2.0 Client Credentials|

## Environment Variables

# See .env.example for full list
        CTI_API_KEY= inbound API key for CTI endpoints
        OPENAI_API_KEY=# GPT-4o for LLM inference and agent
        SALESFORCE_USERNAME=# Salesforce org username
        SALESFORCE_PASSWORD=# Salesforce org password
        SALESFORCE_SECURITY_TOKEN= # Salesforce security token
        JWT_SECRET=# min 32 chars for JWT signing
        SRM_BASE_URL=# SRM endpoint (httpbin for dev)


## Background

Built to demonstrate production-grade Agentic AI engineering — connecting hands-on Uniphore U-Assist production experience (multi-brand intent recognition, CTI/SIP event handling, multi-site deployment) with Python implementation of the same pipeline from first principles.

The architecture mirrors U-Assist's post-call pipeline: CTI event receiver → context enrichment → LLM summary service → SRM integration → ACW automation. Understanding both the platform and the code means debugging at any layer without waiting for vendor support.


## Demo
[▶ Watch demo](https://youtu.be/BkqaS-0Ro1Y?si=1Hqx5Z6xt2ixy1u2)