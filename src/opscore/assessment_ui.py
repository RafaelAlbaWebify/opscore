from __future__ import annotations

from opscore.visual_refresh import apply_trace_aligned_visuals


def enhance_operator_interface(html: str) -> str:
    """Add assessment visibility and apply the shared portfolio visual language."""
    panel = """
      <section id="assessment-panel">
        <div class="card">
          <h2>Operator assessment</h2>
          <p class="muted">
            Explicit operator hypotheses and conclusion status, kept separate
            from deterministic findings.
          </p>
          <button id="load-assessment" class="secondary">
            Load current assessment
          </button>
          <pre id="assessment-preview" class="muted">
Select an incident first.</pre>
        </div>
      </section>
      <script>
        document
          .getElementById("load-assessment")
          .addEventListener("click", async () => {
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
    enhanced = html.replace("</body>", f"{panel}</body>")
    return apply_trace_aligned_visuals(enhanced)
