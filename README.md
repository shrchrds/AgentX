# AgentX — Enterprise Multi-Agent Legal Intelligence Framework

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Orchestration](https://img.shields.io/badge/LangGraph-StateGraph-orange.svg)](https://python.langchain.com/docs/langgraph)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20GPT--4-412991.svg)](https://openai.com/)
[![Tests](https://img.shields.io/badge/Tests-144%20Passed%20(100%25)-success.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)

> **Production-grade multi-agent collaboration platform for complex legal document analysis, contract risk scoring, and legal precedent research using dynamic LangGraph DAG workflows, multi-format document ingestion, and hybrid vector memory.**

---

## Table of Contents

- [Executive Summary & Realistic Value Creation](#executive-summary--realistic-value-creation)
- [Why AgentX is Not a Toy Project](#why-agentx-is-not-a-toy-project)
- [System Architecture](#system-architecture)
- [Specialized Legal Agents](#specialized-legal-agents)
- [Document Ingestion Pipeline](#document-ingestion-pipeline)
- [Hybrid Multi-Tier Memory Store](#hybrid-multi-tier-memory-store)
- [Production Security & LLM Guardrails](#production-security--llm-guardrails)
- [User Interfaces](#user-interfaces)
  - [Full-Featured Web Dashboard](#full-featured-web-dashboard)
  - [Interactive Terminal CLI Demo](#interactive-terminal-cli-demo)
- [Quick Start & Deployment](#quick-start--deployment)
  - [Prerequisites](#prerequisites)
  - [Local Installation](#local-installation)
  - [1-Click Launchers](#1-click-launchers)
  - [Docker & Docker Compose](#docker--docker-compose)
- [API Documentation](#api-documentation)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [AI Engineer Portfolio Competencies](#ai-engineer-portfolio-competencies)
- [Project Structure](#project-structure)
- [License](#license)

---

## Executive Summary & Realistic Value Creation

In modern enterprise legal departments and law firms:
- **The Operational Bottleneck**: Senior attorneys and paralegals spend **4 to 8 hours** manually reviewing each 30-to-100 page corporate contract, vendor agreement, or NDA. At average billable rates of **$350–$650/hour**, manual contract triage consumes massive overhead and creates severe turnaround friction.
- **The Generic AI Failure Mode**: Naive LLM chat wrappers fail in legal domains. Single-prompt models hallucinate enforceability standards, fail to retain document-wide state, exceed token context windows without structured chunking, and lack auditability.
- **The AgentX Solution**: AgentX replaces monolithic prompts with a **deterministic, asynchronous multi-agent coordination system**:
  1. **Autonomous Task Decomposition**: Automatically classifies intake queries and documents into specialized sub-analyses.
  2. **Concurrent Multi-Agent Fan-Out**: Simultaneously evaluates contract terms, identifies conflicting judicial precedents, and scores compliance liabilities across jurisdictions.
  3. **Multi-Format Ingestion**: Ingests production legal documents (**PDF, DOCX, TXT, MD**) with size checks, encryption defense, and encoding recovery.
  4. **Quantifiable ROI**: Reduces initial contract and document risk assessment time from **hours to under 45 seconds** with structured severity scoring and citation trails.

---

## Why AgentX is Not a Toy Project

| Feature | Typical "Toy" / College AI Project | AgentX Enterprise Implementation |
| :--- | :--- | :--- |
| **Agent Topology** | Single prompt with generic system prompt | **LangGraph StateGraph DAG** with dynamic router, concurrent agent fan-out, and synthesis |
| **State & Memory** | Ephemeral python dictionary lost on reload | **Pluggable Multi-tier Memory**: In-memory, **FAISS vector store** with similarity search, and **Redis** with TTL |
| **Document Intake** | Raw text box with 500-word limit | **Multi-Format Document Ingestion Engine** (PDF, Word DOCX, Markdown, Text) with size & truncation guards |
| **Security & Guardrails** | Zero protection against prompt injection | **Defense-in-depth**: Regex-based prompt injection neutralization, output sanitization, schema guarantees |
| **Reliability & Testing** | 0 tests or manual print statements | **144 unit & integration tests** passing (100%), with fully mocked LLM/Redis isolation |
| **Operational Readiness** | Unstructured console prints | **FastAPI async API**, rate-limiting (SlowAPI), bearer auth, `/health` probes, and Docker Compose |
| **User Experience** | Basic command-line script | **Modern React 19 + Vite dashboard** + **Rich Terminal CLI** (`app/cli.py`) + **OpenAPI 3.0 docs** |

---

## System Architecture

AgentX utilizes an event-driven, asynchronous workflow managed by a **LangGraph StateGraph**.

```
                        ┌─────────────────────────────────────────┐
                        │   Client (Web UI / REST API / CLI Demo) │
                        └────────────────────┬────────────────────┘
                                             │  (PDF, DOCX, JSON Query)
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │        FastAPI API Gateway Layer        │
                        │    - Bearer Auth & SlowAPI Rate Limiting│
                        │    - Multi-Format Document Ingestion   │
                        │    - Pydantic v2 Input/Output Schemas   │
                        └────────────────────┬────────────────────┘
                                             │
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │     AgentOrchestrator (LangGraph)       │
                        │                                         │
                        │       [1. TaskRouter Node]              │
                        │         - Classifies legal domain       │
                        │         - Determines agent fan-out      │
                        │                     │                   │
                        │                     ▼                   │
                        │      [2. Concurrent Agent Execution]    │
                        │    ┌──────────────┬──────────────┐      │
                        │    ▼              ▼              ▼      │
                        │ ContractReview   CaseAnalysis   RiskAnalysis
                        │    └──────────────┴──────────────┘      │
                        │                     │                   │
                        │                     ▼                   │
                        │       [3. Result Aggregator Node]       │
                        │         - Synthesizes findings          │
                        │         - Calculates severity score     │
                        │         - Handles fallback & errors     │
                        └────────────────────┬────────────────────┘
                                             │
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │       Hybrid Memory & Vector Store      │
                        │   ┌─────────────┬──────────────────┐    │
                        │   │ In-Memory   │ FAISS Vector DB  │    │
                        │   │ (Local Test)│ (Semantic Search)│    │
                        │   ├─────────────┴──────────────────┤    │
                        │   │ Redis (Distributed Production) │    │
                        │   └────────────────────────────────┘    │
                        └─────────────────────────────────────────┘
```

### Orchestration State Lifecycle (`app/orchestrator/`)
1. **`classify`**: Evaluates task contents using deterministic routing rules, selecting one or multiple specialized agents.
2. **`execute_agents`**: Executes required agents asynchronously and concurrently using `asyncio.gather`, minimizing latency.
3. **`aggregate_results`**: Combines individual agent responses, generates execution metadata, computes overall risk posture, and writes audit records to memory.
4. **`handle_error`**: Intercepts downstream timeouts, rate limits, or parse faults, ensuring the client receives a structured response rather than an uncaught 500 error.

---

## Specialized Legal Agents

All agents inherit from [`LegalAgent`](file:///f:/PER/DATA_SCIENCE/Euron/InternshipsProjects/HARD/AgentX/app/agents/base.py) and feature domain-tuned system prompts and injection sanitizers:

### 1. `ContractReviewAgent` (`app/agents/contract_review.py`)
- **Focus**: Key obligations, indemnification clauses, termination provisions, non-compete enforceability, governing law, and liability caps.
- **Output**: Clause-by-clause breakdown, ambiguity flags, and redline recommendations.

### 2. `CaseAnalysisAgent` (`app/agents/case_analysis.py`)
- **Focus**: Judicial precedents, statutory frameworks, jurisdiction-specific case law citations, and litigation posture.
- **Output**: Relevant legal precedents, judicial trends, and strategic counter-arguments.

### 3. `RiskAnalysisAgent` (`app/agents/risk_analysis.py`)
- **Focus**: Liability exposure, regulatory compliance (GDPR, CCPA, FTC), breach penalties, and operational hazards.
- **Output**: Categorized risk matrix (High / Medium / Low), financial exposure estimates, and mitigation strategies.

---

## Document Ingestion Pipeline

Legal professionals work with real documents, not short text snippets. AgentX includes a hardened, enterprise-grade ingestion engine in [`app/utils/document_parser.py`](file:///f:/PER/DATA_SCIENCE/Euron/InternshipsProjects/HARD/AgentX/app/utils/document_parser.py):

- **Supported Formats**:
  - **PDF (`.pdf`)**: Extracted via `pypdf` with page-by-page streaming, metadata extraction, and encrypted file detection.
  - **Microsoft Word (`.docx`)**: Extracted via `python-docx`, parsing both body paragraphs and embedded data tables.
  - **Plain Text & Markdown (`.txt`, `.md`)**: Automated multi-encoding recovery (UTF-8, Latin-1, Windows CP-1252 fallbacks).
- **Safety Guards**:
  - Strict **10 MB payload limit** preventing memory exhaustion attacks.
  - **50,000 character soft truncation** with user-visible truncation warnings and token accounting.
  - Graceful library fallback if optional binary parsers are missing.

---

## Hybrid Multi-Tier Memory Store

AgentX implements a modular memory architecture configured via `MEMORY_BACKEND`:

| Backend | Implementation | Target Environment | Capabilities |
| :--- | :--- | :--- | :--- |
| **`memory`** | `InMemoryStore` | Local dev & unit tests | Fast, thread-safe in-process dictionary storage |
| **`faiss`** | `FAISSMemoryStore` | Semantic search / RAG | Flat L2 vector index using OpenAI embeddings for precedent retrieval |
| **`redis`** | `RedisMemoryStore` | High-throughput distributed | Distributed session persistence, JSON serialization, and configurable TTL |

---

## Production Security & LLM Guardrails

1. **Prompt Injection Neutralization**: All user document inputs pass through `LegalAgent._sanitize_input()`, which strips instruction-override delimiters (e.g., `IGNORE PREVIOUS INSTRUCTIONS`, system prompt hijack attempts).
2. **Output Sanitization**: Model completions are scrubbed before serialization to prevent downstream Cross-Site Scripting (XSS) or prompt leakage.
3. **No Information Leakage**: Global FastAPI exception handlers intercept unhandled errors and return sanitized generic responses; raw Python stack traces are never exposed to clients.
4. **Zero-Secret Codebase**: Configuration strictly managed via `pydantic-settings` reading from `.env` or system environment variables.
5. **Rate Limiting**: `SlowAPI` enforces per-minute rate limits to protect against denial-of-service and LLM API budget drain.

---

## User Interfaces

AgentX provides two complete, production-ready interfaces:

### Full-Featured Web Dashboard
A modern, responsive React 19 + Vite dashboard located in `frontend/`:
- **Real-Time Task Monitoring**: Live polling of running, completed, and failed tasks with status badges.
- **Document Drag-and-Drop**: Upload PDF, DOCX, TXT, or MD files directly with automatic format detection and text extraction preview.
- **Interactive Legal Report**: Formatted Markdown rendering of agent findings with risk level indicators (Low / Medium / High / Critical).
- **Agent Registry Viewer**: Inspect active agents, their system prompts, and memory states.
- **Execution Log Inspector**: Real-time trace logs detailing each agent's execution latency and token usage.

### Interactive Terminal CLI Demo
A standalone terminal interface located in `app/cli.py` for headless environments and quick evaluations:
```bash
python run.py --demo
# or
python -m app.cli
```
Features interactive menu navigation, sample contract analysis, document ingestion, and formatted terminal reports.

---

## Quick Start & Deployment

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Node.js 18+ (for frontend web dashboard)
- OpenAI API Key

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shrchrds/AgentX.git
   cd AgentX
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and configure your settings:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key
   OPENAI_MODEL=gpt-4
   MEMORY_BACKEND=memory
   LOG_LEVEL=INFO
   ```

### 1-Click Launchers

AgentX includes a unified runner (`run.py`) and a Windows batch script (`start.bat`):

```bash
# Launch both Backend API (port 8000) AND Frontend UI (port 5173) together
python run.py --all

# Launch Backend API server only
python run.py --server

# Launch Frontend UI only
python run.py --frontend

# Run interactive Terminal CLI demo
python run.py --demo

# Windows 1-Click:
start.bat
```

- **Backend API**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **Web Dashboard**: `http://localhost:5173`

### Docker & Docker Compose

Deploy the full stack (FastAPI Backend + Redis Vector/Session Cache):

```bash
docker-compose up --build
```

---

## API Documentation

Interactive OpenAPI documentation is automatically served at `http://localhost:8000/docs`.

### Primary Endpoints

| Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/tasks` | Submit a text-based legal query or document for analysis |
| `POST` | `/api/v1/tasks/upload` | Upload a PDF, DOCX, TXT, or MD document directly for multi-agent review |
| `POST` | `/api/v1/tasks/extract-text` | Parse and preview extracted text and metadata from an uploaded file |
| `GET` | `/api/v1/tasks` | List all submitted tasks and their statuses |
| `GET` | `/api/v1/tasks/{task_id}` | Retrieve comprehensive task results, risk score, and agent findings |
| `GET` | `/api/v1/agents` | List registered agents and active configurations |
| `POST` | `/api/v1/agents` | Dynamically register a new custom agent (hot-plugging) |
| `GET` | `/api/v1/logs/{task_id}` | Retrieve structured execution traces and audit logs |
| `GET` | `/health` | Liveness and readiness health probe |

### Example cURL Requests

#### 1. Analyze Legal Query (JSON)
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secret_key" \
  -d '{
    "input_data": "Review this clause: Employee agrees not to engage in any competitive business worldwide for 3 years post-termination."
  }'
```

#### 2. Upload Document Directly (PDF / DOCX / TXT)
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/upload" \
  -H "X-API-Key: your_secret_key" \
  -F "file=@employment_agreement.pdf"
```

---

## Testing & Quality Assurance

AgentX adheres to rigorous engineering and testing standards. All unit and integration tests are completely isolated from live external APIs via deterministic mocks.

```bash
# Run complete test suite
pytest

# Run with test coverage report
pytest --cov=app --cov-report=term-missing

# Run code style and linting checks
ruff check app tests
ruff format --check app tests
```

### Test Suite Summary
- **144 passing tests** across 19 test modules:
  - Agent behavior & prompt injection defenses (`tests/test_agents/`)
  - REST API routes & error handling (`tests/test_api/`)
  - End-to-end multi-agent orchestration (`tests/test_integration/`)
  - Memory backends (In-memory, FAISS, Redis) (`tests/test_memory/`)
  - Pydantic state models (`tests/test_models/`)
  - LangGraph workflow DAG & dynamic router (`tests/test_orchestrator/`)
  - Multi-format document parser & safety guards (`tests/test_utils/`)

---

## AI Engineer Portfolio Competencies

This repository demonstrates the core engineering skills expected of a Senior / Staff AI Engineer:

1. **Stateful Multi-Agent Orchestration**: Designing directed cyclic/acyclic state machines with LangGraph rather than naive chains, handling branching, fan-out, fan-in, and error states.
2. **Context & Memory Architecture**: Implementing real-world vector stores (FAISS) with cosine similarity and distributed cache layers (Redis) rather than transient variables.
3. **Production Data Ingestion**: Building robust parsers for messy, binary file formats (PDF, DOCX) with encoding fallback, file size enforcement, and memory safety.
4. **Defense-in-Depth LLM Security**: Mitigating prompt injection attacks, sanitizing model output, and enforcing strict Pydantic v2 schemas.
5. **Full-Stack Systems Engineering**: Delivering both a high-concurrency async backend (FastAPI) and an intuitive, modern frontend (React/Vite).
6. **Enterprise Test-Driven Development**: Maintaining a comprehensive, 100% passing test suite with zero live API dependencies.

---

## Project Structure

```
AgentX/
├── app/
│   ├── agents/                   # Specialized legal agent implementations
│   │   ├── base.py               # LegalAgent abstract base with injection defense
│   │   ├── contract_review.py    # Contract review specialist
│   │   ├── case_analysis.py      # Case law precedent specialist
│   │   ├── risk_analysis.py      # Liability & compliance risk specialist
│   │   ├── manager.py            # Agent registry & hot-plug lifecycle manager
│   │   └── types.py              # Agent domain enumerations
│   ├── api/                      # FastAPI web gateway
│   │   ├── dependencies.py       # Authentication & rate limiting
│   │   └── routes/               # Modular route handlers (tasks, agents, logs)
│   ├── core/                     # Core settings, security, and logging
│   │   ├── config.py             # Pydantic-settings configuration
│   │   ├── security.py           # API key validation
│   │   └── logging.py            # Structured logging configuration
│   ├── memory/                   # Pluggable memory architecture
│   │   ├── store.py              # Abstract MemoryStore interface
│   │   └── backends/             # In-memory, FAISS vector store, Redis
│   ├── models/                   # Pydantic v2 domain schemas
│   │   ├── agent.py              # Agent state & response models
│   │   ├── memory.py             # Memory record models
│   │   └── task.py               # Task request, response, and upload models
│   ├── orchestrator/             # LangGraph workflow engine
│   │   ├── graph.py              # LangGraph StateGraph DAG coordinator
│   │   ├── router.py             # Keyword & domain classifier
│   │   └── state.py              # Workflow state definitions
│   ├── utils/                    # Utility services
│   │   └── document_parser.py    # PDF, DOCX, TXT, MD ingestion engine
│   ├── cli.py                    # Interactive terminal CLI demo
│   └── main.py                   # FastAPI application entry point
├── frontend/                     # Modern React 19 + Vite web dashboard
│   ├── src/                      # UI components, dashboard, task management
│   └── package.json
├── tests/                        # Comprehensive test suite (144 tests)
│   ├── test_agents/
│   ├── test_api/
│   ├── test_integration/
│   ├── test_memory/
│   ├── test_models/
│   ├── test_orchestrator/
│   └── test_utils/
├── Docs/                         # Formal architectural design specifications
│   ├── PRD.pdf                   # Product Requirements Document
│   ├── HLD.pdf                   # High-Level Architecture Design
│   └── lld.pdf                   # Low-Level Component Design
├── .env.example                  # Environment configuration template
├── pyproject.toml                # Package definition & dependencies
├── Dockerfile                    # Containerization specification
├── docker-compose.yml            # Multi-service composition (App + Redis)
├── run.py                        # Unified cross-platform launcher
├── start.bat                     # Windows 1-click execution script
└── README.md                     # Framework documentation
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
