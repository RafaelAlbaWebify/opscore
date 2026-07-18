from __future__ import annotations


FINISH_STYLES = """
<style id="opscore-professional-finish">
#workspace > .grid > #assessment-panel {
  grid-column: 1 / -1;
  width: 100%;
}
#workspace > .grid > #assessment-panel pre {
  white-space: pre-wrap;
}
.report-rendered h2 {
  margin: 0 0 .8rem;
  font-size: 1.12rem;
  letter-spacing: -.015em;
}
.report-rendered h3 {
  margin: 1.1rem 0 .4rem;
  font-size: .98rem;
}
.report-rendered strong { color: var(--ops-slate-950); }
.report-rendered code {
  padding: .08rem .28rem;
  border-radius: .28rem;
  background: var(--ops-slate-100);
  color: var(--ops-slate-800);
  font-size: .78rem;
}
@media (max-width: 850px) {
  main > aside::before { display: none; }
  main > aside { padding-top: 1.25rem; }
  .ops-workflow {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .35rem;
    overflow: visible;
  }
  .ops-workflow a {
    min-width: 0;
    padding: .55rem .35rem;
    text-align: center;
  }
}
@media (max-width: 540px) {
  body > header { padding: 1.2rem 1rem 1.35rem; }
  body > header h1 { font-size: 1.72rem; }
  main > section { padding: .85rem !important; }
  .ops-workflow { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .ops-workflow a { font-size: .73rem; }
  .card { padding: 1rem; }
  .incident-register { min-width: 42rem; }
}
</style>
"""


FINISH_SCRIPT = r"""
<script id="opscore-professional-finish-script">
(() => {
  const escapeInline = (value) => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const inlineMarkdown = (value) => {
    let rendered = escapeInline(value);
    rendered = rendered.replace(/`([^`]+)`/g, "<code>$1</code>");
    rendered = rendered.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return rendered;
  };

  const source = document.getElementById("report-preview");
  const target = document.querySelector(".report-rendered");
  const renderProfessionalReport = () => {
    const markdown = source.textContent.trim();
    if (!markdown || markdown.startsWith("Run analysis")) return;
    const output = [];
    let listOpen = false;
    const closeList = () => {
      if (listOpen) output.push("</ul>");
      listOpen = false;
    };
    markdown.split("\n").forEach((rawLine) => {
      const line = rawLine.trimEnd();
      if (line.startsWith("# ")) {
        closeList();
        output.push(`<h2>${inlineMarkdown(line.slice(2))}</h2>`);
      } else if (line.startsWith("## ")) {
        closeList();
        output.push(`<h3>${inlineMarkdown(line.slice(3))}</h3>`);
      } else if (line.startsWith("- ")) {
        if (!listOpen) output.push("<ul>");
        listOpen = true;
        output.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
      } else if (line.startsWith("> ")) {
        closeList();
        output.push(
          `<p><strong>Safety note:</strong> ${inlineMarkdown(line.slice(2))}</p>`,
        );
      } else if (line.trim()) {
        closeList();
        output.push(`<p>${inlineMarkdown(line)}</p>`);
      }
    });
    closeList();
    target.innerHTML = output.join("");
    target.hidden = false;
    source.hidden = true;
  };

  new MutationObserver(renderProfessionalReport).observe(source, {
    childList: true,
    characterData: true,
    subtree: true,
  });
  renderProfessionalReport();
})();
</script>
"""


def apply_professional_finish(html: str) -> str:
    """Apply final screenshot-verified layout and report presentation fixes."""
    with_styles = html.replace("</head>", f"{FINISH_STYLES}</head>")
    return with_styles.replace("</body>", f"{FINISH_SCRIPT}</body>")
