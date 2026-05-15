# Jac / Jaseci Feature Notes

- Graph-native schema with `Goal`, `Task`, `Memory` nodes.
- Semantic relationship edges: `decomposes`, `remembers`, `informs`.
- Walker semantics for planning (`GraphPlanner`), execution (`Executor`), and memory updates (`MemoryTraverse`).
- Agent phases map directly to Jac concepts and are reflected in runtime activity events.
- Persistent memory graph enables stateful multi-run coordination and traversal-style reporting.
