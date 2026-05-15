node Goal {
    has id: str;
    has title: str;
    has scenario: str;
    has status: str = "active";
    has created_at: str;
}

node Task {
    has id: str;
    has title: str;
    has order: int;
    has owner: str;
    has tool: str;
    has status: str = "pending";
    has notes: str = "";
}

node Memory {
    has id: str;
    has kind: str;
    has value: str;
    has created_at: str;
}

edge decomposes;
edge informs;
edge remembers;

walker GraphPlanner {
    has goal_text: str;
    has scenario: str;

    can plan with `root {
        report {"event":"planner_start","goal":self.goal_text,"scenario":self.scenario};
        report {"event":"planner_done","steps":4};
    }
}

walker Executor {
    has task_title: str;
    has tool: str;

    can execute with `root {
        report {"event":"executor_run","task":self.task_title,"tool":self.tool};
    }
}

walker MemoryTraverse {
    has objective: str;

    can update_memory with `root {
        report {"event":"memory_traverse","objective":self.objective};
    }
}
