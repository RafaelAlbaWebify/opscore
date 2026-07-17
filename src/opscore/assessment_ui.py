from __future__ import annotations

from opscore.layout_finish import stabilize_full_page_layout
from opscore.operational_ui import add_operational_overview
from opscore.ux_polish import apply_professional_ux
from opscore.visual_refresh import apply_trace_aligned_visuals


def enhance_operator_interface(html: str) -> str:
    """Add assessment visibility and apply the portfolio interface layers."""
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
    with_assessment = html.replace("</body>", f"{panel}</body>")
    with_visuals = apply_trace_aligned_visuals(with_assessment)
    with_overview = add_operational_overview(with_visuals)
    stabilized = stabilize_full_page_layout(with_overview)
    return apply_professional_ux(stabilized)
