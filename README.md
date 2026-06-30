# Travel Reimbursement Approval Agent

> Agent that evaluates employee travel reimbursement claims against company policy using RAG-grounded reasoning and multi-tool orchestration.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-orange.svg)](https://langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Docker](#docker)
- [API Reference](#api-reference)
- [Sample Outputs](#sample-outputs)
- [Testing](#testing)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [Future Improvements](#future-improvements)

---

## Architecture

### High-Level Overview

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  REST Client │────▶│            FastAPI Application            │
│  (curl/UI)   │◀────│                                          │
└─────────────┘     │  ┌────────────────────────────────────┐  │
                    │  │       Reimbursement Agent           │  │
                    │  │    (LangChain AgentExecutor)        │  │
                    │  │                                    │  │
                    │  │  ┌─────────┐  ┌─────────────────┐ │  │
                    │  │  │   LLM   │  │   7 Agent Tools  │ │  │
                    │  │  │GPT-4.1/ │  │                 │ │  │
                    │  │  │ Gemini  │  │ • Policy Lookup  │ │  │
                    │  │  └─────────┘  │ • Receipt Check  │ │  │
                    │  │               │ • Expense Limit  │ │  │
                    │  │  ┌─────────┐  │ • Duplicate Chk  │ │  │
                    │  │  │  RAG    │  │ • Approval Mtx   │ │  │
                    │  │  │ (FAISS) │  │ • Currency Conv  │ │  │
                    │  │  └─────────┘  │ • Output Valid   │ │  │
                    │  │               └─────────────────┘ │  │
                    │  └────────────────────────────────────┘  │
                    └──────────────────────────────────────────┘
```

### Agent Workflow

1. **Claim Intake** — FastAPI receives a JSON reimbursement claim
2. **RAG Retrieval** — Relevant policy sections are fetched from FAISS
3. **LLM Reasoning** — The agent decides which tools to call
4. **Tool Execution** — 7 tools run sequentially based on LLM decisions
5. **Output Validation** — The final response is validated against the schema
6. **Structured Response** — JSON with decision, amounts, deductions, and audit trail

> See [docs/architecture/architecture.md](docs/architecture/architecture.md) for full Mermaid diagrams.

---

## Features

| Feature | Description |
|---------|-------------|
| **Agentic Design** | LLM decides which tools to call based on claim context |
| **RAG** | Policy documents are chunked, embedded, and stored in FAISS |
| **7 Agent Tools** | Policy lookup, receipt check, expense limits, duplicates, approval matrix, currency conversion, output validation |
| **4 Decision Types** | Approved, Partially Approved, Rejected, Manual Review |
| **Structured Output** | Consistent JSON with decision, amounts, deductions, confidence, and audit trail |
| **Configurable LLM** | Switch between OpenAI GPT-4.1 and Google Gemini 2.5 Flash |
| **Logging** | 4 rotating log files (app, agent, API, error) |
| **Test Suite** | Unit tests for tools, schemas, API, and agent |
| **Docker Ready** | Single-command `docker compose up` |
| **CI/CD** | GitHub Actions for linting, testing, and Docker builds |

---

## Project Structure

```
travel-reimbursement-agent/
├── app/
│   ├── agents/                 # LangChain agent orchestration
│   │   ├── llm_factory.py      # LLM provider factory (OpenAI / Google)
│   │   └── reimbursement_agent.py  # Core agent with tool binding
│   ├── api/
│   │   └── routes.py           # FastAPI endpoints
│   ├── config/
│   │   └── settings.py         # Centralised configuration
│   ├── core/
│   │   └── application.py      # FastAPI app factory
│   ├── exceptions/             # Custom exception hierarchy
│   ├── middleware/
│   │   ├── error_handler.py    # Global exception handler
│   │   └── request_logging.py  # HTTP request logging
│   ├── models/                 # Domain models
│   ├── prompts/
│   │   └── templates.py        # Prompt templates
│   ├── rag/
│   │   ├── embeddings.py       # Embedding model factory
│   │   └── vector_store.py     # FAISS index management
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic services
│   ├── tools/                  # 7 agent tools
│   │   ├── policy_lookup.py
│   │   ├── receipt_completeness.py
│   │   ├── expense_limit.py
│   │   ├── duplicate_claim.py
│   │   ├── approval_matrix.py
│   │   ├── currency_conversion.py
│   │   └── output_validator.py
│   └── utils/
│       └── logging_config.py   # Rotating log setup
├── data/
│   ├── policies/               # Markdown policy documents (for RAG)
│   ├── claims/                 # 5 sample claims
│   ├── receipts/               # Sample receipt metadata
│   └── sample_outputs/         # Expected outputs
├── tests/                      # Test suite
├── docs/architecture/          # Mermaid diagrams
├── scripts/
│   ├── build_index.py          # FAISS index builder
│   └── test_claim.py           # CLI claim tester
├── logs/                       # Rotating log files
├── .github/workflows/ci.yml    # GitHub Actions CI
├── main.py                     # Application entry point
├── config.ini                  # Application configuration
├── .env.example                # Environment variable template
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.12+
- An API key for OpenAI or Google Gemini

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/travel-reimbursement-agent.git
cd travel-reimbursement-agent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and set your API key:
# OPENAI_API_KEY=sk-your-key-here
# or
# LLM_PROVIDER=google
# GOOGLE_API_KEY=your-key-here
```

### 5. Build the FAISS Index

```bash
python scripts/build_index.py
```

---

## Running the Application

### Local Development

```bash
python main.py
```

The API will be available at **http://localhost:8000**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Evaluate a claim
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @data/claims/claim_001_approved.json

# Test with the CLI script
python scripts/test_claim.py data/claims/claim_001_approved.json
```

---

## Docker

### Build and Run

```bash
# Single command startup
docker compose up --build

# Or manually
docker build -t travel-reimbursement-agent .
docker run -p 8000:8000 --env-file .env travel-reimbursement-agent
```

### Stop

```bash
docker compose down
```

---

## API Reference

### POST /evaluate

Evaluate a travel reimbursement claim.

**Request Body:**
```json
{
  "claim_id": "CLM-2025-101",
  "employee_id": "EMP-1001",
  "employee_name": "Alice Johnson",
  "travel_type": "domestic",
  "destination": "New York, NY",
  "business_purpose": "Client meeting",
  "travel_start_date": "2025-08-10",
  "travel_end_date": "2025-08-13",
  "expenses": [
    {
      "expense_type": "flight",
      "description": "Economy round-trip",
      "amount": 450.00,
      "currency": "USD",
      "date": "2025-08-10",
      "receipt_id": "REC-001"
    }
  ],
  "receipts": [
    {
      "receipt_id": "REC-001",
      "expense_type": "flight",
      "vendor": "United Airlines",
      "amount": 450.00,
      "currency": "USD",
      "date": "2025-08-10",
      "is_attached": true
    }
  ],
  "total_claimed_amount": 450.00,
  "claim_currency": "USD"
}
```

**Response:**
```json
{
  "claim_id": "CLM-2025-101",
  "decision": "approved",
  "approved_amount": 450.00,
  "rejected_amount": 0.00,
  "deductions": [],
  "confidence_score": 0.95,
  "policy_references": ["Section 4: Domestic flight limit $1,500"],
  "missing_documents": [],
  "reasoning": "All expenses within policy limits...",
  "tools_used": ["policy_lookup", "receipt_completeness_check", "expense_limit_check"],
  "audit_trail": [
    {
      "step": 1,
      "tool": "policy_lookup",
      "input_summary": "domestic travel policy",
      "output_summary": "Retrieved 5 chunks"
    }
  ]
}
```

### POST /upload-policy

Upload a new policy document to the RAG index.

```bash
curl -X POST http://localhost:8000/upload-policy \
  -F "file=@new_policy.md"
```

### GET /health

```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"1.0.0","environment":"development","timestamp":"..."}
```

### GET /version

```bash
curl http://localhost:8000/version
# {"app_name":"Travel Reimbursement Approval Agent","version":"1.0.0","python_version":"3.12.0","llm_provider":"openai"}
```

### GET /metrics

```bash
curl http://localhost:8000/metrics
# {"total_evaluations":5,"successful_evaluations":4,"failed_evaluations":1,...}
```

---

## Sample Outputs

The `data/sample_outputs/` directory contains expected outputs for three scenarios:

| Claim | Scenario | Expected Decision |
|-------|----------|-------------------|
| CLM-2025-101 | Fully compliant domestic trip | **Approved** |
| CLM-2025-103 | Policy violations (first class, luxury, missing receipts) | **Rejected** |
| CLM-2025-104 | Emergency travel, JPY currency, policy exception | **Manual Review** |

---

## Testing

### Run All Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Test Categories

| Test File | Coverage |
|-----------|----------|
| `test_schemas.py` | Pydantic validation, edge cases |
| `test_tools.py` | All 7 tools independently |
| `test_api.py` | API endpoints, validation, Swagger |
| `test_agent.py` | Agent parsing, fallback, tool config |

---

## Design Decisions & Trade-offs

### LangChain Tool-Calling Agent over ReAct
Tool-calling agents provide more deterministic behavior and better structured outputs than ReAct-style agents. The `create_tool_calling_agent` API maps directly to the model's native function-calling capability, reducing prompt engineering overhead.

### FAISS over Chroma/Pinecone
FAISS is in-process (no external service needed), fast for small-to-medium document sets, and persists to disk. For a demo with 3 policy documents, the operational simplicity outweighs the query features of managed vector DBs.

### Separate Prompts Module
All prompts live in `app/prompts/templates.py`. This makes them auditable, version-controllable, and easy to swap without touching agent logic.

### Manual Review as Default Fallback
When the agent is uncertain (low confidence, ambiguous policy, parsing failure), it routes to `manual_review` instead of forcing a potentially incorrect decision. This is important for a financial compliance system.

### Static Currency Rates
Using a static exchange-rate table avoids external API dependencies in demo/testing. A production system would integrate a live rate API.

### In-Memory Duplicate Store (trade-off)
The duplicate claim checker uses an in-memory list. In production, this would query a claim database.

### No Authentication (trade-off)
The API has no auth layer. In production, API keys, OAuth, or JWT would be required.

---

## Future Improvements

- [ ] Persistent claim database (PostgreSQL) for production duplicate detection
- [ ] Live currency API integration with caching
- [ ] Authentication layer (OAuth 2.0 / JWT)
- [ ] Streaming responses for real-time agent reasoning feedback
- [ ] Multi-modal receipt analysis (OCR for receipt images)
- [ ] Web UI for claim submission and review
- [ ] Evaluation framework with LLM-as-judge for output quality scoring
- [ ] Rate limiting and request throttling
- [ ] Prometheus metrics and Grafana dashboards

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
