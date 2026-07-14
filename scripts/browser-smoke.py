from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


def exercise_interface(page: Page, base_url: str, screenshot: Path) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("heading", name="OPSCORE Operator Workbench").wait_for()
    page.get_by_label("Incident ID").fill("inc-browser-001")
    page.get_by_label("Title").fill("Browser verified incident")
    page.get_by_label("Symptom").fill("Synthetic operator interface verification.")
    page.get_by_label("Service ID").fill("browser-service")
    page.get_by_label("Service name").fill("Browser service")
    page.get_by_role("button", name="Create incident").click()
    page.get_by_text("Incident created.").wait_for()
    page.get_by_role("heading", name="Browser verified incident").wait_for()
    page.get_by_role("button", name="Run deterministic analysis").click()
    page.get_by_text("No deterministic findings.").wait_for()
    page.get_by_role("button", name="Load Markdown report").click()
    page.get_by_text("OPSCORE Incident Evidence Report").wait_for()
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot), full_page=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=Path("artifacts/operator-interface.png"),
    )
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        exercise_interface(page, args.base_url, args.screenshot)
        browser.close()


if __name__ == "__main__":
    main()
