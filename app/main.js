const statusEl = document.getElementById('status');
const activityEl = document.getElementById('activity');
const graphEl = document.getElementById('graph');
const summaryEl = document.getElementById('summary');
const artifactsEl = document.getElementById('artifacts');
const metricsEl = document.getElementById('metrics');

function setStatus(text, cls = 'status') {
  statusEl.className = cls;
  statusEl.textContent = text;
}

document.getElementById('run').onclick = async () => {
  const goal = document.getElementById('goal').value.trim();
  const scenario = document.getElementById('scenario').value;
  if (goal.length < 8) {
    setStatus('Goal must be at least 8 characters.', 'status error');
    return;
  }

  setStatus('Running planner → tools → memory traversal → synthesis...', 'status loading');
  summaryEl.textContent = 'Generating final summary...';

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({goal, scenario})
    });
    if (!res.ok) throw new Error(`Request failed (${res.status})`);

    const data = await res.json();
    const metrics = {
      goals: data.graph.goals.length,
      tasks: data.graph.tasks.length,
      memories: data.graph.memories.length,
      edges: data.graph.edges.length,
      tools_used: data.activity.stats.tools_used,
    };

    setStatus(`Done: ${data.activity.stats.tasks_completed} tasks completed.`, 'status done');
    activityEl.textContent = JSON.stringify(data.activity.events, null, 2);
    graphEl.textContent = JSON.stringify(data.graph, null, 2);
    artifactsEl.textContent = JSON.stringify(data.activity.tool_artifacts, null, 2);
    metricsEl.textContent = JSON.stringify(metrics, null, 2);
    summaryEl.textContent = data.summary;
  } catch (err) {
    setStatus(`Error: ${err.message}`, 'status error');
    summaryEl.textContent = 'Execution failed. Check API health and retry.';
  }
};
