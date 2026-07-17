from __future__ import annotations


FULL_PAGE_LAYOUT = """
<style id="opscore-full-page-layout">
body { position: relative; }
main > aside {
  position: absolute;
  inset: 0 auto 0 0;
  height: auto;
  min-height: 100vh;
}
#assessment-panel { margin-left: var(--ops-sidebar-width); }
@media (max-width: 850px) {
  main > aside {
    position: static;
    min-height: 0;
  }
  #assessment-panel { margin-left: 0; }
}
</style>
"""


def stabilize_full_page_layout(html: str) -> str:
    """Keep the desktop rail anchored from the top in full-page browser proof."""
    return html.replace("</head>", f"{FULL_PAGE_LAYOUT}</head>")
