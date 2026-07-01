"""
extract_vis_positions.py — Extract stabilized vis.js node positions from HTML.

Rewrites the HTML temporarily to store network instances on window,
then extracts getPositions() after physics stabilization.

Output: output/figures/r2/vis_positions_erc.json
        output/figures/r2/vis_positions_a2a.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import ROOT, OUTPUT_FIGURES, OUTPUT_INTERACTIVE

OUTPUT_DIR = OUTPUT_FIGURES
HTML_PATH = OUTPUT_INTERACTIVE / "network_compare.html"


def main():
    if not HTML_PATH.exists():
        print(f"ERROR: {HTML_PATH} not found", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read HTML and inject window.__netErc / window.__netA2a assignments
    html = HTML_PATH.read_text()
    html = html.replace(
        'new vis.Network(document.getElementById("net-erc"),',
        'window.__netErc = new vis.Network(document.getElementById("net-erc"),',
    )
    html = html.replace(
        'new vis.Network(document.getElementById("net-a2a"),',
        'window.__netA2a = new vis.Network(document.getElementById("net-a2a"),',
    )
    tmp_path = OUTPUT_DIR / "_temp_positions.html"
    tmp_path.write_text(html, encoding="utf-8")
    print(f"Temp HTML: {tmp_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 3600, "height": 1800},
            device_scale_factor=1,
        )

        print("Loading HTML with network hooks...")
        page.goto(f"file://{tmp_path}", wait_until="networkidle")

        # Wait for vis.js
        page.wait_for_function("typeof vis !== 'undefined'", timeout=15000)
        # Wait for canvases
        page.wait_for_function(
            "() => document.querySelectorAll('canvas').length >= 2",
            timeout=15000,
        )

        # Wait 8s for physics to fully settle (forceAtlas2 needs time)
        print("Waiting for physics stabilization...")
        page.wait_for_timeout(8000)

        # Extra: wait for network instances to be available
        page.wait_for_function(
            "() => window.__netErc && window.__netA2a",
            timeout=10000,
        )

        # Now extract
        print("Extracting positions...")
        positions = page.evaluate("""() => {
            const result = {erc: {}, a2a: {}};
            try {
                const ep = window.__netErc.getPositions();
                for (const [k, v] of Object.entries(ep)) {
                    result.erc[k] = {x: v.x, y: v.y};
                }
            } catch(e) { console.error('ERC:', e); }
            try {
                const ap = window.__netA2a.getPositions();
                for (const [k, v] of Object.entries(ap)) {
                    result.a2a[k] = {x: v.x, y: v.y};
                }
            } catch(e) { console.error('A2A:', e); }
            return result;
        }""")

        erc_count = len(positions.get("erc", {}))
        a2a_count = len(positions.get("a2a", {}))
        print(f"Extracted: ERC={erc_count}, A2A={a2a_count}")

        # Save
        erc_path = OUTPUT_DIR / "vis_positions_erc.json"
        a2a_path = OUTPUT_DIR / "vis_positions_a2a.json"
        erc_path.write_text(json.dumps(positions["erc"], indent=1))
        a2a_path.write_text(json.dumps(positions["a2a"], indent=1))
        print(f"  → {erc_path} ({erc_count} nodes)")
        print(f"  → {a2a_path} ({a2a_count} nodes)")

        browser.close()

    # Clean temp file
    tmp_path.unlink()
    print("Done.")


if __name__ == "__main__":
    main()
