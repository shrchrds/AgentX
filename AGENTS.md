# AgentX — Multi-Agent Collaboration Framework

> An open-source, research-focused framework enabling dynamic collaboration among specialized AI agents to solve complex legal domain tasks.

---

## Project Overview

AgentX orchestrates specialized AI agents that collaboratively solve legal domain problems—contract review, case analysis, risk assessment—via dynamic, context-aware workflows. Built with **Python**, **FastAPI**, **Langchain**, **LangGraph**, and **OpenAI**.

### Goals

| Goal | Description |
|------|-------------|
| Multi-Agent Collaboration | Multiple specialized agents interact and solve legal tasks |
| Dynamic Orchestration | Context-aware, adaptive workflows via LangGraph |
| Agent Memory Integration | Persistent, queryable long/short-term memory |
| Open-Source & Extensible | Modular, research-friendly, plug-in architecture |
| API-Driven | All core functionality exposed via FastAPI endpoints |

---

## Architecture

```
[Client] <-> [FastAPI API Gateway] <-> [Orchestrator (LangGraph)] <-> [Agents (Langchain, OpenAI)]
                                                  |
                                           [Memory Store]
```

### Core Components

| Component | Technology | Responsibilities |
|-----------|-----------|-----------------|
| **API Layer** | FastAPI | Expose REST endpoints, receive tasks, return results |
| **Orchestrator** | LangGraph | Agent workflow management, task routing, state management |
| **Agent Manager** | Langchain | Instantiate/configure agents, maintain agent registry |
| **Specialized Agents** | Langchain + OpenAI | Execute domain-specific subtasks, maintain memory |
| **Memory Store** | In-memory / Vector DB (FAISS, Redis) | Persist agent context and conversation history |
| **Logging** | Python logging | Record interactions, errors, and workflow traces |

### Data Flow

```
Client → API Gateway → Orchestrator → Agent(s) → LLM (OpenAI)
                                        ↕
                                   Memory Store
```

1. Client submits a legal task via FastAPI endpoint
2. Orchestrator decomposes the task and assigns subtasks to specialized agents
3. Agents process subtasks, leveraging memory and LLM, and return results
4. Orchestrator aggregates agent outputs into a final response
5. API Gateway returns the response to the client

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| API Framework | FastAPI |
| Orchestration | LangGraph |
| Agent Framework | Langchain |
| LLM Provider | OpenAI API |
| Memory / Vector DB | FAISS / Redis (configurable) |
| Authentication | API key / token-based |

---

## Project Structure (Target)

```
agentx/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entrypoint
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── tasks.py         # POST /tasks, GET /tasks/{id}
│   │   │   ├── agents.py        # GET /agents, POST /agents
│   │   │   └── logs.py          # GET /logs/{task_id}
│   │   └── dependencies.py      # Auth, rate limiting, shared deps
│   ├── core/
│   │   ├── config.py            # Settings via env vars (no hardcoded secrets)
│   │   ├── security.py          # Auth, API key validation
│   │   └── logging.py           # Structured logging setup
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph workflow definitions
│   │   ├── router.py            # Dynamic task routing logic
│   │   └── state.py             # Workflow state management
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # LegalAgent base class
│   │   ├── manager.py           # AgentManager: registry, lifecycle
│   │   ├── contract_review.py   # ContractReviewAgent
│   │   ├── case_analysis.py     # CaseAnalysisAgent
│   │   └── risk_analysis.py     # RiskAnalysisAgent
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── store.py             # MemoryStore interface
│   │   └── backends/
│   │       ├── in_memory.py     # In-memory backend
│   │       ├── faiss_backend.py # FAISS vector store backend
│   │       └── redis_backend.py # Redis backend
│   └── models/
│       ├── __init__.py
│       ├── task.py              # TaskRequest, TaskResponse schemas
│       ├── agent.py             # AgentState, AgentResponse schemas
│       └── memory.py            # MemoryRecord schema
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_orchestrator/
│   ├── test_agents/
│   └── test_memory/
├── Docs/
│   ├── PRD.pdf
│   ├── HLD.pdf
│   └── lld.pdf
├── .env.example                 # Environment variable template (never .env with real secrets)
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Key Data Models

### TaskRequest
```python
class TaskRequest(BaseModel):
    task_id: str
    input_data: str           # The legal query / document
    metadata: dict = {}       # Optional context
```

### AgentState
```python
class AgentState(BaseModel):
    agent_id: str
    context: dict
    history: list
    status: str               # "pending" | "running" | "completed" | "failed"
```

### AgentResponse
```python
class AgentResponse(BaseModel):
    task_id: str
    output_data: str
    status: str
    errors: list[str] = []
```

### MemoryRecord
```python
class MemoryRecord(BaseModel):
    agent_id: str
    conversation_id: str
    data: dict
    timestamp: datetime
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks` | Submit a new legal task |
| `GET` | `/tasks/{id}` | Get task status and result |
| `GET` | `/agents` | List available agents |
| `POST` | `/agents` | Register a new agent |
| `GET` | `/logs/{task_id}` | Retrieve task execution logs |

---

## Core Classes & Relationships

```
APIServer → AgentOrchestrator → AgentManager → LegalAgent
                                                   ↕
                                              MemoryStore
```

| Class | Key Methods | Description |
|-------|-------------|-------------|
| `AgentOrchestrator` | `run_workflow()`, `route_task()` | Manages LangGraph workflow and task assignment |
| `AgentManager` | `register_agent()`, `get_agent()` | Agent registry and lifecycle management |
| `LegalAgent` (base) | `process_input()`, `memory` | Base class for all specialized legal agents |
| `MemoryStore` | `save_context()`, `load_context()` | Abstract interface for memory backends |
| `APIServer` | FastAPI route handlers | REST API surface |

---

## Orchestration Flow (Pseudocode)

```python
def run_workflow(task_request):
    state = initialize_state(task_request)
    while not state.is_complete():
        agent = select_next_agent(state)
        response = agent.process_input(state.context)
        state.update(response)
        MemoryStore.save_context(agent.id, state.context)
    return state.final_output()
```

---

## Coding Conventions

### General
- **Python 3.10+** with type hints on all function signatures.
- Use `pydantic` BaseModel for all request/response schemas.
- Follow PEP 8. Use a formatter (black) and linter (ruff/flake8).
- Keep functions focused and single-responsibility.
- Refactor repeated logic into shared utilities.

### Security (Mandatory)
- **Never** hardcode secrets, API keys, tokens, or credentials in source code.
- Use environment variables via `pydantic-settings` or `python-dotenv` for configuration.
- Validate and sanitize all user inputs (task queries, agent registration payloads).
- Enforce authentication on all API endpoints.
- Apply rate limiting to sensitive/expensive endpoints (especially LLM-calling routes).
- Do not return internal exception details to API consumers.
- Add prompt injection resistance in agent prompts.

### Error Handling
| Scenario | Strategy |
|----------|----------|
| Invalid API request | Return HTTP 400 with structured error message |
| Agent processing failure | Log error, update status, return fallback response |
| Memory store unavailable | Retry with backoff, else return error to orchestrator |
| OpenAI API failure | Exponential backoff, fallback response |
| Workflow timeout | Abort workflow, return partial results with warning |

### Testing
- Write tests for all agent logic, orchestrator routing, and API endpoints.
- Use `pytest` as the test framework.
- Mock external services (OpenAI, Redis) in tests — never call live APIs in test flows.
- Cover validation, failure, and edge cases.
- Keep tests deterministic, readable, and isolated.

### Logging
- Use structured logging (JSON format preferred).
- Log all agent interactions, workflow steps, and errors.
- **Never** log passwords, tokens, raw secrets, or sensitive user content.
- Include `task_id` and `agent_id` in log context for traceability.

---

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | Accept legal tasks via REST API |
| FR2 | Dynamically assign tasks to appropriate agents |
| FR3 | Agents access and update memory during task execution |
| FR4 | Support adding/removing agents without downtime (hot-plug) |
| FR5 | Provide endpoints for task status, results, and logs |
| FR6 | All agent interactions must be logged and traceable |
| FR7 | Handle concurrent task submissions |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | Response time < 5s for standard tasks (excluding LLM latency) |
| NFR2 | Modular and extensible architecture |
| NFR3 | Open-source, well-documented codebase |
| NFR4 | Data privacy and secure API endpoints |
| NFR5 | Support local and cloud deployment (Docker) |

---

## Milestones

| Milestone | Deliverable | Timeline |
|-----------|-------------|----------|
| Core Framework | API, Orchestrator, Agent base, Memory | Week 2 |
| Specialized Agents | Contract, Case, Risk Analysis agents | Week 4 |
| Dynamic Workflows | LangGraph integration, multi-agent flows | Week 6 |
| Logging & Extensibility | Logging, agent/plugin system | Week 7 |
| Documentation & Release | Open-source repo, usage docs | Week 8 |

---

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM API latency/cost | Caching, batching, local LLM fallback support |
| Legal data privacy | Secure storage, API authentication, input sanitization |
| Workflow complexity | Modular design, extensive testing, clear state management |

---

## Environment Variables (Reference)

```bash
# .env.example — copy to .env and fill in real values
OPENAI_API_KEY=            # OpenAI API key (required)
OPENAI_MODEL=gpt-4         # Default LLM model
MEMORY_BACKEND=faiss       # "memory" | "faiss" | "redis"
REDIS_URL=                 # Redis connection URL (if using Redis backend)
API_SECRET_KEY=            # Secret key for API auth
RATE_LIMIT_PER_MINUTE=60   # Rate limit for API endpoints
LOG_LEVEL=INFO             # Logging level
```

---

## Reference Documents

- [PRD.pdf](Docs/PRD.pdf) — Product Requirements & Specification
- [HLD.pdf](Docs/HLD.pdf) — High Level Design
- [lld.pdf](Docs/lld.pdf) — Low Level Design
