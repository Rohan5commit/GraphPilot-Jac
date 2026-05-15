const statusEl = document.getElementById('status');
const activityEl = document.getElementById('activity');
const graphEl = document.getElementById('graph');
const summaryEl = document.getElementById('summary');

function setStatus(text, cls='status') {
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

  setStatus('Running planner, tools, and memory walkers...', 'status loading');
  summaryEl.textContent = 'Generating...';
  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({goal, scenario})
    });
    if (!res.ok) throw new Error(`Request failed (${res.status})`);

    const data = await res.json();
    setStatus(`Complete: ${data.activity.stats.tasks_completed} tasks, ${data.activity.stats.memories_written} memories.`, 'status done');
    activityEl.textContent = JSON.stringify(data.activity, null, 2);
    graphEl.textContent = JSON.stringify(data.graph, null, 2);
    summaryEl.textContent = data.summary;
  } catch (err) {
    setStatus(`Error: ${err.message}`, 'status error');
    summaryEl.textContent = 'Execution failed. Check API health and retry.';
  }
};
