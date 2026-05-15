from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid
from typing import Any

import requests

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "graph_memory.json"
NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


@dataclass
class Goal:
    id: str
    title: str
    status: str
    created_at: str


@dataclass
class Task:
    id: str
    goal_id: str
    title: str
    status: str
    owner: str
    notes: str
    tool: str


@dataclass
class Memory:
    id: str
    goal_id: str
    kind: str
    value: str
    created_at: str


class GraphPilotEngine:
    def __init__(self) -> None:
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text())
        return {"goals": [], "tasks": [], "memories": [], "activity": []}

    def _save_state(self) -> None:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self._state, indent=2))

    def run_goal(self, goal_text: str, scenario: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        goal = Goal(id=str(uuid.uuid4()), title=goal_text, status="active", created_at=now)
        self._state["goals"].append(asdict(goal))

        steps = self._plan_steps(goal_text, scenario)
        tasks = []
        for step in steps:
            tool = self._select_tool(step)
            t = Task(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                title=step,
                status="done",
                owner="jac_executor",
                notes=f"Executed with {tool}",
                tool=tool,
            )
            tasks.append(asdict(t))
            self._state["tasks"].append(asdict(t))

        memories = self._build_memories(goal.id, goal_text, scenario)
        self._state["memories"].extend(memories)

        summary = self._final_summary(goal_text, scenario, tasks, memories)
        activity = {
            "goal_id": goal.id,
            "timestamp": now,
            "events": [
                {"type": "planner_start", "goal": goal_text},
                {"type": "planner_steps", "count": len(steps)},
                {"type": "tool_execution", "tools": sorted({t['tool'] for t in tasks})},
                {"type": "summary_complete"},
            ],
        }
        self._state["activity"].append(activity)
        self._save_state()

        return {
            "goal": asdict(goal),
            "tasks": tasks,
            "memories": memories,
            "activity": activity,
            "summary": summary,
            "graph": self.graph_snapshot(goal.id),
        }

    def graph_snapshot(self, goal_id: str | None = None) -> dict[str, Any]:
        goals = self._state["goals"]
        tasks = self._state["tasks"]
        memories = self._state["memories"]
        if goal_id:
            goals = [g for g in goals if g["id"] == goal_id]
            tasks = [t for t in tasks if t["goal_id"] == goal_id]
            memories = [m for m in memories if m["goal_id"] == goal_id]
        return {"goals": goals, "tasks": tasks, "memories": memories, "activity": self._state["activity"][-10:]}

    def _plan_steps(self, goal_text: str, scenario: str) -> list[str]:
        base = [
            f"Define success criteria for: {goal_text}",
            "Collect contextual information from tools",
            "Create prioritized execution plan",
            "Generate final recommendation and risks",
        ]
        if scenario == "fintech":
            base[1] = "Collect market/news context and budget constraints"
        elif scenario == "healthcare":
            base[1] = "Collect care constraints, schedules, and support resources"
        return base

    def _select_tool(self, step: str) -> str:
        if "Collect" in step:
            return "web_lookup"
        if "Define" in step:
            return "memory_traverse"
        return "llm_synthesis"

    def _build_memories(self, goal_id: str, goal_text: str, scenario: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        mems = [
            Memory(str(uuid.uuid4()), goal_id, "goal", goal_text, now),
            Memory(str(uuid.uuid4()), goal_id, "scenario", scenario, now),
        ]
        return [asdict(m) for m in mems]

    def _final_summary(self, goal_text: str, scenario: str, tasks: list[dict[str, Any]], memories: list[dict[str, Any]]) -> str:
        api_key = os.getenv("NIM_API_KEY", "")
        prompt = f"Goal: {goal_text}\nScenario: {scenario}\nTasks: {tasks}\nMemories: {memories}\nProvide concise action summary with next 3 steps."
        if not api_key:
            return "NIM API key missing. Generated local fallback summary: prioritize task execution, validate assumptions, and track outcomes in graph memory."
        try:
            response = requests.post(
                NIM_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "meta/llama-3.1-70b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 350,
                },
                timeout=25,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            return f"NIM call failed ({exc}). Local fallback: execute top priority task, capture findings, then iterate through graph-linked subtasks."
