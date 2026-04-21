#!/usr/bin/env python3
"""Automate SSO login and launch Citrix virtual desktop."""

import os
import subprocess
import sys

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

load_dotenv()

SSO_URL = os.environ.get("SSO_URL")
USERNAME = os.environ.get("SSO_USERNAME")
PIN = os.environ.get("SSO_PIN")
FAVORITE_DEVICE = os.environ.get("VD_FAVORITE_DEVICE", "").strip()


def pick_device(devices):
    """Show a native macOS picker and return the chosen label, or None if cancelled."""
    escaped = [d.replace('"', '\\"') for d in devices]
    items = ", ".join(f'"{d}"' for d in escaped)
    script = (
        f'choose from list {{{items}}} '
        'with title "VD Login" '
        'with prompt "Choose 2FA device:" '
        f'default items {{"{escaped[0]}"}}'
    )
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True
    )
    out = result.stdout.strip()
    if out in ("", "false"):
        return None
    return out


def handle_device_selection(page):
    """If the Airlock device-selection page is present, pick a device and submit.

    No-op if the page does not appear within a short window.
    """
    try:
        page.wait_for_selector('input[type="radio"]', timeout=8000)
    except PlaywrightTimeoutError:
        return

    radios = page.locator('input[type="radio"]')
    count = radios.count()
    if count == 0:
        return

    devices = []
    for i in range(count):
        radio = radios.nth(i)
        radio_id = radio.get_attribute("id")
        label = ""
        if radio_id:
            label_loc = page.locator(f'label[for="{radio_id}"]')
            if label_loc.count() > 0:
                label = (label_loc.first.text_content() or "").strip()
        if not label:
            label = (radio.get_attribute("value") or f"Device {i + 1}").strip()
        devices.append((label, radio))

    labels = [d[0] for d in devices]
    chosen_label = None

    if FAVORITE_DEVICE:
        for label, _ in devices:
            if label.casefold() == FAVORITE_DEVICE.casefold():
                chosen_label = label
                print(f"Auto-selecting favorite device: {label}")
                break
        if chosen_label is None:
            print(
                f"Favorite device '{FAVORITE_DEVICE}' not in list {labels}; prompting.",
                file=sys.stderr,
            )

    if chosen_label is None:
        print("Multiple 2FA devices found, prompting...")
        chosen_label = pick_device(labels)
        if chosen_label is None:
            print("Device selection cancelled.", file=sys.stderr)
            raise SystemExit(1)

    chosen_radio = next(r for label, r in devices if label == chosen_label)
    chosen_radio.check()
    page.click('button[type="submit"], input[type="submit"]')


def main():
    if not SSO_URL or not USERNAME or not PIN:
        print("Error: SSO_USERNAME and SSO_PIN must be set in .env or environment")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Opening SSO page...")
        page.goto(SSO_URL)

        print("Filling username...")
        page.fill('input[name="username"], input[type="text"]', USERNAME)
        page.click('button[type="submit"], input[type="submit"]')

        print("Waiting for PIN field...")
        page.wait_for_selector('input[name="pin"], input[type="password"]', timeout=30000)

        print("Filling PIN...")
        page.fill('input[name="pin"], input[type="password"]', PIN)

        print("Submitting...")
        page.click('button[type="submit"], input[type="submit"]')

        try:
            handle_device_selection(page)
        except SystemExit:
            browser.close()
            raise

        print("Complete 2FA in the browser, then wait for .ica download...")
        with page.expect_download(timeout=120000) as download_info:
            pass
        download = download_info.value
        path = download.path()

        if path:
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", download.suggested_filename)
            download.save_as(save_path)
            print(f"Downloaded: {save_path}")

            print("Opening with Citrix Workspace...")
            subprocess.run(["open", save_path])
        else:
            print("Error: Download failed")
            sys.exit(1)

        browser.close()

    print("Done!")


if __name__ == "__main__":
    main()
