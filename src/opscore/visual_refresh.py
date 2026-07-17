from __future__ import annotations


TRACE_ALIGNED_STYLES = """
<style id="opscore-visual-refresh">
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system,
    BlinkMacSystemFont, "Segoe UI", sans-serif;
  --ops-navy-950: #071a33;
  --ops-navy-900: #0b2342;
  --ops-blue-700: #135fca;
  --ops-blue-600: #1976e9;
  --ops-blue-100: #e8f2ff;
  --ops-blue-050: #f4f8ff;
  --ops-slate-950: #172033;
  --ops-slate-800: #29364d;
  --ops-slate-700: #445169;
  --ops-slate-600: #5f6b80;
  --ops-slate-500: #7b8799;
  --ops-slate-300: #cfd7e3;
  --ops-slate-200: #e1e6ee;
  --ops-slate-100: #edf1f6;
  --ops-slate-050: #f7f9fc;
  --ops-white: #ffffff;
  --ops-success-700: #287a4a;
  --ops-success-100: #e7f6ed;
  --ops-warning-700: #95620d;
  --ops-warning-100: #fff3d6;
  --ops-danger-700: #a63c35;
  --ops-danger-100: #fdebea;
  --ops-shadow: 0 1px 2px rgba(16, 34, 61, .04),
    0 8px 24px rgba(16, 34, 61, .045);
  --ops-focus: 0 0 0 3px rgba(25, 118, 233, .2);
  --ops-sidebar-width: 15.5rem;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  min-width: 20rem;
  background: #f6f8fb;
  color: var(--ops-slate-950);
}
body > header {
  margin-left: var(--ops-sidebar-width);
  padding: 2rem clamp(1.25rem, 3vw, 3rem) 1.5rem;
  border-bottom: 1px solid var(--ops-slate-200);
  background: rgba(246, 248, 251, .96);
}
body > header::before {
  display: block;
  margin-bottom: .45rem;
  color: var(--ops-blue-700);
  content: "INFRASTRUCTURE / PRODUCTION OPERATIONS";
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .11em;
}
body > header h1 {
  margin: 0 0 .35rem;
  color: var(--ops-slate-950);
  font-size: clamp(1.75rem, 3vw, 2.35rem);
  letter-spacing: -.035em;
}
body > header p,
.muted { color: var(--ops-slate-600); }
main {
  grid-template-columns: var(--ops-sidebar-width) minmax(0, 1fr);
  min-height: calc(100vh - 8rem);
}
main > aside {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 10;
  width: var(--ops-sidebar-width);
  height: 100vh;
  overflow-y: auto;
  padding: 6.2rem .9rem 1.5rem;
  border: 0;
  background: linear-gradient(180deg, var(--ops-navy-950), var(--ops-navy-900));
  color: #fff;
}
main > aside::before {
  position: absolute;
  top: 1.5rem;
  left: 1.25rem;
  white-space: pre;
  color: #fff;
  content: "OPSCORE\A INCIDENT EVIDENCE";
  font-size: .97rem;
  font-weight: 850;
  line-height: 1.05;
  letter-spacing: .045em;
}
.ops-nav {
  display: grid;
  gap: .25rem;
  margin: 0 0 1.25rem;
}
.ops-nav a {
  display: grid;
  gap: .12rem;
  padding: .72rem .8rem;
  border: 1px solid transparent;
  border-radius: .7rem;
  color: rgba(255, 255, 255, .9);
  font-size: .86rem;
  font-weight: 720;
  text-decoration: none;
}
.ops-nav a:first-child {
  border-color: rgba(255, 255, 255, .08);
  background: linear-gradient(90deg, rgba(25, 118, 233, .95),
    rgba(25, 118, 233, .7));
}
.ops-nav a:hover,
.ops-nav a:focus-visible { background: rgba(255, 255, 255, .085); }
.ops-nav span { color: rgba(255, 255, 255, .55); font-size: .7rem; }
main > aside h2 {
  margin: 1.15rem 0 .7rem;
  color: rgba(255, 255, 255, .62);
  font-size: .7rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}
main > aside hr { border: 0; border-top: 1px solid rgba(255, 255, 255, .12); }
main > aside .muted { color: rgba(255, 255, 255, .64); }
main > section {
  grid-column: 2;
  padding: 1.5rem clamp(1.25rem, 3vw, 3rem) 3rem;
}
button,
input,
textarea,
select {
  border-color: var(--ops-slate-300);
  border-radius: .45rem;
  background: var(--ops-white);
  color: var(--ops-slate-950);
  font: inherit;
}
input:focus,
textarea:focus,
select:focus,
button:focus-visible {
  outline: none;
  box-shadow: var(--ops-focus);
}
button {
  border-color: var(--ops-blue-700);
  background: var(--ops-blue-700);
  color: #fff;
}
button:hover { background: #0f55b6; }
button.secondary {
  border-color: var(--ops-slate-300);
  background: var(--ops-white);
  color: var(--ops-slate-800);
}
main > aside button,
main > aside input,
main > aside textarea,
main > aside select {
  border-color: rgba(255, 255, 255, .16);
  background: rgba(255, 255, 255, .08);
  color: #fff;
}
main > aside option { color: var(--ops-slate-950); }
.incident {
  padding: .8rem;
  border-color: rgba(255, 255, 255, .12);
  border-radius: .65rem;
  background: rgba(255, 255, 255, .045);
}
.incident:hover { border-color: rgba(114, 167, 255, .8); }
.grid { gap: 1rem; }
.card {
  padding: 1.25rem;
  border-color: var(--ops-slate-200);
  border-radius: .8rem;
  background: var(--ops-white);
  color: var(--ops-slate-950);
  box-shadow: var(--ops-shadow);
}
.card h2,
.card h3,
.card h4 { color: var(--ops-slate-950); }
.card h2 { margin-top: 0; font-size: 1.45rem; letter-spacing: -.025em; }
.card h3 { margin-top: 0; font-size: 1rem; }
.card li { margin: .4rem 0; color: var(--ops-slate-700); }
#workspace > .grid > .card:first-child {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 1rem;
}
#workspace > .grid > .card:first-child p { grid-column: 1; margin: 0; }
#workspace > .grid > .card:first-child button {
  grid-column: 2;
  grid-row: 1 / span 2;
}
#findings > div {
  padding: .85rem 0;
  border-bottom: 1px solid var(--ops-slate-200);
}
#findings > div:last-child { border-bottom: 0; }
.critical { color: var(--ops-danger-700); }
.warning { color: var(--ops-warning-700); }
#report-preview,
#assessment-preview {
  max-height: 30rem;
  overflow: auto;
  padding: 1rem;
  border: 1px solid var(--ops-slate-200);
  border-radius: .55rem;
  background: var(--ops-slate-050);
  color: var(--ops-slate-700);
  font-size: .78rem;
  line-height: 1.55;
}
#assessment-panel {
  grid-column: 2;
  width: auto;
  padding: 0 clamp(1.25rem, 3vw, 3rem) 3rem !important;
  border: 0 !important;
}
.ops-safety-note {
  margin-bottom: 1rem;
  padding: .85rem 1rem;
  border: 1px solid #b9d3f2;
  border-left: 4px solid var(--ops-blue-600);
  border-radius: .7rem;
  background: var(--ops-blue-050);
  color: #294766;
  font-size: .85rem;
  line-height: 1.5;
}
@media (max-width: 850px) {
  body > header { margin-left: 0; padding-top: 1.5rem; }
  main { display: block; }
  main > aside {
    position: static;
    width: auto;
    height: auto;
    max-height: none;
    padding-top: 5.5rem;
  }
  main > section,
  #assessment-panel { padding: 1rem !important; }
  .ops-nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .grid { grid-template-columns: 1fr; }
  #workspace > .grid > .card:first-child { display: block; }
  #workspace > .grid > .card:first-child button { width: 100%; }
}
</style>
"""


NAVIGATION = """
<nav class="ops-nav" aria-label="OPSCORE workspace navigation">
  <a href="#incident-list">Overview<span>Incident workload</span></a>
  <a href="#incident-list">Incidents<span>Register and selection</span></a>
  <a href="#incident-form">New incident<span>Validated intake</span></a>
  <a href="#workspace">Investigation<span>Evidence and findings</span></a>
  <a href="#assessment-panel">Assessment<span>Operator conclusion</span></a>
  <a href="#report-preview">Report<span>Reviewable output</span></a>
</nav>
"""


SAFETY_NOTE = """
<aside class="ops-safety-note">
  <strong>Read-only investigation boundary.</strong>
  OPSCORE records evidence and explicit operator assessment. It does not infer
  root cause, remediate infrastructure, or rewrite immutable history.
</aside>
"""


def apply_trace_aligned_visuals(html: str) -> str:
    """Apply TRACE's shared portfolio visual language to the OPSCORE interface."""
    refreshed = html.replace("</head>", f"{TRACE_ALIGNED_STYLES}</head>")
    refreshed = refreshed.replace("<aside>\n              <h2>Incidents", f"<aside>\n              {NAVIGATION}\n              <h2>Incidents")
    return refreshed.replace("<section>\n              <div id=\"empty-state\"", f"<section>\n              {SAFETY_NOTE}\n              <div id=\"empty-state\"")
