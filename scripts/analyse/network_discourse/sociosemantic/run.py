"""
Socio-semantic Bipartite Network — entry point.

Usage:
    uv run python scripts/analyse/network_discourse/sociosemantic/run.py
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

OUT_DIR = ROOT / "output/network_discourse/sociosemantic"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load themes label map
    themes_raw = json.loads(
        (ROOT / "output/topic_discovery/thematic_lm/themes.json").read_text()
    )
    themes_meta = {t["theme_id"]: t["label"] for t in themes_raw}

    print("Building socio-semantic networks...")
    data = build()

    all_metrics: dict = {}

    for case in ("ERC-8004", "Google-A2A"):
        cd = data["by_case"][case]
        m = summary_metrics(cd)
        all_metrics[case] = m

        print(f"\n[{case}]")
        print(f"  Actors: {m['n_actors']}, Active themes: {m['n_themes']}")
        print(f"  Actor-actor projection edges: {m['n_edges_actor_proj']}")
        print(f"  Actor entropy — mean={m['actor_entropy']['mean']}, "
              f"median={m['actor_entropy']['median']}, "
              f"gini={m['actor_entropy']['gini']}")
        print(f"  Actor modularity: {m['actor_modularity']}")
        if m["gatekeepers"]:
            print(f"  Top gatekeepers: {m['gatekeepers'][:3]}")

        # Save actor diversity table
        safe = case.replace("-", "").replace(" ", "_").lower()
        cd["actor_diversity"].to_csv(OUT_DIR / f"actor_diversity_{safe}.csv", index=False)
        cd["theme_concentration"].to_csv(OUT_DIR / f"theme_concentration_{safe}.csv", index=False)
        cd["B"].to_csv(OUT_DIR / f"actor_topic_matrix_{safe}.csv")

    # Cross-case thematic overlap
    ov = thematic_overlap(data["by_case"]["ERC-8004"], data["by_case"]["Google-A2A"])
    print(f"\n[Cross-case]")
    print(f"  Thematic overlap coefficient: {ov['overlap_coefficient']}")
    print(f"  Shared themes: {ov['n_shared_themes']}, "
          f"ERC-only: {ov['n_erc_only']}, A2A-only: {ov['n_a2a_only']}")

    # Add theme labels and save comparison
    overlap_df = ov["theme_actor_comparison"].copy()
    overlap_df.insert(1, "label", overlap_df["theme_id"].map(themes_meta))
    overlap_df.to_csv(OUT_DIR / "theme_actor_comparison.csv", index=False)

    # Serialize metrics (drop DataFrames)
    metrics_out = {
        "ERC-8004": all_metrics["ERC-8004"],
        "Google-A2A": all_metrics["Google-A2A"],
        "cross_case": {
            "overlap_coefficient": ov["overlap_coefficient"],
            "n_shared_themes": ov["n_shared_themes"],
            "n_erc_only": ov["n_erc_only"],
            "n_a2a_only": ov["n_a2a_only"],
        },
    }
    (OUT_DIR / "ss_metrics.json").write_text(
        json.dumps(metrics_out, indent=2, ensure_ascii=False)
    )
    print("\nSaved ss_metrics.json")

    # Visualize
    plot_entropy_comparison(
        data["by_case"]["ERC-8004"],
        data["by_case"]["Google-A2A"],
        OUT_DIR / "specialization_compare.png",
    )
    plot_theme_actor_comparison(
        overlap_df, themes_meta, OUT_DIR / "theme_actor_comparison.png"
    )

    print("\nSocio-semantic analysis complete.")
    print(f"Outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()
