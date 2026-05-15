# Architecture

## Jac Core
- `backend/jac/graphpilot.jac` defines graph schema and walkers.
- Node types: `Goal`, `Task`, `Memory`.
- Edge semantics: `decomposes`, `remembers`, `informs`.
- Walkers emit orchestration events to mirror planner/executor behavior.

## Runtime Flow
1. Frontend posts a goal to `POST /api/run`.
2. `GraphPilotEngine` creates goal/task/memory graph state.
3. Tool routing chooses `memory_traverse`, `web_lookup`, or `llm_synthesis`.
4. NVIDIA NIM LLM synthesizes final action summary.
5. Updated graph snapshot returns to UI and persists in JSON memory store.

## System Components
- **UI** (`app/*`): Landing + console + activity + graph viewer + result panel.
- **API** (`backend/main.py`): FastAPI endpoints for run + graph state.
- **Engine** (`backend/services/engine.py`): Agent orchestration, persistence, tool execution.
- **Jac Module** (`backend/jac/graphpilot.jac`): Native graph/agent semantics.
