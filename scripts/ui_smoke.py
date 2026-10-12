"""Drive the PantryPulse UI through a full CRUD journey in a real browser.

    pip install playwright && playwright install chromium
    python scripts/ui_smoke.py http://localhost:3000 [screenshot_dir]

Steps: receive a new lot (POST), dispatch part of it (POST + quantity update),
edit it (PUT), void the dispatch and delete the lot (DELETE). Each step waits
for the API-backed UI to change, so a dead button or a broken /api route fails
the script. Screenshots are optional.
"""

import sys
import time
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

base = sys.argv[1].rstrip("/")
shots = Path(sys.argv[2]) if len(sys.argv) > 2 else None
item = f"UI smoke lentils {int(time.time()) % 100000}"


def snap(page, name):
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
        page.wait_for_timeout(450)
        page.screenshot(path=shots / f"{name}.png")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base, wait_until="load")
    expect(page.locator(".lot").first).to_be_visible()

    # CREATE
    page.get_by_role("button", name="Receive stock").first.click()
    drawer = page.get_by_role("dialog", name="Receive stock")
    drawer.get_by_label("Item").fill(item)
    drawer.get_by_label("Category").select_option("protein")
    drawer.get_by_label("Quantity").fill("25")
    drawer.get_by_label("Best before").fill((date.today() + timedelta(days=6)).isoformat())
    drawer.get_by_label("Donor").select_option(index=1)
    drawer.get_by_label("Notes").fill("Logged by the UI smoke test")
    snap(page, "crud-1-create-form")
    drawer.get_by_role("button", name="Receive stock").click()
    card = page.locator(".lot", has_text=item)
    expect(card).to_be_visible()
    expect(page.locator(".toast")).to_contain_text("added to the shelf")
    card.scroll_into_view_if_needed()
    snap(page, "crud-2-created")

    # DISPATCH (POST /api/dispatches, decrements the lot)
    card.get_by_role("button", name="Dispatch").click()
    d = page.get_by_role("dialog", name="Dispatch to a partner")
    d.get_by_label("Partner organisation").fill("Asha Night Shelter")
    d.get_by_label("Quantity (kg)").fill("10")
    d.get_by_role("button", name="Record dispatch").click()
    expect(card.locator(".lot__qty .num")).to_have_text("15")
    card.scroll_into_view_if_needed()
    snap(page, "crud-3-dispatched")

    # UPDATE (PUT)
    card.get_by_role("button", name=f"Edit {item}").click()
    e = page.get_by_role("dialog", name="Edit stock lot")
    e.get_by_label("Quantity").fill("14.5")
    e.get_by_label("Status").select_option("on_hold")
    e.get_by_role("button", name="Save changes").click()
    expect(card.locator(".lot__qty .num")).to_have_text("14.5")
    expect(card.locator(".status")).to_have_text("on hold")
    card.scroll_into_view_if_needed()
    snap(page, "crud-4-updated")

    # DELETE is refused while dispatch history exists (409), so void the dispatch first.
    page.get_by_role("button", name="Dispatch log").click()
    row = page.locator("tr", has_text=item)
    row.get_by_role("button", name="Void").click()
    page.get_by_role("button", name="Yes, do it").click()
    expect(row).to_have_count(0)
    page.get_by_role("button", name="Shelf").click()
    card.get_by_role("button", name=f"Delete {item}").click()
    page.get_by_role("button", name="Yes, do it").click()
    expect(page.locator(".lot", has_text=item)).to_have_count(0)
    expect(page.locator(".toast").last).to_contain_text("Lot deleted")
    snap(page, "crud-5-deleted")

    browser.close()
    if errors:
        sys.exit(f"page errors: {errors}")

print(f"UI CRUD journey passed against {base} (item: {item})")
