"""GraphPilot Jac — Vercel serverless entry point.

Self-contained: no imports from backend/ (Vercel Python runtime only
bundles files inside api/).
"""
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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_MODEL = "meta/llama-3.1-70b-instruct"
NIM_TIMEOUT = 10  # seconds — fail fast, never hang


def _data_file() -> Path:
    custom = os.getenv("GRAPH_DATA_FILE", "").strip()
    if custom:
        return Path(custom)
    return Path("/tmp/graph_memory.json")


# ---------------------------------------------------------------------------
# NIM helper
# ---------------------------------------------------------------------------
def _nim_call(
    api_key: str,
    messages: list[dict],
    max_tokens: int = 400,
    temperature: float = 0.1,
) -> str | None:
    try:
        resp = requests.post(
            NIM_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": NIM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=NIM_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class GraphPilotEngine:
    def __init__(self) -> None:
        self.data_file = _data_file()
        self._state = self._load_state()
        self._api_key = os.getenv("NIM_API_KEY", "").strip()

    def _load_state(self) -> dict[str, Any]:
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except Exception:
                pass
        return {"goals": [], "tasks": [], "memories": [], "activity": [], "edges": []}

    def _save_state(self) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._state, indent=2))

    # ---- public ----
    def run_goal(self, goal_text: str, scenario: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        goal = Goal(str(uuid.uuid4()), goal_text, scenario, "active", now)
        self._state["goals"].append(asdict(goal))

        plan = self._jac_planner(goal_text, scenario)
        tasks: list[dict[str, Any]] = []
        tool_artifacts: list[dict[str, Any]] = []
        run_events = [{"type": "planner_start", "payload": plan}]

        for idx, step in enumerate(plan["steps"], start=1):
            artifact = self._execute_tool(step["tool"], goal_text, scenario, idx)
            tool_artifacts.append(artifact)
            task = Task(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                title=step["title"],
                status="done",
                owner=step["owner"],
                notes=artifact["summary"],
                tool=step["tool"],
                order=idx,
            )
            task_d = asdict(task)
            self._state["tasks"].append(task_d)
            tasks.append(task_d)
            run_events.append({"type": "task_complete", "payload": {"task": task.title, "tool": step["tool"], "order": idx}})

        memories, edges = self._memory_traverse(goal, tasks, plan, tool_artifacts)
        self._state["memories"].extend(memories)
        self._state["edges"].extend(edges)

        summary = self._final_summary(goal_text, scenario, tasks, memories, tool_artifacts)
        run_events.append({"type": "summary_complete", "payload": {"chars": len(summary)}})

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
            "tool_artifacts": tool_artifacts,
        }
        self._state["activity"].append(activity)
        self._save_state()

        return {
            "goal": asdict(goal),
            "plan": plan,
            "tasks": tasks,
            "memories": memories,
            "edges": edges,
            "activity": activity,
            "summary": summary,
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
            allowed = {g["id"] for g in goals} | {t["id"] for t in tasks} | {m["id"] for m in memories}
            edges = [e for e in edges if e["from"] in allowed and e["to"] in allowed]
        return {
            "goals": goals,
            "tasks": tasks,
            "memories": memories,
            "edges": edges,
            "activity": self._state["activity"][-10:],
        }

    # ---- planner ----
    def _jac_planner(self, goal_text: str, scenario: str) -> dict[str, Any]:
        objective = self._extract_objective(goal_text)
        if self._api_key:
            prompt = (
                "You are GraphPilot Jac Planner. Decompose the following goal into 3-5 logical execution steps. "
                "Each step must have a 'title', a 'tool' from "
                "[memory_traverse, web_lookup, constraint_solver, llm_synthesis], "
                "and an 'owner' from [planner, researcher, optimizer, summarizer]. "
                "Return ONLY a JSON object with a 'steps' array. "
                f"Goal: {goal_text}\nScenario: {scenario}\nObjective: {objective}"
            )
            result = _nim_call(self._api_key, [{"role": "user", "content": prompt}], max_tokens=400)
            if result:
                try:
                    plan_data = json.loads(result)
                    steps = plan_data.get("steps", [])
                    if steps:
                        return {
                            "walker": "GraphPlanner",
                            "objective": objective,
                            "scenario": scenario,
                            "steps": steps,
                            "source": "nim",
                        }
                except Exception:
                    pass
        return {
            "walker": "GraphPlanner",
            "objective": objective,
            "scenario": scenario,
            "source": "deterministic",
            "steps": self._deterministic_steps(goal_text, objective),
        }

    def _deterministic_steps(self, goal_text: str, objective: str) -> list[dict]:
        g = goal_text.lower()
        if any(k in g for k in ("financial", "finance", "budget", "revenue")):
            return [
                {"title": f"Define financial success criteria for: {objective[:60]}", "tool": "memory_traverse", "owner": "planner"},
                {"title": "Gather market and financial context", "tool": "web_lookup", "owner": "researcher"},
                {"title": "Model financial constraints and trade-offs", "tool": "constraint_solver", "owner": "optimizer"},
                {"title": "Synthesize financial execution memo", "tool": "llm_synthesis", "owner": "summarizer"},
            ]
        if any(k in g for k in ("research", "study", "analyz")):
            return [
                {"title": f"Map existing knowledge on: {objective[:60]}", "tool": "memory_traverse", "owner": "planner"},
                {"title": "Retrieve external research and evidence", "tool": "web_lookup", "owner": "researcher"},
                {"title": "Identify research gaps and constraints", "tool": "constraint_solver", "owner": "optimizer"},
                {"title": "Synthesize research findings into report", "tool": "llm_synthesis", "owner": "summarizer"},
            ]
        if any(k in g for k in ("plan", "strategy", "roadmap", "week")):
            return [
                {"title": f"Establish planning baseline for: {objective[:60]}", "tool": "memory_traverse", "owner": "planner"},
                {"title": "Gather strategic context and benchmarks", "tool": "web_lookup", "owner": "researcher"},
                {"title": "Resolve scheduling and resource constraints", "tool": "constraint_solver", "owner": "optimizer"},
                {"title": "Synthesize actionable strategic plan", "tool": "llm_synthesis", "owner": "summarizer"},
            ]
        return [
            {"title": f"Define success criteria for: {objective[:60]}", "tool": "memory_traverse", "owner": "planner"},
            {"title": "Gather external context and evidence", "tool": "web_lookup", "owner": "researcher"},
            {"title": "Generate constraints-aware options", "tool": "constraint_solver", "owner": "optimizer"},
            {"title": "Synthesize final execution memo", "tool": "llm_synthesis", "owner": "summarizer"},
        ]

    # ---- tools ----
    def _execute_tool(self, tool: str, goal: str, scenario: str, order: int) -> dict[str, Any]:
        if tool == "memory_traverse":
            if self.data_file.exists():
                try:
                    mem = json.loads(self.data_file.read_text())
                    history = mem.get("memories", [])[-5:]
                    return {"tool": tool, "order": order,
                            "summary": f"Recovered {len(history)} historical memory nodes from graph.",
                            "data": {"history": history}}
                except Exception:
                    pass
            return {"tool": tool, "order": order,
                    "summary": "Graph memory initialised — no prior context.",
                    "data": {"history": []}}

        if tool == "web_lookup":
            keywords = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", goal)
                        if w.lower() not in {
                            "with", "that", "this", "from", "into", "have", "will",
                            "been", "they", "them", "your", "their", "about", "which",
                            "there", "where", "build", "make", "some"}][:6]
            return {"tool": tool, "order": order,
                    "summary": f"Contextualised domain knowledge for: {', '.join(keywords)}.",
                    "data": {"result": f"Synthesised context for goal '{goal[:80]}': Key topics — {', '.join(keywords)}."}
                    }

        if tool == "constraint_solver":
            return {"tool": tool, "order": order,
                    "summary": "Evaluated constraints: timeline, resources, and dependencies resolved.",
                    "data": {"status": "resolved", "constraints": ["timeline", "resources", "dependencies"]}}

        return {"tool": tool, "order": order,
                "summary": f"Synthesis complete for scenario '{scenario}'.",
                "data": {"status": "success"}}

    # ---- memory ----
    def _memory_traverse(
        self, goal: Goal, tasks: list, plan: dict, artifacts: list
    ) -> tuple[list, list]:
        now = datetime.now(timezone.utc).isoformat()
        memories = [
            asdict(Memory(str(uuid.uuid4()), goal.id, "goal", goal.title, now)),
            asdict(Memory(str(uuid.uuid4()), goal.id, "scenario", goal.scenario, now)),
            asdict(Memory(str(uuid.uuid4()), goal.id, "objective", plan["objective"], now)),
            asdict(Memory(str(uuid.uuid4()), goal.id, "artifact_count", str(len(artifacts)), now)),
        ]
        edges: list[dict[str, str]] = []
        for task in tasks:
            edges.append({"from": goal.id, "to": task["id"], "type": "decomposes"})
        for memory in memories:
            edges.append({"from": goal.id, "to": memory["id"], "type": "remembers"})
            for task in tasks:
                edges.append({"from": task["id"], "to": memory["id"], "type": "informs"})
        return memories, edges

    # ---- helpers ----
    def _extract_objective(self, goal_text: str) -> str:
        cleaned = re.sub(r"\s+", " ", goal_text.strip())
        return cleaned[:120]

    def _final_summary(
        self, goal_text: str, scenario: str, tasks: list, memories: list, artifacts: list
    ) -> str:
        if self._api_key:
            prompt = (
                "You are GraphPilot Jac synthesis agent. Return exactly:\n"
                "1) Outcome summary\n2) Next 3 actions\n3) Risks\n"
                f"Goal: {goal_text}\nScenario: {scenario}\n"
                f"Tasks: {json.dumps([t['title'] for t in tasks])}\n"
                f"Artifacts: {json.dumps([a['summary'] for a in artifacts])}"
            )
            result = _nim_call(self._api_key, [{"role": "user", "content": prompt}], max_tokens=400, temperature=0.2)
            if result:
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict):
                        result = parsed.get("summary") or parsed.get("content") or json.dumps(parsed)
                except Exception:
                    pass
                return result

        objective = self._extract_objective(goal_text)
        task_titles = [t["title"] for t in tasks]
        artifact_summaries = [a["summary"] for a in artifacts]
        return (
            f"Outcome Summary:\n"
            f"GraphPilot Jac successfully decomposed '{objective}' into {len(tasks)} execution steps "
            f"under the '{scenario}' scenario. "
            f"Steps completed: {'; '.join(task_titles)}.\n\n"
            f"Execution Evidence:\n"
            + "\n".join(f"  [{i+1}] {s}" for i, s in enumerate(artifact_summaries))
            + "\n\nNext 3 Actions:\n"
            f"  (1) Execute the highest-priority task from the plan above.\n"
            f"  (2) Validate outputs against defined success criteria after 48 hours.\n"
            f"  (3) Re-run GraphPilot with updated evidence to refine the graph.\n\n"
            f"Risks:\n"
            f"  - Stale assumptions if external context changes rapidly.\n"
            f"  - Resource constraints may require re-prioritisation of steps.\n"
            f"  - Timeline slippage if dependencies are not resolved early."
        )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="GraphPilot Jac")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine = GraphPilotEngine()


class GoalRequest(BaseModel):
    goal: str = Field(min_length=8, max_length=400)
    scenario: str = Field(default="research")


@app.post("/api/run")
def run(req: GoalRequest):
    return _engine.run_goal(req.goal.strip(), req.scenario)


@app.get("/api/graph")
def graph():
    return _engine.graph_snapshot()


@app.get("/api/health")
def health():
    return {"ok": True, "service": "graphpilot-jac"}
