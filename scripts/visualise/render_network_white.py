"""
render_network_white.py — Render white-background network HTML to PNG + PDF.

Uses Playwright headless Chromium to:
  1. Open the white-background HTML
  2. Wait for both vis.js networks to finish physics stabilization
  3. Capture full-page PNG at 300 DPI and PDF (vector)

Output:
  output/figures/r2/network_compare_white.png
  output/figures/r2/network_compare_white.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, OUTPUT_FIGURES, OUTPUT_INTERACTIVE

OUTPUT_DIR = OUTPUT_FIGURES
HTML_PATH = OUTPUT_INTERACTIVE / "network_compare_white.html"
PNG_PATH = OUTPUT_FIGURES / "network_compare_white.png"
PDF_PATH = OUTPUT_FIGURES / "network_compare_white.pdf"


def main():
    if not HTML_PATH.exists():
        print(f"ERROR: {HTML_PATH} not found", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # High-res viewport: 3600×1800 at deviceScaleFactor=2 = effective 7200px width for 300+ DPI
        page = browser.new_page(
            viewport={"width": 3600, "height": 1800},
            device_scale_factor=2,
        )

        print("Loading HTML...")
        page.goto(f"file://{HTML_PATH}", wait_until="networkidle")

        # Wait for vis.js to be available and both networks to stabilize
        print("Waiting for vis.js networks to stabilize...")
        page.wait_for_function(
            """
            () => {
                return typeof vis !== 'undefined'
                    && document.getElementById('net-erc')
                    && document.getElementById('net-a2a');
            }
            """,
            timeout=15000,
        )

        # Wait for both networks to finish physics stabilization
        # vis.js fires 'stabilizationIterationsDone' when physics settles
        page.evaluate("""
            () => {
                return Promise.all([
                    new Promise(resolve => {
                        const netErc = document.getElementById('net-erc');
                        // vis.Network stores instance data on the container
                        // We need to access the network instance
                        // Since the script creates them as global vars, we can find them
                        const interval = setInterval(() => {
                            const canvases = document.querySelectorAll('canvas');
                            if (canvases.length >= 2) {
                                clearInterval(interval);
                                // Wait a bit more for final rendering
                                setTimeout(resolve, 2000);
                            }
                        }, 500);
                        setTimeout(() => { clearInterval(interval); resolve(); }, 15000);
                    })
                ]);
            }
        """)

        # Extra settle time for final rendering
        page.wait_for_timeout(3000)

        print("Capturing PNG at high resolution...")
        page.screenshot(path=str(PNG_PATH), full_page=True)
        print(f"  PNG → {PNG_PATH}")

        print("Capturing PDF...")
        page.pdf(
            path=str(PDF_PATH),
            format="A2",  # large format to fit side-by-side layout
            landscape=True,
            print_background=True,
        )
        print(f"  PDF → {PDF_PATH}")

        browser.close()

    # Print file sizes
    for p in [PNG_PATH, PDF_PATH]:
        if p.exists():
            size_kb = p.stat().st_size / 1024
            print(f"  {p.name}: {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
