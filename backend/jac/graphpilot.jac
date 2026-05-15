node Goal {
    has id: str;
    has title: str;
    has status: str = "active";
    has created_at: str;
}

node Task {
    has id: str;
    has title: str;
    has status: str = "pending";
    has owner: str = "planner";
    has notes: str = "";
}

node Memory {
    has id: str;
    has kind: str;
    has value: str;
    has created_at: str;
}

edge decomposes;
edge remembers;
edge informs;

walker GraphPlanner {
    has goal_text: str;
    has steps: list[str] = [];

    can create_goal with `root {
        report {"event": "planner_start", "goal": self.goal_text};
        self.steps = [
            "Clarify objective and constraints",
            "Gather supporting context with tools",
            "Synthesize findings into action plan",
            "Generate final summary with next actions"
        ];
        report {"event": "planner_steps", "steps": self.steps};
    }
}

walker MemoryTraverse {
    has query: str;

    can find_relevant with `root {
        report {"event": "memory_query", "query": self.query};
    }
}

walker Executor {
    has task_title: str;
    has tool: str;

    can run_task with `root {
        report {"event": "executor_run", "task": self.task_title, "tool": self.tool};
    }
}
