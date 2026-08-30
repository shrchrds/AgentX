# AgentX

A multi-agent collaboration framework for legal domain tasks. AgentX orchestrates specialized AI agents (contract review, case analysis, risk analysis) that work together via LangGraph workflows to solve complex legal problems.

## Architecture Overview

AgentX uses a modular agent-based architecture with concurrent execution and flexible memory backends:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Request                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI API Gateway                           │
│                    (app/api/routes/)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AgentOrchestrator (LangGraph)                    │
│   ┌─────────────┬─────────────────┬──────────────────────┐     │
│   │  Classify   │  Execute Agents │  Aggregate/Error     │     │
│   │  (Router)   │  (Concurrent)   │  (Result Combiner)   │     │
│   └─────────────┴─────────────────┴──────────────────────┘     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AgentManager                                │
│               (Registry & Lifecycle Manager)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┬──────────────┬──────────────┐
    │  Contract    │  Case        │  Risk        │
    │  Review      │  Analysis    │  Analysis    │
    │  Agent       │  Agent       │  Agent       │
    └──────┬───────┴──────┬───────┴──────┬───────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  OpenAI LLM   │
                  └───────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ MemoryStore   │
                  │ (In-Memory,   │
                  │  FAISS, or    │
                  │  Redis)       │
                  └───────────────┘
```

### Key Components

- **AgentOrchestrator**: LangGraph StateGraph coordinator managing the workflow: `classify → execute_agents → aggregate/handle_error`
- **TaskRouter**: Keyword-based classifier mapping tasks to appropriate agent types
- **AgentManager**: Agent registry and lifecycle manager with hot-plug support
- **LegalAgent**: Abstract base class providing LLM integration, prompt injection resistance, and memory access
- **MemoryStore**: Pluggable memory backend (in-memory, FAISS vector store, or Redis)

## Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AgentX
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your configuration:
   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4
   MEMORY_BACKEND=memory
   LOG_LEVEL=INFO
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Docker Quick Start

```bash
# Build the image
docker build -t agentx .

# Run the container
docker run -p 8000:8000 --env-file .env agentx
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

- `POST /api/v1/tasks` — Submit a new task for agent processing
- `GET /api/v1/tasks/{task_id}` — Get task status and results
- `GET /api/v1/agents` — List registered agents
- `POST /api/v1/agents` — Register a new agent
- `GET /api/v1/logs/{task_id}` — Retrieve task execution logs

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Review this employment contract for potential risks",
    "context": {"contract_text": "..."}
  }'
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `MEMORY_BACKEND` | Memory backend (`memory`, `faiss`, `redis`) | `memory` |
| `REDIS_URL` | Redis connection string (if using redis backend) | - |
| `API_SECRET_KEY` | API authentication secret | - |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_api/test_tasks.py
```

### Run Specific Test

```bash
pytest tests/test_agents/test_base.py::TestLegalAgent::test_sanitize_output
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

Coverage report will be available at `htmlcov/index.html`

### Run Tests Verbosely

```bash
pytest -v
```

**Note**: All tests mock external services (OpenAI, Redis) and never call live APIs.

## Development

### Code Formatting

```bash
# Format code with black
black app tests
```

### Linting

```bash
# Check for linting issues
ruff check app tests

# Auto-fix linting issues
ruff check --fix app tests
```

### Project Conventions

- **Type hints required** on all function signatures
- **Pydantic models** for all request/response schemas
- **Structured logging**: Include `task_id` and `agent_id` in log context
- **Error handling**: Return HTTP 400 for invalid input, 500 for internal errors
- **Async throughout**: All I/O operations use async/await
- **Testing**: Mock external dependencies; cover validation, failure, and edge cases

## Project Structure

```
AgentX/
├── app/
│   ├── agents/           # Agent implementations
│   │   ├── base.py       # LegalAgent base class
│   │   ├── manager.py    # AgentManager registry
│   │   └── types.py      # Agent type enums
│   ├── api/              # FastAPI routes
│   │   ├── dependencies.py
│   │   └── routes/
│   ├── core/             # Core configurations
│   │   └── config.py     # Settings via pydantic-settings
│   ├── memory/           # Memory store implementations
│   │   └── store.py      # Abstract + concrete stores
│   ├── orchestrator/     # LangGraph workflow
│   │   ├── graph.py      # AgentOrchestrator
│   │   └── router.py     # TaskRouter
│   └── main.py           # FastAPI app entry point
├── tests/                # Test suite
├── Docs/                 # Design documents (PRD, HLD, LLD)
├── .env.example          # Example environment file
├── CLAUDE.md             # Claude Code project instructions
├── pyproject.toml        # Project dependencies
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the project conventions
4. Run tests and linting (`pytest && black app tests && ruff check app tests`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Maintain type hints on all functions
- Follow the existing code style
- Update documentation for user-facing changes
- Keep commits atomic and well-described

## Documentation

Detailed design documents are available in the `Docs/` directory:

- `PRD.pdf` — Product Requirements Document
- `HLD.pdf` — High Level Design
- `lld.pdf` — Low Level Design

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technology Stack

- **Framework**: FastAPI (async web framework)
- **Agent Orchestration**: LangGraph (workflow management)
- **LLM Integration**: LangChain + OpenAI API
- **Memory**: In-memory / FAISS / Redis (pluggable)
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: black (formatting) + ruff (linting)

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

---

**Built with ❤️ for intelligent legal document processing**
