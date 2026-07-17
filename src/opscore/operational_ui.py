from __future__ import annotations


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
    with_overview = html.replace(
        '<div id="empty-state" class="card">',
        f'{OPERATIONAL_OVERVIEW}<div id="empty-state" class="card">',
    )
    return with_overview.replace("</body>", f"{OPERATIONAL_SCRIPT}</body>")
