from __future__ import annotations


OPERATIONAL_STYLES = """
<style id="opscore-operational-styles">
.operations-overview { margin-bottom: 1rem; }
.operations-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.operations-heading h2 { margin-bottom: .25rem; }
.operations-heading p { margin: 0; }
.ops-eyebrow {
  margin: 0 0 .35rem !important;
  color: var(--ops-blue-700);
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.ops-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: .8rem;
  margin: 1.25rem 0;
}
.ops-metrics article {
  min-height: 6rem;
  padding: 1rem;
  border: 1px solid var(--ops-slate-200);
  border-radius: .7rem;
  background: var(--ops-slate-050);
}
.ops-metrics span {
  display: block;
  color: var(--ops-slate-600);
  font-size: .72rem;
  font-weight: 750;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.ops-metrics strong {
  display: block;
  margin-top: .45rem;
  color: var(--ops-slate-950);
  font-size: 1.8rem;
  line-height: 1;
}
.register-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: .75rem;
}
.register-toolbar label {
  width: min(100%, 28rem);
  color: var(--ops-slate-700);
  font-size: .76rem;
  font-weight: 750;
}
.incident-register-wrap {
  overflow-x: auto;
  border: 1px solid var(--ops-slate-200);
  border-radius: .7rem;
}
.incident-register {
  width: 100%;
  border-collapse: collapse;
  background: var(--ops-white);
  font-size: .82rem;
}
.incident-register th,
.incident-register td {
  padding: .75rem .85rem;
  border-bottom: 1px solid var(--ops-slate-200);
  text-align: left;
  vertical-align: middle;
}
.incident-register th {
  background: var(--ops-slate-050);
  color: var(--ops-slate-600);
  font-size: .68rem;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.incident-register tr:last-child td { border-bottom: 0; }
.incident-register code { color: var(--ops-slate-600); font-size: .75rem; }
.incident-register button { width: auto; margin: 0; padding: .45rem .7rem; }
.ops-badge {
  display: inline-flex;
  align-items: center;
  padding: .25rem .5rem;
  border-radius: 999px;
  font-size: .7rem;
  font-weight: 750;
  text-transform: capitalize;
}
.badge-danger { background: var(--ops-danger-100); color: var(--ops-danger-700); }
.badge-warning { background: var(--ops-warning-100); color: var(--ops-warning-700); }
.badge-success { background: var(--ops-success-100); color: var(--ops-success-700); }
.badge-neutral { background: var(--ops-slate-100); color: var(--ops-slate-700); }
@media (max-width: 1000px) {
  .ops-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 600px) {
  .operations-heading { display: block; }
  .operations-heading button { width: 100%; }
  .ops-metrics { grid-template-columns: 1fr; }
}
</style>
"""

OPERATIONAL_OVERVIEW = """
<section id="operations-overview" class="operations-overview card">
  <div class="operations-heading">
    <div>
      <p class="ops-eyebrow">Operational overview</p>
      <h2>Incident workload</h2>
      <p class="muted">
        Persisted incidents only. Metrics refresh from the local OPSCORE workspace.
      </p>
    </div>
    <button id="refresh-overview" class="secondary">Refresh overview</button>
  </div>
  <div class="ops-metrics" aria-label="Incident workload metrics">
    <article><span>Total incidents</span><strong id="metric-total">0</strong></article>
    <article><span>Critical / high</span><strong id="metric-priority">0</strong></article>
    <article><span>Active</span><strong id="metric-active">0</strong></article>
    <article><span>Root cause confirmed</span><strong id="metric-confirmed">0</strong></article>
  </div>
  <div class="register-toolbar">
    <label>
      Search incident register
      <input id="incident-search" placeholder="ID, title, environment, status or severity">
    </label>
  </div>
  <div class="incident-register-wrap">
    <table class="incident-register">
      <thead>
        <tr>
          <th>Incident</th>
          <th>Environment</th>
          <th>Severity</th>
          <th>Status</th>
          <th>Root cause</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="incident-register-body">
        <tr><td colspan="6" class="muted">No incidents loaded.</td></tr>
      </tbody>
    </table>
  </div>
</section>
"""

OPERATIONAL_SCRIPT = """
<script>
  let overviewIncidents = [];
  const badgeClass = (value) => {
    const normalized = String(value).toLowerCase();
    if (["critical", "confirmed"].includes(normalized)) return "badge-danger";
    if (["high", "suspected", "supported"].includes(normalized)) return "badge-warning";
    if (["resolved", "closed"].includes(normalized)) return "badge-success";
    return "badge-neutral";
  };
  const renderRegister = () => {
    const query = document.getElementById("incident-search").value
      .trim().toLowerCase();
    const visible = overviewIncidents.filter((incident) => [
      incident.incident_id,
      incident.title,
      incident.environment,
      incident.severity,
      incident.status,
      incident.root_cause_status,
    ].some((value) => String(value).toLowerCase().includes(query)));
    const body = document.getElementById("incident-register-body");
    body.innerHTML = visible.length ? visible.map((incident) => `
      <tr>
        <td><strong>${escapeHtml(incident.title)}</strong><br>
          <code>${escapeHtml(incident.incident_id)}</code></td>
        <td>${escapeHtml(incident.environment)}</td>
        <td><span class="ops-badge ${badgeClass(incident.severity)}">
          ${escapeHtml(incident.severity)}</span></td>
        <td><span class="ops-badge ${badgeClass(incident.status)}">
          ${escapeHtml(incident.status)}</span></td>
        <td><span class="ops-badge ${badgeClass(incident.root_cause_status)}">
          ${escapeHtml(incident.root_cause_status)}</span></td>
        <td><button class="secondary register-open"
          data-id="${escapeHtml(incident.incident_id)}">Open</button></td>
      </tr>`).join("") :
      "<tr><td colspan='6' class='muted'>No incidents match the search.</td></tr>";
    document.querySelectorAll(".register-open").forEach((button) => {
      button.addEventListener("click", async () => {
        await loadIncident(button.dataset.id);
        document.getElementById("workspace").scrollIntoView({behavior: "smooth"});
      });
    });
  };
  const refreshOperationalOverview = async () => {
    overviewIncidents = await request("/api/incidents");
    document.getElementById("metric-total").textContent = overviewIncidents.length;
    document.getElementById("metric-priority").textContent = overviewIncidents
      .filter((item) => ["critical", "high"].includes(item.severity)).length;
    document.getElementById("metric-active").textContent = overviewIncidents
      .filter((item) => !["resolved", "closed"].includes(item.status)).length;
    document.getElementById("metric-confirmed").textContent = overviewIncidents
      .filter((item) => item.root_cause_status === "confirmed").length;
    renderRegister();
  };
  document.getElementById("incident-search")
    .addEventListener("input", renderRegister);
  document.getElementById("refresh-overview")
    .addEventListener("click", refreshOperationalOverview);
  refreshOperationalOverview().catch(() => {
    document.getElementById("incident-register-body").innerHTML =
      "<tr><td colspan='6' class='muted'>Overview could not be loaded.</td></tr>";
  });
</script>
"""


def add_operational_overview(html: str) -> str:
    """Insert a data-backed operational dashboard without changing API behavior."""
    with_styles = html.replace("</head>", f"{OPERATIONAL_STYLES}</head>")
    with_overview = with_styles.replace(
        '<div id="empty-state" class="card">',
        f'{OPERATIONAL_OVERVIEW}<div id="empty-state" class="card">',
    )
    return with_overview.replace("</body>", f"{OPERATIONAL_SCRIPT}</body>")
