from __future__ import annotations


COMPATIBILITY_SCRIPT = r"""
<script id="opscore-ux-compatibility">
(() => {
  const safeText = (value) => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
  const humanDate = (value) => {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(parsed);
  };
  const humanizeDates = (root) => {
    const pattern = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z/g;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      node.textContent = node.textContent.replace(pattern, humanDate);
    });
  };
  const status = document.getElementById("ux-status");
  const setStatus = (message, kind = "working") => {
    status.textContent = message;
    status.className = `status-${kind}`;
  };
  const loadAssessment = async (id) => {
    const preview = document.getElementById("assessment-preview");
    try {
      const assessment = await request(`/api/incidents/${id}/assessment`);
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
      if (error.message === "assessment not found") {
        preview.innerHTML =
          '<span class="ops-empty">No operator assessment has been recorded for this incident.</span>';
      } else {
        preview.textContent = error.message;
      }
    }
  };

  loadIncident = async (id) => {
    selectedIncident = id;
    setStatus("Loading incident workspace…");
    try {
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
        (item) => `<strong>${safeText(item.name)}</strong>
          (${safeText(item.service_type)})`,
      );
      el("dependencies").innerHTML = listItems(
        bundle.dependencies,
        (item) => `${safeText(item.source_service_id)} →
          ${safeText(item.target_service_id)}
          (${safeText(item.dependency_type)},
          ${item.required ? "required" : "optional"})`,
      );
      el("evidence").innerHTML = listItems(
        bundle.evidence,
        (item) => `<strong>${safeText(item.evidence_type)}</strong>
          · ${safeText(item.source_system)}
          · ${safeText(item.collected_at)}`,
      );
      await loadHistory();
      await loadAnalysis(false);
      await loadAssessment(id);
      humanizeDates(document.getElementById("workspace"));
      document.querySelectorAll(".incident").forEach((item) => {
        item.setAttribute("aria-current", String(item.dataset.id === id));
      });
      setStatus("Incident workspace ready.", "success");
    } catch (error) {
      setStatus(error.message, "error");
      throw error;
    }
  };
})();
</script>
"""


def apply_ux_compatibility(html: str) -> str:
    """Preserve the verified incident load path after presentation enhancements."""
    return html.replace("</body>", f"{COMPATIBILITY_SCRIPT}</body>")
