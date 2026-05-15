# Submission Description

GraphPilot Jac is a Jac-first agentic workspace that transforms real-world goals into executable graph plans. It uses Jac graph modeling and walkers for orchestration while integrating tool execution and LLM summarization for practical outcomes.

## What we built
- A web app where users enter goals.
- A Jac-native graph memory layer storing goals, tasks, and memories.
- Agent workflow: planner -> executor -> synthesis.
- Scenario presets for research, personal planning, and fintech decisions.

## Hackathon track fit
Built for JacHacks Spring with Jac + Jaseci emphasized in runtime model and reasoning workflow.

## How it works
- User submits goal.
- System decomposes into tasks and records graph entities.
- Tool actions execute per task class.
- Final summary + graph/memory state displayed.
