const statusEl=document.getElementById('status');
const activityEl=document.getElementById('activity');
const graphEl=document.getElementById('graph');
const summaryEl=document.getElementById('summary');

document.getElementById('run').onclick=async()=>{
  const goal=document.getElementById('goal').value.trim();
  const scenario=document.getElementById('scenario').value;
  if(!goal){statusEl.textContent='Please enter a goal.';return;}
  statusEl.textContent='Running Jac agents...';
  try{
    const res=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal,scenario})});
    const data=await res.json();
    statusEl.textContent='Completed.';
    activityEl.textContent=JSON.stringify(data.activity,null,2);
    graphEl.textContent=JSON.stringify(data.graph,null,2);
    summaryEl.textContent=data.summary;
  }catch(e){statusEl.textContent='Error: '+e.message;}
};
