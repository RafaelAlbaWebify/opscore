from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright


def record(screenshot: Path, stage: str) -> None:
    path = screenshot.with_name("browser-checkpoints.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{stage}\n")


def settle_visual_state(page: Page, screenshot: Path) -> None:
    page.wait_for_timeout(4000)
    record(screenshot, "desktop:settle-wait-complete")
    analyze = page.locator("#analyze")
    expect(analyze).to_be_enabled()
    record(screenshot, "desktop:analyze-enabled")
    expect(analyze).to_have_text("Run deterministic analysis")
    record(screenshot, "desktop:analyze-label-restored")
    expect(page.locator(".ops-toast")).to_have_count(0)
    record(screenshot, "desktop:toast-cleared")
    page.evaluate("document.activeElement?.blur()")
    page.evaluate("window.scrollTo({top: 0, left: 0, behavior: 'instant'})")
    page.wait_for_timeout(250)
    record(screenshot, "desktop:scroll-reset")


def exercise_desktop(page: Page, base_url: str, screenshot: Path) -> None:
    record(screenshot, "desktop:start")
    page.goto(base_url, wait_until="networkidle")
    page.get_by_role("heading", name="OPSCORE Operator Workbench").wait_for()
    expect(page.get_by_role("navigation", name="Active incident workflow")).to_be_visible()
    expect(page.get_by_role("button", name="Create new incident")).to_be_visible()
    record(screenshot, "desktop:initial-layout")

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
    expect(page.get_by_text("No operator assessment has been recorded")).to_be_visible()
    record(screenshot, "desktop:incident-opened")

    analyze_url = f"{base_url}/api/incidents/inc-browser-001/analyze"
    with page.expect_response(lambda response: response.url == analyze_url) as response_info:
        page.get_by_role("button", name="Run deterministic analysis").click()
    assert response_info.value.status == 200
    page.get_by_text("No deterministic findings.").wait_for()
    record(screenshot, "desktop:analysis-complete")

    page.locator("#report-panel summary").click()
    report_url = f"{base_url}/api/incidents/inc-browser-001/report.md"
    with page.expect_response(lambda response: response.url == report_url) as report_info:
        page.get_by_role("button", name="Load Markdown report").click()
    assert report_info.value.status == 200
    record(screenshot, "desktop:report-response")
    report = page.locator(".report-rendered")
    expect(report).to_be_visible()
    expect(report).to_contain_text("OPSCORE Incident Evidence Report")
    expect(report).not_to_contain_text("**")
    expect(report).not_to_contain_text("# OPSCORE")
    expect(page.locator("#report-preview")).to_be_hidden()
    expect(page.locator("#assessment-panel")).to_be_visible()
    record(screenshot, "desktop:report-rendered")

    settle_visual_state(page, screenshot)
    record(screenshot, "desktop:settled")
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot), full_page=True)
    record(screenshot, "desktop:screenshot")


def exercise_narrow(page: Page, base_url: str, screenshot: Path) -> None:
    record(screenshot, "narrow:start")
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url, wait_until="networkidle")
    expect(page.get_by_role("navigation", name="Active incident workflow")).to_be_visible()
    expect(page.get_by_role("button", name="Create new incident")).to_be_visible()
    expect(page.locator(".incident-register-wrap")).to_be_visible()
    record(screenshot, "narrow:initial-layout")
    page.locator(".incident").first.click()
    page.get_by_role("heading", name="Browser verified incident").wait_for()
    expect(page.locator("#workspace")).to_be_visible()
    expect(page.locator("#assessment-panel")).to_be_visible()
    record(screenshot, "narrow:incident-opened")
    page.evaluate("document.activeElement?.blur()")
    page.screenshot(path=str(screenshot), full_page=True)
    record(screenshot, "narrow:screenshot")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=Path("artifacts/operator-interface.png"),
    )
    args = parser.parse_args()
    checkpoint = args.screenshot.with_name("browser-checkpoints.txt")
    checkpoint.unlink(missing_ok=True)
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
