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

function renderGraph(graphData) {
  const container = document.getElementById('graph-viz');
  const nodes = new vis.DataSet();
  const edges = new vis.DataSet();
  const network = new vis.Network(container, { nodes, edges }, {
    physics: { enabled: true, stabilization: { iterations: 100 } },
    nodes: { borderWidth: 2 },
    edges: { smooth: { type: 'cubicBezier' } }
  });

  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  (async () => {
    // Add Goals
    for (const g of graphData.goals) {
      nodes.add({ id: g.id, label: `Goal: ${g.title}`, color: '#2f7af8', font: { color: '#fff' }, shape: 'ellipse' });
      await sleep(500);
    }
    // Add Tasks
    for (const t of graphData.tasks) {
      nodes.add({ id: t.id, label: `Task: ${t.title}`, color: '#35c27a', font: { color: '#fff' }, shape: 'box' });
      await sleep(500);
    }
    // Add Memories
    for (const m of graphData.memories) {
      nodes.add({ id: m.id, label: `Mem: ${m.value}`, color: '#facc15', font: { color: '#000' }, shape: 'dot', size: 10 });
      await sleep(500);
    }
    // Add Edges
    for (const e of graphData.edges) {
      edges.add({ from: e.from, to: e.to, label: e.type, arrows: 'to', font: { size: 10, color: '#9fb0cc' }, color: '#2b3a55' });
      await sleep(300);
    }
  })();
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
    artifactsEl.textContent = JSON.stringify(data.activity.tool_artifacts, null, 2);
    metricsEl.textContent = JSON.stringify(metrics, null, 2);
    summaryEl.textContent = data.summary;
    renderGraph(data.graph);
  } catch (err) {
    setStatus(`Error: ${err.message}`, 'status error');
    summaryEl.textContent = 'Execution failed. Check API health and retry.';
  }
};
