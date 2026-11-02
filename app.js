const messages = document.getElementById("messages");
const stats = document.getElementById("stats");
const riskList = document.getElementById("riskList");
const threshold = document.getElementById("threshold");
const thresholdLabel = document.getElementById("thresholdLabel");
const form = document.getElementById("askForm");
const question = document.getElementById("question");

function addMessage(role, text, table) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  if (table && table.length) {
    bubble.appendChild(renderTable(table));
  }
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

function renderTable(rows) {
  const table = document.createElement("table");
  const headers = Object.keys(rows[0]);
  table.innerHTML = `
    <thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
    <tbody>
      ${rows
        .map(
          (row) =>
            `<tr>${headers.map((h) => `<td>${row[h]}</td>`).join("")}</tr>`
        )
        .join("")}
    </tbody>
  `;
  return table;
}

async function refresh() {
  const overview = await (await fetch("/api/overview")).json();
  stats.innerHTML = [
    ["Students", overview.students],
    ["Avg attendance", `${overview.average_pct}%`],
    ["Present", overview.present],
    ["Absent", overview.absent],
  ]
    .map(
      ([label, value]) =>
        `<div class="stat"><span>${label}</span><strong>${value}</strong></div>`
    )
    .join("");
  await refreshRisk();
}

async function refreshRisk() {
  const cut = Number(threshold.value);
  thresholdLabel.textContent = `${cut}%`;
  const data = await (await fetch(`/api/at-risk?threshold=${cut}`)).json();
  if (!data.students.length) {
    riskList.innerHTML = `<div class="empty">No students below ${cut}%.</div>`;
    return;
  }
  riskList.innerHTML = data.students
    .map(
      (s) =>
        `<div class="risk-item"><span>${s.Name} · ${s.Section}</span><b>${s["Attendance %"]}%</b></div>`
    )
    .join("");
}

async function ask(text) {
  addMessage("user", text);
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: text, threshold: Number(threshold.value) }),
  });
  const data = await res.json();
  addMessage("agent", data.text, data.table);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = question.value.trim();
  if (!text) return;
  question.value = "";
  ask(text);
});

document.querySelectorAll(".chips button").forEach((btn) => {
  btn.addEventListener("click", () => ask(btn.dataset.q));
});

threshold.addEventListener("input", refreshRisk);

document.getElementById("csv").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const body = new FormData();
  body.append("file", file);
  const res = await fetch("/api/upload", { method: "POST", body });
  const data = await res.json();
  if (!res.ok) {
    addMessage("agent", data.error || "Upload failed.");
    return;
  }
  addMessage("agent", `Loaded ${data.overview.records} records for ${data.overview.students} students.`);
  refresh();
});

document.getElementById("reset").addEventListener("click", async () => {
  await fetch("/api/reset", { method: "POST" });
  addMessage("agent", "Sample attendance data reloaded.");
  refresh();
});

addMessage(
  "agent",
  "I can answer questions about this class and list anyone below your attendance threshold. Sample data is already loaded."
);
refresh();
