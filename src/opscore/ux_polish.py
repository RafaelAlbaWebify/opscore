from __future__ import annotations


UX_STYLES = """
<style id="opscore-ux-polish">
.skip-link {
  position: fixed;
  top: .75rem;
  left: calc(var(--ops-sidebar-width) + 1rem);
  z-index: 100;
  translate: 0 -200%;
  padding: .65rem .9rem;
  border-radius: .45rem;
  background: var(--ops-navy-950);
  color: #fff;
  font-weight: 750;
  text-decoration: none;
}
.skip-link:focus { translate: 0; }
body { line-height: 1.45; }
button { min-height: 2.65rem; }
label { line-height: 1.35; }
.muted { line-height: 1.5; }
.ops-nav a[aria-current="page"] {
  border-color: rgba(255, 255, 255, .14);
  background: linear-gradient(90deg, rgba(25, 118, 233, .95),
    rgba(25, 118, 233, .7));
}
.ops-nav a:first-child:not([aria-current="page"]) { background: transparent; }
.ops-workflow {
  position: sticky;
  top: 0;
  z-index: 7;
  display: flex;
  gap: .45rem;
  margin-bottom: 1rem;
  padding: .55rem;
  overflow-x: auto;
  border: 1px solid var(--ops-slate-200);
  border-radius: .75rem;
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 4px 16px rgba(16, 34, 61, .06);
  backdrop-filter: blur(10px);
}
.ops-workflow a {
  flex: 0 0 auto;
  padding: .55rem .75rem;
  border-radius: .5rem;
  color: var(--ops-slate-700);
  font-size: .78rem;
  font-weight: 750;
  text-decoration: none;
}
.ops-workflow a:hover,
.ops-workflow a:focus-visible,
.ops-workflow a[aria-current="location"] {
  background: var(--ops-blue-100);
  color: var(--ops-blue-700);
}
.ops-intake { position: relative; }
.ops-intake .intake-heading { padding-right: 11rem; }
#toggle-intake {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: auto;
  min-height: 2.35rem;
  margin: 0;
}
#incident-form-host[hidden] { display: none; }
#form-status,
#ux-status {
  min-height: 1.4rem;
  font-size: .82rem;
  font-weight: 700;
}
.status-success { color: var(--ops-success-700) !important; }
.status-error { color: var(--ops-danger-700) !important; }
.status-working { color: var(--ops-blue-700) !important; }
#workspace .card { scroll-margin-top: 5rem; }
#workspace details > summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 2rem;
  cursor: pointer;
  color: var(--ops-slate-950);
  font-size: 1rem;
  font-weight: 800;
  list-style: none;
}
#workspace details > summary::-webkit-details-marker { display: none; }
#workspace details > summary::after {
  content: "+";
  color: var(--ops-blue-700);
  font-size: 1.2rem;
}
#workspace details[open] > summary::after { content: "−"; }
#workspace details .panel-body { padding-top: .85rem; }
#assessment-panel {
  margin-left: 0 !important;
  padding: 0 !important;
}
#assessment-panel .card { box-shadow: none; }
#assessment-preview,
#report-preview { min-height: 7rem; }
.report-rendered {
  max-height: 34rem;
  overflow: auto;
  padding: 1rem 1.15rem;
  border: 1px solid var(--ops-slate-200);
  border-radius: .55rem;
  background: var(--ops-slate-050);
  color: var(--ops-slate-800);
}
.report-rendered h4 {
  margin: 1rem 0 .35rem;
  font-size: .95rem;
}
.report-rendered p,
.report-rendered li { font-size: .82rem; line-height: 1.55; }
.report-rendered ul { margin: .35rem 0 .8rem; }
.ops-empty {
  padding: 1rem;
  border: 1px dashed var(--ops-slate-300);
  border-radius: .55rem;
  background: var(--ops-slate-050);
  color: var(--ops-slate-600);
  font-size: .84rem;
}
.ops-toast {
  position: fixed;
  right: 1.25rem;
  bottom: 1.25rem;
  z-index: 100;
  max-width: min(24rem, calc(100vw - 2rem));
  padding: .8rem 1rem;
  border: 1px solid var(--ops-slate-200);
  border-left: 4px solid var(--ops-blue-600);
  border-radius: .65rem;
  background: #fff;
  color: var(--ops-slate-800);
  box-shadow: 0 16px 42px rgba(16, 34, 61, .18);
  font-size: .84rem;
}
@media (max-width: 850px) {
  .skip-link { left: 1rem; }
  .ops-workflow { position: static; }
  .ops-intake .intake-heading { padding-right: 0; }
  #toggle-intake { position: static; width: 100%; margin-bottom: .8rem; }
}
</style>
"""


WORKFLOW_NAV = """
<nav class="ops-workflow" aria-label="Active incident workflow">
  <a href="#operations-overview">Overview</a>
  <a href="#incident-intake">Create</a>
  <a href="#workspace">Investigate</a>
  <a href="#evidence-panel">Evidence</a>
  <a href="#history-panel">History</a>
  <a href="#report-panel">Report</a>
  <a href="#assessment-panel">Assessment</a>
</nav>
<div id="ux-status" role="status" aria-live="polite"></div>
"""


UX_SCRIPT = r"""
<script>
(() => {
  const escapeText = (value) => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const status = document.getElementById("ux-status");
  const setStatus = (message, kind = "working") => {
    status.textContent = message;
    status.className = `status-${kind}`;
  };
  const toast = (message) => {
    document.querySelector(".ops-toast")?.remove();
    const notice = document.createElement("div");
    notice.className = "ops-toast";
    notice.setAttribute("role", "status");
    notice.textContent = message;
    document.body.appendChild(notice);
    window.setTimeout(() => notice.remove(), 3200);
  };
  const humanDate = (value) => {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(parsed);
  };
  const replaceIsoDates = (root) => {
    const pattern = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z/g;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      node.textContent = node.textContent.replace(pattern, humanDate);
    });
  };

  document.body.insertAdjacentHTML(
    "afterbegin",
    '<a class="skip-link" href="#operations-overview">Skip to workspace</a>',
  );
  const mainSection = document.querySelector("main > section");
  mainSection.insertAdjacentHTML("afterbegin", `__WORKFLOW_NAV__`);

  const intake = document.getElementById("incident-intake");
  const intakeHeading = document.createElement("div");
  intakeHeading.className = "intake-heading";
  while (intake.firstElementChild && intake.firstElementChild.id !== "incident-form-host") {
    intakeHeading.appendChild(intake.firstElementChild);
  }
  intake.prepend(intakeHeading);
  const toggle = document.createElement("button");
  toggle.id = "toggle-intake";
  toggle.className = "secondary";
  toggle.type = "button";
  toggle.setAttribute("aria-expanded", "false");
  toggle.textContent = "Create new incident";
  intake.prepend(toggle);
  const formHost = document.getElementById("incident-form-host");
  formHost.hidden = true;
  const setIntakeOpen = (open) => {
    formHost.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    toggle.textContent = open ? "Close incident intake" : "Create new incident";
    if (open) document.getElementById("incident-id").focus();
  };
  toggle.addEventListener("click", () => setIntakeOpen(formHost.hidden));
  document.querySelectorAll('a[href="#incident-intake"]').forEach((link) => {
    link.addEventListener("click", () => setIntakeOpen(true));
  });

  const panelNames = new Map([
    ["Evidence inventory", ["evidence-panel", false]],
    ["Immutable incident history", ["history-panel", false]],
    ["Report preview", ["report-panel", false]],
  ]);
  document.querySelectorAll("#workspace article.card").forEach((article) => {
    const heading = article.querySelector("h3");
    if (!heading || !panelNames.has(heading.textContent.trim())) return;
    const [id, open] = panelNames.get(heading.textContent.trim());
    article.id = id;
    const details = document.createElement("details");
    details.open = open;
    const summary = document.createElement("summary");
    summary.textContent = heading.textContent;
    const body = document.createElement("div");
    body.className = "panel-body";
    [...article.children].forEach((child) => {
      if (child !== heading) body.appendChild(child);
    });
    heading.remove();
    details.append(summary, body);
    article.appendChild(details);
  });

  const assessmentSection = document.getElementById("assessment-panel");
  const assessmentCard = assessmentSection.querySelector(".card");
  assessmentCard.classList.add("wide");
  assessmentCard.id = "assessment-panel";
  document.querySelector("#workspace .grid").appendChild(assessmentCard);
  assessmentSection.remove();

  const reportPreview = document.getElementById("report-preview");
  const reportRendered = document.createElement("div");
  reportRendered.className = "report-rendered";
  reportRendered.hidden = true;
  reportPreview.after(reportRendered);
  const renderReport = () => {
    const markdown = reportPreview.textContent.trim();
    if (!markdown || markdown.startsWith("Run analysis")) return;
    const lines = markdown.split("\n");
    const output = [];
    let listOpen = false;
    const closeList = () => {
      if (listOpen) output.push("</ul>");
      listOpen = false;
    };
    lines.forEach((line) => {
      if (line.startsWith("## ")) {
        closeList();
        output.push(`<h4>${escapeText(line.slice(3))}</h4>`);
      } else if (line.startsWith("- ")) {
        if (!listOpen) output.push("<ul>");
        listOpen = true;
        output.push(`<li>${escapeText(line.slice(2))}</li>`);
      } else if (line.startsWith("> ")) {
        closeList();
        output.push(`<p><strong>Safety note:</strong> ${escapeText(line.slice(2))}</p>`);
      } else if (line.trim()) {
        closeList();
        output.push(`<p>${escapeText(line)}</p>`);
      }
    });
    closeList();
    reportRendered.innerHTML = output.join("");
    reportRendered.hidden = false;
    reportPreview.hidden = true;
  };
  new MutationObserver(renderReport).observe(reportPreview, {
    childList: true,
    characterData: true,
    subtree: true,
  });

  const loadAssessmentState = async () => {
    const preview = document.getElementById("assessment-preview");
    if (!selectedIncident) {
      preview.innerHTML = '<span class="ops-empty">Select an incident to review its operator assessment.</span>';
      return;
    }
    setStatus("Loading operator assessment…");
    try {
      document.getElementById("load-assessment").click();
      await new Promise((resolve) => window.setTimeout(resolve, 120));
      if (preview.textContent.includes("assessment not found")) {
        preview.innerHTML = '<span class="ops-empty">No operator assessment has been recorded for this incident.</span>';
      }
      replaceIsoDates(preview);
      setStatus("Incident workspace ready.", "success");
    } catch (error) {
      preview.textContent = error.message;
      setStatus("Assessment could not be loaded.", "error");
    }
  };

  const originalLoadIncident = loadIncident;
  loadIncident = async (id) => {
    setStatus("Loading incident workspace…");
    try {
      await originalLoadIncident(id);
      replaceIsoDates(document.getElementById("workspace"));
      await loadAssessmentState();
      document.querySelectorAll(".incident").forEach((item) => {
        item.setAttribute("aria-current", String(item.dataset.id === id));
      });
      toast(`Opened ${document.getElementById("incident-title").textContent}`);
    } catch (error) {
      setStatus(error.message, "error");
      throw error;
    }
  };

  const formStatus = document.getElementById("form-status");
  formStatus.setAttribute("role", "status");
  formStatus.setAttribute("aria-live", "polite");
  new MutationObserver(() => {
    const message = formStatus.textContent.trim();
    if (!message) return;
    const success = message === "Incident created.";
    formStatus.className = success ? "status-success" : "status-error";
    if (success) {
      setIntakeOpen(false);
      toast("Incident created and opened.");
    }
  }).observe(formStatus, {childList: true, characterData: true, subtree: true});

  const analyzeButton = document.getElementById("analyze");
  analyzeButton.addEventListener("click", () => {
    analyzeButton.disabled = true;
    analyzeButton.textContent = "Running analysis…";
    setStatus("Running deterministic analysis…");
    window.setTimeout(() => {
      analyzeButton.disabled = false;
      analyzeButton.textContent = "Run deterministic analysis";
      setStatus("Analysis completed.", "success");
      toast("Deterministic analysis completed.");
    }, 450);
  });

  const navLinks = [...document.querySelectorAll(".ops-nav a, .ops-workflow a")];
  navLinks.forEach((link) => link.removeAttribute("aria-current"));
  const observed = [...document.querySelectorAll(
    "#operations-overview, #incident-intake, #workspace, #evidence-panel, " +
    "#history-panel, #report-panel, #assessment-panel",
  )];
  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    navLinks.forEach((link) => {
      const active = link.getAttribute("href") === `#${visible.target.id}`;
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }, {rootMargin: "-15% 0px -70%", threshold: [0, .25, .5]});
  observed.forEach((section) => observer.observe(section));

  document.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => button.blur(), {passive: true});
  });
})();
</script>
"""


def apply_professional_ux(html: str) -> str:
    """Add progressive disclosure, feedback and accessible operator workflows."""
    script = UX_SCRIPT.replace("__WORKFLOW_NAV__", WORKFLOW_NAV)
    refreshed = html.replace("</head>", f"{UX_STYLES}</head>")
    return refreshed.replace("</body>", f"{script}</body>")
