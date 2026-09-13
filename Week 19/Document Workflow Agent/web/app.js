"use strict";
const $ = (id) => document.getElementById(id);
let samples = [];
async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
function text(tag, content, className = "") {
  const element = document.createElement(tag);
  element.textContent = content;
  element.className = className;
  return element;
}
function render(run) {
  $("empty").hidden = true;
  $("result").hidden = false;
  $("status").textContent = `${run.status} · ${run.provider}`;
  const result = run.result || {outputs: {}, tools_used: [], duration_ms: 0};
  const output = result.outputs;
  $("count").textContent = `${result.tools_used.length} / 8`;
  $("elapsed").textContent = `${(result.duration_ms / 1000).toFixed(2)} s`;
  $("goal").textContent = run.task;
  const next = output.recommend_next_action;
  $("action").textContent = next ? next.action.replaceAll("_", " ") : (run.status === "running" ? "Agent is working…" : "Task result available below");
  $("reason").textContent = next?.reason || result.error || result.stop_reason || "";
  $("tools").replaceChildren(...result.tools_used.map(name => text("span", name, "chip")));
  const findings = [];
  if (output.classify_document) findings.push(text("div", `Document type: ${output.classify_document.document_type}`, "finding"));
  if (output.detect_previous_revisions) findings.push(text("div", `Revision finding: ${output.detect_previous_revisions.status}`, "finding"));
  for (const comment of output.generate_review_comments?.comments || []) findings.push(text("div", `${comment.severity.toUpperCase()} · ${comment.comment}`, "finding"));
  for (const point of output.generate_summary?.points || []) findings.push(text("div", `Line ${point.line}: ${point.quote}`, "finding"));
  $("findings").replaceChildren(...findings);
  $("decisions").replaceChildren(...run.events.filter(e => e.kind === "decision").map(e => {
    const item = document.createElement("li");
    item.append(text("strong", e.tool), text("span", e.reason));
    return item;
  }));
  $("json").textContent = JSON.stringify(run, null, 2);
}
async function history() {
  const data = await api("/api/v1/runs");
  $("history").replaceChildren(...data.runs.map(run => {
    const row = text("div", "", "history-row");
    const button = text("button", run.filename);
    button.type = "button";
    button.addEventListener("click", async () => {
      try { render(await api(`/api/v1/runs/${run.id}`)); }
      catch (error) { $("message").textContent = error.message; }
    });
    row.append(button, text("span", run.task), text("span", run.status), text("span", new Date(run.created_at).toLocaleString()));
    return row;
  }));
  if (!data.runs.length) $("history").textContent = "No runs yet.";
}
$("form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("file").files[0];
  const sample = samples.find(item => item.filename === $("sample").value);
  $("message").className = "";
  if (!file && !sample) { $("message").textContent = "Choose a document or a training sample."; return; }
  $("submit").disabled = true;
  $("message").textContent = "Agent is processing the document…";
  let poll;
  try {
    poll = setInterval(() => history().catch(() => {}), 2000);
    const task = $("task").value, instruction = $("instruction").value;
    let run;
    if (file) {
      const query = new URLSearchParams({filename: file.name, task, instruction});
      run = await api(`/api/v1/runs?${query}`, {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: file});
    } else {
      run = await api("/api/v1/runs", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({...sample, task, instruction})});
    }
    render(run);
    $("message").textContent = `Run ${run.status}. Execution history saved.`;
    $("message").className = run.status === "completed" ? "good" : "error";
    await history();
  } catch (error) { $("message").textContent = error.message; $("message").className = "error"; }
  finally { clearInterval(poll); $("submit").disabled = false; }
});
$("sample").addEventListener("change", () => { $("file").value = ""; });
$("file").addEventListener("change", () => { $("sample").value = ""; });
$("refresh").addEventListener("click", () => history().catch(error => { $("message").textContent = error.message; }));
(async () => {
  try {
    const health = await api("/api/v1/health");
    $("provider").textContent = health.provider === "offline" ? "OFFLINE · policy demo" : `OPENAI · ${health.model}`;
    samples = (await api("/api/v1/samples")).samples;
    for (const sample of samples) { const option = text("option", sample.filename); option.value = sample.filename; $("sample").append(option); }
    await history();
  } catch (error) { $("provider").textContent = "Service unavailable"; $("message").textContent = error.message; }
})();
