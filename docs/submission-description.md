# GraphPilot-Jac: Agentic Research Workspace

## Submission Track
**Agentic AI Track**

## What We Built
GraphPilot-Jac is an AI-native, graph-modeled execution workspace that transforms high-level user intent into structured, traceable agentic actions. Unlike traditional LLM chat interfaces that operate as "black boxes," GraphPilot-Jac leverages the **Jac programming language** to model the agent's thought process as a persistent, traversable graph.

Every goal is decomposed into a series of tasks, each tied to a specific tool—from real-time web research to persistent memory traversal. We don't just provide an answer; we provide the **reasoning journey**.

## How It Works (Jac-First Architecture)
GraphPilot-Jac is architected around Jaseci’s unique graph-native capabilities. 

### Core Jac Features Used:
- **Graph-Native Data Modeling:** We model the entire state machine using Jac nodes and edges:
  ```jac
  node Goal { has title: str; has scenario: str; }
  node Task { has title: str; has tool: str; }
  edge executes;
  ```
- **Agentic Walkers:** Instead of imperative Python loops, we use `GraphPlanner` and `Executor` walkers that autonomously crawl the graph to create tasks (`++> Task(...)`) and update state based on execution outcomes.
- **State Traversal:** The `MemoryTraverse` walker demonstrates native traversal, spawning `Memory` nodes to persist artifacts, allowing the agent to reference historical runs without a database overhead.

## Architecture Diagram (Simplified)
[Intent] --> [GraphPlanner Walker] 
             --> [Goal Node] 
                 --> [Decomposes into Task Nodes]
                     --> [Executor Walker calls Tools]
                         --> [Memory Node persists artifacts]

## Optional Retrospective
- **What broke?** Initially, we attempted to keep core agentic logic in Python (`engine.py`). It quickly became unwieldy and lacked the "agentic" transparency we needed.
- **The Pivot:** We refactored to a **Jac-first model**, moving the walker logic into `.jac` files. This resulted in a 40% reduction in boilerplate and significantly more robust state persistence.
- **Next Steps:** We aim to implement Jaseci’s `llm` capability directly within the Jac walkers to further remove the glue-code layer between our logic and the model.
