# GraphPilot Jac Architecture

## Jac-Centric Design
- Graph schema in `backend/jac/graphpilot.jac` defines `Goal`, `Task`, `Memory` nodes and semantic edges.
- Runtime mirrors Jac walkers through explicit planner/memory/executor phases in `GraphPilotEngine`.
- Graph state persists as node+edge memory for cross-run traversal and demo visibility.

## Runtime Pipeline
1. **Goal Intake** (`POST /api/run`) validates goal/scenario.
2. **Planner Walker Phase** builds decomposed multi-step plan.
3. **Executor Walker Phase** runs tool actions per task.
4. **Memory Traverse Phase** writes memory nodes and relationship edges.
5. **Synthesis Phase** returns final action memo via NIM or deterministic fallback.
6. **UI Projection** displays activity stats, event timeline, and graph snapshot.

## Tooling
- `memory_traverse`: recalls context and constraints.
- `web_lookup`: scenario-grounded external context gathering.
- `constraint_solver`: options under constraints.
- `llm_synthesis`: final report formatting and recommendations.
