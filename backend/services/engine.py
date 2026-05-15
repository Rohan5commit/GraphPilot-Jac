from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import uuid
from typing import Any

import requests

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "graph_memory.json"
NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


@dataclass
class Goal:
    id: str
    title: str
    scenario: str
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
    order: int


@dataclass
class Memory:
    id: str
    goal_id: str
    kind: str
    value: str
    created_at: str


class GraphPilotEngine:
    """Jac-inspired agentic graph engine with deterministic tool pipeline."""

    def __init__(self) -> None:
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text())
        return {"goals": [], "tasks": [], "memories": [], "activity": [], "edges": []}

    def _save_state(self) -> None:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(self._state, indent=2))

    def run_goal(self, goal_text: str, scenario: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        goal = Goal(str(uuid.uuid4()), goal_text, scenario, "active", now)
        self._state["goals"].append(asdict(goal))

        planner = self._jac_planner(goal_text, scenario)
        tasks: list[dict[str, Any]] = []
        run_events = [{"type": "planner_start", "payload": planner}]

        for idx, step in enumerate(planner["steps"], start=1):
            tool = step["tool"]
            result = self._execute_tool(tool=tool, goal=goal_text, step_title=step["title"], scenario=scenario)
            task = Task(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                title=step["title"],
                status="done",
                owner=step["owner"],
                notes=result["summary"],
                tool=tool,
                order=idx,
            )
            task_obj = asdict(task)
            self._state["tasks"].append(task_obj)
            tasks.append(task_obj)
            run_events.append({"type": "task_complete", "payload": {"task": task.title, "tool": tool}})

        memories, edges = self._memory_traverse(goal, tasks, planner)
        self._state["memories"].extend(memories)
        self._state["edges"].extend(edges)

        final_summary = self._final_summary(goal_text, scenario, tasks, memories)
        run_events.append({"type": "final_summary", "payload": {"chars": len(final_summary)}})

        activity = {
            "goal_id": goal.id,
            "timestamp": now,
            "events": run_events,
            "stats": {
                "tasks_completed": len(tasks),
                "memories_written": len(memories),
                "edges_written": len(edges),
                "tools_used": sorted({t["tool"] for t in tasks}),
            },
        }
        self._state["activity"].append(activity)
        self._save_state()

        return {
            "goal": asdict(goal),
            "plan": planner,
            "tasks": tasks,
            "memories": memories,
            "edges": edges,
            "activity": activity,
            "summary": final_summary,
            "graph": self.graph_snapshot(goal.id),
        }

    def graph_snapshot(self, goal_id: str | None = None) -> dict[str, Any]:
        goals = self._state["goals"]
        tasks = self._state["tasks"]
        memories = self._state["memories"]
        edges = self._state["edges"]
        if goal_id:
            goals = [g for g in goals if g["id"] == goal_id]
            tasks = [t for t in tasks if t["goal_id"] == goal_id]
            memories = [m for m in memories if m["goal_id"] == goal_id]
            mem_ids = {m["id"] for m in memories}
            task_ids = {t["id"] for t in tasks}
            edge_ids = mem_ids | task_ids | {g["id"] for g in goals}
            edges = [e for e in edges if e["from"] in edge_ids and e["to"] in edge_ids]
        return {"goals": goals, "tasks": tasks, "memories": memories, "edges": edges, "activity": self._state["activity"][-12:]}

    def _jac_planner(self, goal_text: str, scenario: str) -> dict[str, Any]:
        objective = self._extract_objective(goal_text)
        base_tools = ["memory_traverse", "web_lookup", "constraint_solver", "llm_synthesis"]
        return {
            "walker": "GraphPlanner",
            "objective": objective,
            "scenario": scenario,
            "steps": [
                {"title": f"Define success criteria for {objective}", "tool": base_tools[0], "owner": "planner"},
                {"title": "Gather external context and evidence", "tool": base_tools[1], "owner": "researcher"},
                {"title": "Generate constraints-aware options", "tool": base_tools[2], "owner": "optimizer"},
                {"title": "Synthesize final execution memo", "tool": base_tools[3], "owner": "summarizer"},
            ],
        }

    def _execute_tool(self, tool: str, goal: str, step_title: str, scenario: str) -> dict[str, str]:
        if tool == "web_lookup":
            return self._tool_web_lookup(goal, scenario)
        if tool == "constraint_solver":
            return self._tool_constraint_solver(goal, scenario)
        if tool == "memory_traverse":
            return {"summary": f"Recovered related memories and constraints for '{goal}'."}
        return {"summary": f"Prepared synthesis context for '{step_title}'."}

    def _tool_web_lookup(self, goal: str, scenario: str) -> dict[str, str]:
        domain_hint = {
            "research": "industry reports",
            "planning": "calendar and effort estimates",
            "fintech": "budgeting and risk controls",
            "healthcare": "care coordination constraints",
        }.get(scenario, "relevant public information")
        return {"summary": f"Collected {domain_hint} to support: {goal}."}

    def _tool_constraint_solver(self, goal: str, scenario: str) -> dict[str, str]:
        constraints = {
            "research": "confidence, recency, and source diversity",
            "planning": "time blocks, deadlines, and energy windows",
            "fintech": "cashflow volatility, reserves, and spending caps",
            "healthcare": "safety, follow-up cadence, and accessibility",
        }.get(scenario, "resources, risk, and timeline")
        return {"summary": f"Generated ranked options balancing {constraints} for goal: {goal}."}

    def _memory_traverse(self, goal: Goal, tasks: list[dict[str, Any]], planner: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        now = datetime.now(timezone.utc).isoformat()
        memories = [
            asdict(Memory(str(uuid.uuid4()), goal.id, "goal", goal.title, now)),
            asdict(Memory(str(uuid.uuid4()), goal.id, "scenario", goal.scenario, now)),
            asdict(Memory(str(uuid.uuid4()), goal.id, "planner_objective", planner["objective"], now)),
        ]
        edges: list[dict[str, str]] = []
        for t in tasks:
            edges.append({"from": goal.id, "to": t["id"], "type": "decomposes"})
            for m in memories:
                edges.append({"from": t["id"], "to": m["id"], "type": "informs"})
        return memories, edges

    def _extract_objective(self, goal_text: str) -> str:
        cleaned = re.sub(r"\s+", " ", goal_text.strip())
        return cleaned[:120] if len(cleaned) > 120 else cleaned

    def _final_summary(self, goal_text: str, scenario: str, tasks: list[dict[str, Any]], memories: list[dict[str, Any]]) -> str:
        prompt = (
            "You are GraphPilot Jac's final synthesis agent. "
            "Return: 1) outcome summary, 2) next 3 actions, 3) risks.\n"
            f"Goal: {goal_text}\nScenario: {scenario}\n"
            f"Tasks: {json.dumps(tasks)}\nMemories: {json.dumps(memories)}"
        )
        api_key = os.getenv("NIM_API_KEY", "")
        if not api_key:
            return "Outcome: plan generated with 4 completed tasks. Next actions: execute top priority item, validate assumptions, and review metrics in 48 hours. Risks: stale inputs and changing constraints."
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
        except Exception:
            return "Outcome: resilient fallback summary created. Next actions: run execution checklist, gather fresh evidence, and rerank options against constraints. Risks: external API timeout and limited source breadth."
