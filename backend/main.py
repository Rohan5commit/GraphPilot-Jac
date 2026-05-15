from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services.engine import GraphPilotEngine

app = FastAPI(title="GraphPilot Jac")
engine = GraphPilotEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GoalRequest(BaseModel):
    goal: str = Field(min_length=8, max_length=400)
    scenario: str = Field(default="research")


@app.post("/api/run")
def run(req: GoalRequest):
    return engine.run_goal(req.goal.strip(), req.scenario)


@app.get("/api/graph")
def graph():
    return engine.graph_snapshot()


@app.get("/api/health")
def health():
    return {"ok": True, "service": "graphpilot-jac"}


app.mount("/app", StaticFiles(directory="app", html=True), name="app")


@app.get("/")
def root():
    return FileResponse("app/index.html")
