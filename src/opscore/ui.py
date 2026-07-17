from __future__ import annotations

from textwrap import dedent


def render_operator_interface() -> str:
    return dedent(
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>OPSCORE Operator Workbench</title>
          <style>
            :root {
              color-scheme: dark;
              font-family: Inter, system-ui, sans-serif;
            }
            body {
              margin: 0;
              background: #0b1020;
              color: #e7edf7;
            }
            header {
              padding: 24px 32px;
              border-bottom: 1px solid #26314d;
            }
            header p, .muted { color: #9fb0cf; }
            main {
              display: grid;
              grid-template-columns: 320px 1fr;
              min-height: 88vh;
            }
            aside, section { padding: 24px; }
            aside {
              border-right: 1px solid #26314d;
              background: #10172a;
            }
            button, input, select, textarea {
              width: 100%;
              box-sizing: border-box;
              margin: 6px 0 12px;
              padding: 10px;
              border: 1px solid #34415f;
              border-radius: 8px;
              background: #151f36;
              color: #e7edf7;
            }
            button {
              cursor: pointer;
              background: #275dad;
              font-weight: 700;
            }
            button.secondary { background: #1c2945; }
            .incident {
              padding: 12px;
              margin: 8px 0;
              border: 1px solid #34415f;
              border-radius: 8px;
              cursor: pointer;
            }
            .incident:hover { border-color: #72a7ff; }
            .grid {
              display: grid;
              grid-template-columns: repeat(2, minmax(0, 1fr));
              gap: 16px;
            }
            .card {
              padding: 18px;
              border: 1px solid #26314d;
              border-radius: 12px;
              background: #111a2f;
            }
            .wide { grid-column: 1 / -1; }
            .critical { color: #ff8b8b; }
            .warning { color: #ffd27d; }
            ul { padding-left: 20px; }
            pre {
              white-space: pre-wrap;
              overflow-wrap: anywhere;
            }
            @media (max-width: 850px) {
              main { grid-template-columns: 1fr; }
              aside {
                border-right: 0;
                border-bottom: 1px solid #26314d;
              }
              .grid { grid-template-columns: 1fr; }
            }
          </style>
        </head>
        <body>
          <header>
            <h1>OPSCORE Operator Workbench</h1>
            <p>
              Local-first incident evidence, deterministic findings,
              immutable history, and safe next checks.
            </p>
          </header>
          <main>
            <aside>
              <h2>Incidents</h2>
              <button id="refresh">Refresh incidents</button>
              <div id="incident-list" class="muted">No incidents loaded.</div>
              <hr>
              <h2>New incident</h2>
              <form id="incident-form">
                <label>
                  Incident ID
                  <input id="incident-id" required value="inc-new-001">
                </label>
                <label>
                  Title
                  <input id="title" required value="Service unavailable">
                </label>
                <label>
                  Symptom
                  <textarea id="symptom" required>
Users cannot reach the service.</textarea>
                </label>
                <label>
                  Environment
                  <input id="environment" required value="sample">
                </label>
                <label>
                  Severity
                  <select id="severity">
                    <option>critical</option>
                    <option selected>high</option>
                    <option>medium</option>
                    <option>low</option>
                  </select>
                </label>
                <label>
                  Service ID
                  <input id="service-id" required value="service-web">
                </label>
                <label>
                  Service name
                  <input id="service-name" required value="Web service">
                </label>
                <button type="submit">Create incident</button>
              </form>
              <div id="form-status" class="muted"></div>
            </aside>
            <section>
              <div id="empty-state" class="card">
                Select an incident to inspect services, dependencies,
                evidence, immutable history, timeline, findings, gaps, and report.
              </div>
              <div id="workspace" hidden>
                <div class="grid">
                  <article class="card wide">
                    <h2 id="incident-title"></h2>
                    <p id="incident-summary" class="muted"></p>
                    <button id="analyze">Run deterministic analysis</button>
                  </article>
                  <article class="card">
                    <h3>Services</h3>
                    <ul id="services"></ul>
                  </article>
                  <article class="card">
                    <h3>Dependencies</h3>
                    <ul id="dependencies"></ul>
                  </article>
                  <article class="card wide">
                    <h3>Evidence inventory</h3>
                    <ul id="evidence"></ul>
                  </article>
                  <article class="card wide">
                    <h3>Immutable incident history</h3>
                    <p class="muted">
                      Read-only bundle and analysis revisions. OPSCORE provides no restore,
                      rollback, edit, or delete action for historical revisions.
                    </p>
                    <ul id="history"></ul>
                  </article>
                  <article class="card">
                    <h3>Timeline</h3>
                    <ul id="timeline"></ul>
                  </article>
                  <article class="card">
                    <h3>Findings and gaps</h3>
                    <div id="findings"></div>
                  </article>
                  <article class="card wide">
                    <h3>Report preview</h3>
                    <button id="report" class="secondary">
                      Load Markdown report
                    </button>
                    <pre id="report-preview" class="muted">
Run analysis before loading a report.</pre>
                  </article>
                </div>
              </div>
            </section>
          </main>
          <script>
            let selectedIncident = null;
            const el = (id) => document.getElementById(id);
            const escapeHtml = (value) => String(value)
              .replaceAll("&", "&amp;")
              .replaceAll("<", "&lt;")
              .replaceAll(">", "&gt;")
              .replaceAll('"', "&quot;")
              .replaceAll("'", "&#039;");
            const request = async (url, options = {}) => {
              const response = await fetch(url, options);
              if (!response.ok) {
                const payload = await response.json();
                throw new Error(payload.detail || response.statusText);
              }
              const contentType = response.headers.get("content-type") || "";
              return contentType.includes("json")
                ? response.json()
                : response.text();
            };
            const listItems = (items, render) => items.length
              ? items.map((item) => `<li>${render(item)}</li>`).join("")
              : "<li class='muted'>None declared.</li>";
            async function refreshIncidents() {
              const incidents = await request("/api/incidents");
              el("incident-list").innerHTML = incidents.length
                ? incidents.map((incident) => `
                  <div class="incident"
                       data-id="${escapeHtml(incident.incident_id)}">
                    <strong>${escapeHtml(incident.title)}</strong><br>
                    <span class="muted">
                      ${escapeHtml(incident.incident_id)}
                    </span>
                  </div>`).join("")
                : "No incidents stored.";
              document.querySelectorAll(".incident").forEach((item) => {
                item.addEventListener(
                  "click",
                  () => loadIncident(item.dataset.id),
                );
              });
            }
            async function loadIncident(id) {
              selectedIncident = id;
              const bundle = await request(`/api/incidents/${id}`);
              el("empty-state").hidden = true;
              el("workspace").hidden = false;
              el("incident-title").textContent = bundle.incident.title;
              el("incident-summary").textContent = [
                bundle.incident.incident_id,
                bundle.incident.environment,
                bundle.incident.severity,
                bundle.incident.reported_symptom,
              ].join(" · ");
              el("services").innerHTML = listItems(
                bundle.services,
                (item) => `<strong>${escapeHtml(item.name)}</strong>
                  (${escapeHtml(item.service_type)})`,
              );
              el("dependencies").innerHTML = listItems(
                bundle.dependencies,
                (item) => `${escapeHtml(item.source_service_id)} →
                  ${escapeHtml(item.target_service_id)}
                  (${escapeHtml(item.dependency_type)},
                  ${item.required ? "required" : "optional"})`,
              );
              el("evidence").innerHTML = listItems(
                bundle.evidence,
                (item) => `<strong>${escapeHtml(item.evidence_type)}</strong>
                  · ${escapeHtml(item.source_system)}
                  · ${escapeHtml(item.collected_at)}`,
              );
              await loadHistory();
              await loadAnalysis(false);
            }
            async function loadHistory() {
              if (!selectedIncident) return;
              try {
                const revisions = await request(
                  `/api/incidents/${selectedIncident}/history`,
                );
                el("history").innerHTML = listItems(
                  revisions,
                  (item) => `<strong>Revision ${escapeHtml(item.revision_number)}</strong>
                    · ${escapeHtml(item.revision_type)}
                    · ${escapeHtml(item.created_at)}`,
                );
              } catch (error) {
                el("history").innerHTML = `<li class='muted'>${escapeHtml(error.message)}</li>`;
              }
            }
            async function loadAnalysis(run) {
              if (!selectedIncident) return;
              const suffix = run ? "analyze" : "analysis";
              const options = run ? {method: "POST"} : {};
              try {
                const analysis = await request(
                  `/api/incidents/${selectedIncident}/${suffix}`,
                  options,
                );
                el("timeline").innerHTML = listItems(
                  analysis.timeline,
                  (item) => `${escapeHtml(item.timestamp)} ·
                    <strong>${escapeHtml(item.event_type)}</strong>
                    · ${escapeHtml(item.summary)}`,
                );
                el("findings").innerHTML = analysis.findings.length
                  ? analysis.findings.map((finding) => `
                    <div>
                      <h4 class="${escapeHtml(finding.severity)}">
                        ${escapeHtml(finding.code)}
                      </h4>
                      <p>${escapeHtml(finding.statement)}</p>
                      <p class="muted">
                        Missing:
                        ${escapeHtml(
                          finding.missing_evidence.join(", ") || "none",
                        )}
                      </p>
                      <p>
                        Safe checks:
                        ${escapeHtml(
                          finding.safe_next_checks.join("; ") || "none",
                        )}
                      </p>
                    </div>`).join("")
                  : "<p class='muted'>No deterministic findings.</p>";
                if (run) await loadHistory();
              } catch (error) {
                el("timeline").innerHTML =
                  "<li class='muted'>Analysis not generated.</li>";
                el("findings").textContent = error.message;
              }
            }
            el("incident-form").addEventListener(
              "submit",
              async (event) => {
                event.preventDefault();
                const now = new Date().toISOString();
                const serviceId = el("service-id").value;
                const environment = el("environment").value;
                const severity = el("severity").value;
                const payload = {
                  incident: {
                    incident_id: el("incident-id").value,
                    title: el("title").value,
                    reported_symptom: el("symptom").value.trim(),
                    environment,
                    reported_at: now,
                    investigation_started_at: now,
                    affected_service_ids: [serviceId],
                    severity,
                    status: "new",
                    root_cause_status: "unassessed",
                  },
                  services: [{
                    service_id: serviceId,
                    name: el("service-name").value,
                    service_type: "application",
                    environment,
                    expected_endpoints: [],
                    owner: null,
                    criticality: severity,
                  }],
                  dependencies: [],
                  evidence: [],
                };
                try {
                  await request("/api/incidents", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(payload),
                  });
                  el("form-status").textContent = "Incident created.";
                  await refreshIncidents();
                  await loadIncident(payload.incident.incident_id);
                } catch (error) {
                  el("form-status").textContent = error.message;
                }
              },
            );
            el("refresh").addEventListener("click", refreshIncidents);
            el("analyze").addEventListener(
              "click",
              () => loadAnalysis(true),
            );
            el("report").addEventListener("click", async () => {
              try {
                el("report-preview").textContent = await request(
                  `/api/incidents/${selectedIncident}/report.md`,
                );
              } catch (error) {
                el("report-preview").textContent = error.message;
              }
            });
            refreshIncidents();
          </script>
        </body>
        </html>
        """
    ).strip()
