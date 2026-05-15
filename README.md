# GraphPilot Jac

GraphPilot Jac is an agentic research-and-action workspace built Jac-first: goals become graph nodes, walkers orchestrate planning/execution, and LLM synthesis generates final action summaries.

## Repo Tree

```text
GraphPilot-Jac/
├── app/
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── backend/
│   ├── data/graph_memory.json (created at runtime)
│   ├── jac/graphpilot.jac
│   ├── services/engine.py
│   └── main.py
├── docs/
│   ├── architecture.md
│   ├── demo-script.md
│   ├── jac-feature-notes.md
│   ├── optional-retrospective.md
│   ├── submission-checklist.md
│   └── submission-description.md
├── scenarios/demo_scenarios.json
├── .env.example
└── requirements.txt
```

## Quick Start

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and set `NIM_API_KEY`
4. `export $(cat .env | xargs)`
5. `uvicorn backend.main:app --reload --port 8000`
6. Open `http://localhost:8000`

## Jac-centric highlights
- Graph-native model in `backend/jac/graphpilot.jac` with `Goal`, `Task`, `Memory` nodes + semantic edges.
- Walkers: `GraphPlanner`, `MemoryTraverse`, `Executor` for planning, retrieval, and execution events.
- Persistent graph memory in `backend/data/graph_memory.json`.
- Agent orchestration and tool selection in backend service.

## Demo scenarios
Use seeded entries in `scenarios/demo_scenarios.json`.
