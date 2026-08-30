# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentX is a multi-agent collaboration framework for legal domain tasks. It orchestrates specialized AI agents (contract review, case analysis, risk analysis) that work together via LangGraph workflows to solve complex legal problems.

**Stack**: Python 3.10+, FastAPI, LangChain, LangGraph, OpenAI API

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies (including dev tools)
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and other settings
```

### Running the Application
```bash
# Start the FastAPI server with hot reload
uvicorn app.main:app --reload

# API documentation available at http://localhost:8000/docs
```

### Testing
```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_api/test_tasks.py

# Run a specific test
pytest tests/test_agents/test_base.py::TestLegalAgent::test_sanitize_output

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests verbosely
pytest -v
```

### Code Quality
```bash
# Format code with black
black app tests

# Lint with ruff
ruff check app tests

# Auto-fix linting issues
ruff check --fix app tests
```

## Architecture Overview

### Request Flow
```
Client → FastAPI API Gateway → AgentOrchestrator (LangGraph) → AgentManager → Specialized Agents → OpenAI LLM
                                                                     ↕
                                                                MemoryStore
```

### Key Components

**AgentOrchestrator** (`app/orchestrator/graph.py`): LangGraph StateGraph coordinator that manages the workflow: `classify → execute_agents → aggregate/handle_error`. Runs agents concurrently via `asyncio.gather()`. Handles timeouts (300s default) and error routing.

**TaskRouter** (`app/orchestrator/router.py`): Keyword-based classifier that maps task input to appropriate agent types. Falls back to routing to all agents if no keywords match.

**AgentManager** (`app/agents/manager.py`): Agent registry and lifecycle manager. Auto-registers one default agent of each type on startup. Supports hot-plug add/remove. Maps `AgentType` enum to concrete agent classes.

**LegalAgent** (`app/agents/base.py`): Abstract base class for all specialized agents. Provides:
- Lazy LLM initialization from settings
- Prompt injection resistance via `_build_system_prompt()`
- Output sanitization to strip leaked system prompts or control tokens
- Memory integration

**MemoryStore** (`app/memory/store.py`): Abstract interface for agent memory with three backends:
- `InMemoryStore`: Dict-based, non-persistent
- `FAISSMemoryStore`: FAISS vector store for semantic search
- `RedisMemoryStore`: Redis-backed persistent store

Backend selection via `MEMORY_BACKEND` env var (`memory` | `faiss` | `redis`).

**API Routes** (`app/api/routes/`):
- `/api/v1/tasks` — Submit tasks, query status
- `/api/v1/agents` — List/register agents
- `/api/v1/logs` — Retrieve task execution logs

### Application Lifecycle

The FastAPI `lifespan` context manager (`app/main.py`) initializes shared state on startup:
1. Sets up structured logging
2. Creates the memory store (from `settings.memory_backend`)
3. Initializes `AgentManager` (auto-registers default agents)
4. Initializes `AgentOrchestrator`
5. Creates in-memory `task_store` and `log_store` dicts

These are stored in `app.state` and accessed via dependency injection (`app/api/dependencies.py`).

### Configuration

All settings loaded via `pydantic-settings` from environment variables or `.env` file (`app/core/config.py`):

- `OPENAI_API_KEY` — Required for LLM calls
- `OPENAI_MODEL` — Default: `gpt-4`
- `MEMORY_BACKEND` — `memory` | `faiss` | `redis` (default: `memory`)
- `REDIS_URL` — Redis connection string (if using redis backend)
- `API_SECRET_KEY` — For API authentication
- `RATE_LIMIT_PER_MINUTE` — Default: 60
- `LOG_LEVEL` — Default: `INFO`

**Security**: Never hardcode secrets. All sensitive values must come from environment variables.

### Testing Patterns

- All tests use `pytest` with `pytest-asyncio` for async support
- External services (OpenAI, Redis) are mocked—tests never call live APIs
- FastAPI test client uses `ASGITransport` for in-process requests
- Agent tests mock the LLM via `langchain_core.language_models.FakeListChatModel`

**Known Issue**: Some API tests fail because test fixtures don't initialize `app.state` properly. When writing API tests, ensure the test setup initializes `app.state.agent_manager`, `app.state.orchestrator`, `app.state.task_store`, and `app.state.log_store`.

### Agent Execution Model

1. **Classify**: TaskRouter analyzes input keywords to select agent types
2. **Execute**: All selected agents run concurrently (`asyncio.gather`)
3. **Aggregate**: Successful outputs are combined into markdown sections
4. **Error Handling**: If all agents fail → `handle_error` node; partial failures → warnings in aggregate

Agents save/load context via their `MemoryStore` instance using `task_id` as `conversation_id`.

## Project Conventions

- **Type hints required** on all function signatures
- **Pydantic models** for all request/response schemas
- **Structured logging**: Include `task_id` and `agent_id` in log context for traceability
- **Error handling**: API returns HTTP 400 for invalid input, 500 for internal errors. Never expose internal exception details to clients
- **Async throughout**: All I/O operations (LLM calls, memory access) use async/await
- **Testing**: Mock external dependencies; cover validation, failure, and edge cases

## Reference Documents

See `Docs/` directory for detailed specifications:
- `PRD.pdf` — Product Requirements
- `HLD.pdf` — High Level Design
- `lld.pdf` — Low Level Design
