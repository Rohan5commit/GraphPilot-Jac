# GraphPilot Jac (Final Submission)

GraphPilot Jac is a Jac-first agentic workspace that converts a user goal into a graph-modeled execution plan, runs tool-backed steps, persists graph memory, and returns a final action summary.

## Exact Repo Tree

```text
GraphPilot-Jac/
├── app/
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── backend/
│   ├── __init__.py
│   ├── data/graph_memory.json (runtime)
│   ├── jac/graphpilot.jac
│   ├── main.py
│   └── services/
│       ├── __init__.py
│       └── engine.py
├── docs/
│   ├── architecture.md
│   ├── demo-script.md
│   ├── jac-feature-notes.md
│   ├── optional-retrospective.md
│   ├── submission-checklist.md
│   └── submission-description.md
├── scenarios/demo_scenarios.json
├── tests/test_engine.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export $(cat .env | xargs)
uvicorn backend.main:app --reload --port 8000
```

Visit: http://localhost:8000

## Core Agent Flow
1. Goal intake (`POST /api/run`).
2. Jac-style planning decomposition (`GraphPlanner`).
3. Tool execution (`memory_traverse`, `web_lookup`, `constraint_solver`, `llm_synthesis`).
4. Graph memory updates (nodes + edges with relationship semantics).
5. Final synthesis and action summary.
6. UI projections for activity timeline, tool artifacts, graph state, and metrics.

## Tests
```bash
pytest -q
```

## Env vars
- `NIM_API_KEY` (optional): enables live NIM synthesis.
- `VERCEL_TOKEN` (optional): deployment token.
