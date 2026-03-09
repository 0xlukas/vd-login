#!/usr/bin/env python3
"""Automate SSO login and launch Citrix virtual desktop."""

import os
import subprocess
import sys

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

SSO_URL = os.environ.get("SSO_URL")
USERNAME = os.environ.get("SSO_USERNAME")
PIN = os.environ.get("SSO_PIN")


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
