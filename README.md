# Code Review Agents 🤖

AI-powered code review system using multiple specialized agents orchestrated with LangGraph.

## Features

- **Multi-Agent Architecture**: Specialized agents for security, style, and summarization
- **Flexible LLM Backend**: Supports Ollama (local), Claude, and OpenAI
- **LangGraph Orchestration**: Coordinated workflow with parallel execution
- **FastAPI REST API**: Easy integration with any system
- **Kubernetes Ready**: Deployable to k3d/k8s with load balancing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Request                            │
│                    POST /review                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                             │
│                   (LangGraph)                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
┌───────────────────┐       ┌───────────────────┐
│ Security Reviewer │       │  Style Reviewer   │
│  (vulnerabilities)│       │ (best practices)  │
└─────────┬─────────┘       └─────────┬─────────┘
          │                           │
          └─────────────┬─────────────┘
                        │
                        ▼
          ┌───────────────────────────┐
          │       Summarizer          │
          │  (consolidate findings)   │
          └───────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Ollama (for local LLM) or API keys for Claude/OpenAI

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/code-review-agents.git
cd code-review-agents

# Copy environment file
cp .env.example .env

# Start the service
docker-compose up --build

# Test the API
curl http://localhost:8000/health
```

### Test Code Review

```bash
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def login(user, pwd):\n    query = f\"SELECT * FROM users WHERE user='{user}' AND pwd='{pwd}'\"\n    return db.execute(query)",
    "language": "python"
  }'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and version info |
| `/health` | GET | Health check for k8s probes |
| `/ready` | GET | Readiness check (verifies LLM) |
| `/review` | POST | Submit code for review |
| `/providers` | GET | List available LLM providers |

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM backend (ollama/claude/openai) | `ollama` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5-coder:7b` |
| `CLAUDE_API_KEY` | Anthropic API key | - |
| `CLAUDE_MODEL` | Claude model | `claude-sonnet-4-20250514` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | `gpt-4o-mini` |

## Kubernetes Deployment

```bash
# Build and push to local registry
docker build -t localhost:5000/code-review-agents:v1 .
docker push localhost:5000/code-review-agents:v1

# Deploy to k3d
kubectl apply -f k8s/
```

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## License

MIT
