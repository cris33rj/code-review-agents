# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Local Development
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
python -m http.server 3000 --directory frontend/
# Open http://localhost:3000 (backend must be running on port 8000)
```

The frontend is a single-file SPA (`frontend/index.html`) using CodeMirror 6 via CDN. No build step required.

### Docker
```bash
cp .env.example .env   # configure environment variables
docker-compose up --build
```

### Lint and Format
```bash
ruff check src/
black src/
```

### Tests
```bash
pytest tests/ -v
pytest tests/path/to/test_file.py -v   # single test file
```

### CI/CD (GitHub Actions, self-hosted runner)
- Trigger: push to `main`, PRs, manual dispatch
- Jobs: test → build (Docker image) → deploy (Kubernetes)
- Registry: `localhost:5000/code-review-agents`
- Kubernetes: `kubectl apply -k k8s/`

## Architecture

This is an **AI-powered code review API** built with FastAPI and LangGraph, supporting multiple LLM backends.

### Request Flow

```
POST /review
    → FastAPI (src/api/main.py)
    → Orchestrator (src/agents/orchestrator.py)
    → [Sequential or Parallel via LangGraph]
        ├─ SecurityReviewer (src/agents/security_reviewer.py)
        ├─ StyleReviewer (src/agents/style_reviewer.py)
        └─ Summarizer (src/agents/summarizer.py)
    → LLMGateway (src/llm/gateway.py)
    → Ollama | Claude | OpenAI
```

**Sequential mode** (`parallel=false`): Security → Style → Summarizer
**Parallel mode** (`parallel=true`): Security + Style concurrently → Summarizer

### LLM Provider Abstraction

`LLMGateway` selects a client based on the `LLM_PROVIDER` env var:
- `ollama` → `OllamaClient` (HTTP to local Ollama)
- `claude` → `ClaudeClient` (Anthropic async SDK)
- `openai` → `OpenAIClient` (OpenAI async SDK)

The provider can also be overridden per-request via the `provider` field in the request body.

### Key Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Active provider: `ollama`, `claude`, `openai` |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Ollama model |
| `CLAUDE_API_KEY` | — | Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `MAX_CODE_LENGTH` | `10000` | Max chars accepted per review |
| `REQUEST_TIMEOUT` | `120` | LLM request timeout (seconds) |

Configuration is loaded via `pydantic-settings` in [src/config.py](src/config.py).

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe (verifies LLM connectivity) |
| `/review` | POST | Submit code for review |
| `/providers` | GET | List configured providers |

### Kubernetes Deployment

Manifests in `k8s/` use Kustomize. Deployed to namespace `code-review`:
- 3 replicas by default, HPA scales 2–5 based on CPU (70%) / memory (80%)
- Ingress via Traefik at `codereview.localhost`
- Non-sensitive config in `k8s/configmap.yaml`; secrets go in `k8s/secrets.yaml` (not committed — use `k8s/secrets.yaml.example` as template)
