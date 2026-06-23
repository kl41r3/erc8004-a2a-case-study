"""
Socio-semantic Bipartite Network (R2) — entry point.

Uses R2 consensus annotations + new Thematic-LM coded records.

Usage:
    uv run python scripts/analyse/network_discourse/sociosemantic/run_r2.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "scripts/analyse/network_discourse"))

from sociosemantic.build import build
from sociosemantic.compare import (
    summary_metrics,
    thematic_overlap,
    plot_entropy_comparison,
    plot_theme_actor_comparison,
)
from loader_r2 import load_joined_r2

OUT_DIR = ROOT / "output/network_discourse/r2/sociosemantic"
THEMATIC_LM_DIR = ROOT / "output/topic_discovery/r2/thematic_lm"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load R2 themes label map
    themes_path = THEMATIC_LM_DIR / "themes.json"
    if not themes_path.exists():
        print(f"WARNING: themes.json not found at {themes_path}")
        print("Run the R2 Thematic-LM pipeline first.")
        themes_meta = {}
    else:
        themes_raw = json.loads(themes_path.read_text())
        themes_meta = {t["theme_id"]: t.get("label", t["theme_id"]) for t in themes_raw}

    print("Building R2 socio-semantic networks...")
    data = build(load_fn=load_joined_r2)

    all_metrics: dict = {}

    for case in ("ERC-8004", "Google-A2A"):
        if case not in data["by_case"]:
            print(f"  WARNING: {case} not found in R2 data")
            continue
        cd = data["by_case"][case]
        m = summary_metrics(cd)
        all_metrics[case] = m

        print(f"\n[{case}]")
        print(f"  Actors: {m['n_actors']}, Active themes: {m['n_themes']}")
        print(f"  Actor-actor projection edges: {m['n_edges_actor_proj']}")
        print(f"  Actor entropy — mean={m['actor_entropy']['mean']}, "
              f"median={m['actor_entropy']['median']}, "
              f"gini={m['actor_entropy']['gini']}")

        safe = case.replace("-", "").replace(" ", "_").lower()
        cd["actor_diversity"].to_csv(OUT_DIR / f"actor_diversity_{safe}.csv", index=False)
        cd["theme_concentration"].to_csv(OUT_DIR / f"theme_concentration_{safe}.csv", index=False)
        cd["B"].to_csv(OUT_DIR / f"actor_topic_matrix_{safe}.csv")

    # Cross-case thematic overlap (only if both cases present)
    if "ERC-8004" in data["by_case"] and "Google-A2A" in data["by_case"]:
        ov = thematic_overlap(data["by_case"]["ERC-8004"], data["by_case"]["Google-A2A"])
        print(f"\n[Cross-case]")
        print(f"  Thematic overlap coefficient: {ov['overlap_coefficient']}")
        print(f"  Shared themes: {ov['n_shared_themes']}, "
              f"ERC-only: {ov['n_erc_only']}, A2A-only: {ov['n_a2a_only']}")

        overlap_df = ov["theme_actor_comparison"].copy()
        if themes_meta:
            overlap_df.insert(1, "label", overlap_df["theme_id"].map(themes_meta))
        overlap_df.to_csv(OUT_DIR / "theme_actor_comparison.csv", index=False)

        metrics_out = {
            "ERC-8004": all_metrics.get("ERC-8004", {}),
            "Google-A2A": all_metrics.get("Google-A2A", {}),
            "cross_case": {
                "overlap_coefficient": ov["overlap_coefficient"],
                "n_shared_themes": ov["n_shared_themes"],
                "n_erc_only": ov["n_erc_only"],
                "n_a2a_only": ov["n_a2a_only"],
            },
        }

        # Visualize
        plot_entropy_comparison(
            data["by_case"]["ERC-8004"],
            data["by_case"]["Google-A2A"],
            OUT_DIR / "r2_specialization_compare.png",
        )
        if themes_meta:
            plot_theme_actor_comparison(
                overlap_df, themes_meta, OUT_DIR / "r2_theme_actor_comparison.png"
            )
    else:
        metrics_out = {k: v for k, v in all_metrics.items()}

    (OUT_DIR / "ss_metrics.json").write_text(
        json.dumps(metrics_out, indent=2, ensure_ascii=False)
    )
    print("\nSaved ss_metrics.json")
    print(f"\nR2 Socio-semantic analysis complete. Outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()
