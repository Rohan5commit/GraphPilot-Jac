from pathlib import Path

from backend.services.engine import GraphPilotEngine


def test_run_goal_and_graph_snapshot(tmp_path: Path):
    engine = GraphPilotEngine(data_file=tmp_path / "graph.json")
    result = engine.run_goal("Plan a 14-day interview prep sprint", "planning")

    assert result["activity"]["stats"]["tasks_completed"] == 5
    assert len(result["tasks"]) == 5
    assert len(result["edges"]) > 0
    assert "Next 3 actions" in result["summary"]

    snapshot = engine.graph_snapshot(result["goal"]["id"])
    assert len(snapshot["goals"]) == 1
    assert len(snapshot["tasks"]) == 5
    assert len(snapshot["memories"]) >= 4


def test_deterministic_fallback_without_nim_key(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("NIM_API_KEY", raising=False)
    engine = GraphPilotEngine(data_file=tmp_path / "graph2.json")
    result = engine.run_goal("Build a simple fintech budget cadence", "fintech")
    assert "Outcome summary" in result["summary"]
