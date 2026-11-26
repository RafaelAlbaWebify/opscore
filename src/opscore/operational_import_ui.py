from __future__ import annotations


def add_operational_import_ui(html: str) -> str:
    """Append a local, explicit evidence import control to the rendered workbench."""
    panel = """
    <script>
    (() => {
      const grid = document.querySelector("#workspace .grid");
      if (!grid) return;
      const card = document.createElement("article");
      card.className = "card wide";
      card.id = "operational-import-panel";
      card.innerHTML = '<h3>Import operational evidence</h3>' +
        '<p>JSON or application text logs. Selected diagnostic counts are retained, not raw records. ' +
        'Use authorized files and retain originals separately.</p>' +
        '<form id="operational-import-form">' +
        '<label>Evidence type <select id="operational-kind">' +
        '<option value="application-log">Application logs</option>' +
        '<option value="windows-event">Windows events</option>' +
        '<option value="iis">IIS snapshot</option></select></label>' +
        '<label>Incident service ID <input id="operational-target" required></label>' +
        '<label>Collection time (UTC ISO 8601) ' +
        '<input id="operational-time" required placeholder="2026-07-14T08:10:00Z"></label>' +
        '<label>Evidence file <input id="operational-file" type="file" accept=".json,.log,.txt" required>' +
        '</label><button type="submit">Import evidence</button></form>' +
        '<p id="operational-status" role="status" class="muted"></p>';
      grid.appendChild(card);
      const field = (id) => document.getElementById(id);
      field("operational-import-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const status = field("operational-status");
        const incident = selectedIncident;
        const file = field("operational-file").files[0];
        if (!incident || !file || file.size > 2097152) {
          status.textContent = "Select an incident and an evidence file up to 2 MiB.";
          return;
        }
        const button = event.currentTarget.querySelector("button");
        button.disabled = true;
        try {
          const payload = {
            kind: field("operational-kind").value,
            target_reference: field("operational-target").value,
            collected_at: field("operational-time").value,
            content: await file.text(),
            input_format: /\\.(log|txt)$/i.test(file.name) ? "text" : "json",
          };
          await request(
            "/api/incidents/" + encodeURIComponent(incident) + "/operational-import",
            {method: "POST", headers: {"Content-Type": "application/json"},
             body: JSON.stringify(payload)}
          );
          field("operational-file").value = "";
          status.textContent = "Imported. Run analysis to refresh findings.";
          if (selectedIncident === incident) await loadIncident(incident);
        } catch (_) {
          status.textContent = "Import rejected or unavailable. Check the file and service ID.";
        } finally {
          button.disabled = false;
        }
      });
    })();
    </script>
    """
    return html.replace("</body>", f"{panel}</body>")
