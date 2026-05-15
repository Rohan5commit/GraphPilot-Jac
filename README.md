# GraphPilot Jac

GraphPilot Jac is a Jac-first agentic workspace for turning real-world goals into executable graph plans with visible agent activity.

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

Visit: `http://localhost:8000`

## Core Product Flow
1. User enters a goal and scenario.
2. Graph planner creates Jac-style step sequence.
3. Tool-enabled executor runs 3 practical actions:
   - `memory_traverse`
   - `web_lookup`
   - `constraint_solver`
4. Memory walker writes goal/task/context nodes and edges.
5. Final synthesis agent returns action summary with next actions and risks.
6. UI renders activity timeline + graph state + final report.

## Demo Scenarios
See `scenarios/demo_scenarios.json` for seeded stable runs.

## Environment Variables
- `NIM_API_KEY`: NVIDIA NIM API key for live LLM synthesis.
- `VERCEL_TOKEN`: optional deployment token.
