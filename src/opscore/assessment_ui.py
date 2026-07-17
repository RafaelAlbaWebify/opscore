from __future__ import annotations


def enhance_operator_interface(html: str) -> str:
    """Add a read-only assessment panel without coupling it to core UI rendering."""
    panel = """
      <section id="assessment-panel" style="border-top:1px solid #26314d;padding:24px;">
        <div class="card">
          <h2>Operator assessment</h2>
          <p class="muted">Explicit operator hypotheses and conclusion status.</p>
          <button id="load-assessment" class="secondary">Load current assessment</button>
          <pre id="assessment-preview" class="muted">Select an incident first.</pre>
        </div>
      </section>
      <script>
        document.getElementById("load-assessment").addEventListener("click", async () => {
          const preview = document.getElementById("assessment-preview");
          if (!selectedIncident) {
            preview.textContent = "Select an incident first.";
            return;
          }
          try {
            const assessment = await request(
              `/api/incidents/${selectedIncident}/assessment`,
            );
            const hypotheses = assessment.hypotheses.length
              ? assessment.hypotheses.map((item) =>
                  `${item.hypothesis_id}: ${item.status} — ${item.statement}`
                ).join("\n")
              : "No hypotheses recorded.";
            preview.textContent = [
              `Assessed by: ${assessment.assessed_by}`,
              `Assessed at: ${assessment.assessed_at}`,
              `Conclusion status: ${assessment.root_cause.status}`,
              `Statement: ${assessment.root_cause.statement || "not stated"}`,
              `Rationale: ${assessment.root_cause.operator_rationale}`,
              "",
              "Hypotheses:",
              hypotheses,
            ].join("\n");
          } catch (error) {
            preview.textContent = error.message;
          }
        });
      </script>
    """
    return html.replace("</body>", f"{panel}</body>")
