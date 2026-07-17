from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright


def exercise_desktop(page: Page, base_url: str, screenshot: Path) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("heading", name="OPSCORE Operator Workbench").wait_for()
    expect(page.get_by_role("navigation", name="Active incident workflow")).to_be_visible()
    expect(page.get_by_role("button", name="Create new incident")).to_be_visible()

    page.get_by_role("button", name="Create new incident").click()
    page.get_by_label("Incident ID").fill("inc-browser-001")
    page.get_by_label("Title").fill("Browser verified incident")
    page.get_by_label("Symptom").fill("Synthetic operator interface verification.")
    page.get_by_label("Service ID").fill("browser-service")
    page.get_by_label("Service name").fill("Browser service")
    page.get_by_role("button", name="Create incident").click()

    page.get_by_text("Incident created and opened.").wait_for()
    page.get_by_role("heading", name="Browser verified incident").wait_for()
    expect(page.locator("#metric-total")).to_have_text("1")
    expect(page.get_by_role("button", name="Create new incident")).to_be_visible()

    analyze = page.get_by_role("button", name="Run deterministic analysis")
    analyze.click()
    page.get_by_text("No deterministic findings.").wait_for()
    expect(analyze).to_be_enabled()
    expect(page.locator("#history")).to_contain_text("analysis")

    page.locator("#report-panel summary").click()
    page.get_by_role("button", name="Load Markdown report").click()
    page.locator(".report-rendered h4").first.wait_for()
    expect(page.locator("#report-preview")).to_be_hidden()
    expect(page.locator(".report-rendered")).to_be_visible()

    expect(page.get_by_text("No operator assessment has been recorded")).to_be_visible()
    expect(page.locator("#assessment-panel")).to_be_visible()

    screenshot.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot), full_page=True)


def exercise_narrow(page: Page, base_url: str, screenshot: Path) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url, wait_until="networkidle")
    expect(page.get_by_role("navigation", name="Active incident workflow")).to_be_visible()
    expect(page.get_by_role("button", name="Create new incident")).to_be_visible()
    expect(page.locator(".incident-register-wrap")).to_be_visible()
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
    narrow = args.screenshot.with_name(f"{args.screenshot.stem}-narrow.png")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        desktop = browser.new_page(viewport={"width": 1440, "height": 1100})
        exercise_desktop(desktop, args.base_url, args.screenshot)
        narrow_page = browser.new_page(viewport={"width": 390, "height": 844})
        exercise_narrow(narrow_page, args.base_url, narrow)
        browser.close()


if __name__ == "__main__":
    main()
