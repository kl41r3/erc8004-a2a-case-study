#!/usr/bin/env python3
"""
R2 Full Pipeline Runner — runs all analysis phases in order.

Phases:
  1. A2A ICR validation       (validate_multimodel.py --dataset a2a)
  2. Build consensus           (build_consensus.py)
  3. Structural metrics        (compute_metrics_r2.py)
  4. BERTopic                  (comparative_discourse/run_r2.py)
  5. A2A Thematic open-coding  (annotate_thematic_a2a.py × 3 models, parallel)
  6. Thematic-LM Stages 2-4    (thematic_lm/run_r2.py)
  7. SNA                       (build_network_r2.py)
  8. DNA                       (network_discourse/dna/run_r2.py)
  9. Socio-semantic            (network_discourse/sociosemantic/run_r2.py)
  10. Paper figures            (visualise/build_paper_figures_r2.py)

Usage:
    uv run python scripts/analyse/run_r2_pipeline.py
    uv run python scripts/analyse/run_r2_pipeline.py --from-phase 3   # resume from phase 3
    uv run python scripts/analyse/run_r2_pipeline.py --skip-thematic   # skip thematic open-coding
    uv run python scripts/analyse/run_r2_pipeline.py --skip-figures    # skip figures
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ── Phase definitions ─────────────────────────────────────────────────────────
# (phase_id, description, command_list, output_check_path)
PHASES = [
    (1, "A2A ICR Validation", [
        ["uv", "run", "python", "scripts/analyse/validate_multimodel.py", "--dataset", "a2a"],
    ], ROOT / "data" / "annotated" / "r2" / "a2a" / "validation" / "validation_report.json"),

    (2, "Build Consensus", [
        ["uv", "run", "python", "scripts/process/build_consensus.py"],
    ], ROOT / "data" / "annotated" / "r2" / "consensus" / "a2a_annotations.json"),

    (3, "Structural Metrics", [
        ["uv", "run", "python", "scripts/analyse/compute_metrics_r2.py"],
    ], ROOT / "analysis" / "r2_structural_metrics.csv"),

    (4, "BERTopic Comparative Discourse", [
        ["uv", "run", "python", "scripts/analyse/topic_discovery/comparative_discourse/run_r2.py"],
    ], ROOT / "output" / "topic_discovery" / "r2" / "comparative_discourse" / "divergence_table.csv"),

    (5, "A2A Thematic Open-coding (3 models)", [
        ["uv", "run", "python", "scripts/process/annotate_thematic_a2a.py", "--model", "deepseek"],
        ["uv", "run", "python", "scripts/process/annotate_thematic_a2a.py", "--model", "glm"],
        ["uv", "run", "python", "scripts/process/annotate_thematic_a2a.py", "--model", "kimi"],
    ], ROOT / "data" / "annotated" / "r2" / "thematic" / "a2a" / "kimi_themes.json"),

    (6, "Thematic-LM Stages 2-4", [
        ["uv", "run", "python", "scripts/analyse/topic_discovery/thematic_lm/run_r2.py"],
    ], ROOT / "output" / "topic_discovery" / "r2" / "thematic_lm" / "coded_records.json"),

    (7, "SNA Co-participation Networks", [
        ["uv", "run", "python", "scripts/analyse/build_network_r2.py"],
    ], ROOT / "analysis" / "r2_network_erc_nodes.csv"),

    (8, "DNA Discourse Network Analysis", [
        ["uv", "run", "python", "scripts/analyse/network_discourse/dna/run_r2.py"],
    ], ROOT / "output" / "network_discourse" / "r2" / "dna" / "dna_metrics.json"),

    (9, "Socio-semantic Bipartite Network", [
        ["uv", "run", "python", "scripts/analyse/network_discourse/sociosemantic/run_r2.py"],
    ], ROOT / "output" / "network_discourse" / "r2" / "sociosemantic" / "ss_metrics.json"),

    (10, "Paper Figures", [
        ["uv", "run", "python", "scripts/visualise/build_paper_figures_r2.py"],
    ], ROOT / "output" / "figures" / "r2" / "r2-fig-icr-heatmap.pdf"),
]


def check_prerequisites() -> bool:
    """Verify A2A annotation is complete (all 3 models have 4920 records)."""
    a2a_dir = ROOT / "data" / "annotated" / "r2" / "a2a"
    all_ok = True
    for model in ["deepseek", "glm", "kimi"]:
        p = a2a_dir / model / "annotations.json"
        if p.exists():
            n = len(json.loads(p.read_text()))
            status = "✓" if n >= 4900 else "⚠"
            print(f"  A2A {model}: {n} records  {status}")
            if n < 4900:
                all_ok = False
        else:
            print(f"  A2A {model}: MISSING  ✗")
            all_ok = False
    return all_ok


def run_phase(phase_id: int, description: str, commands: list[list[str]],
              output_check: Path, skip: bool = False) -> bool:
    """Run one phase. Returns True on success."""
    print(f"\n{'='*72}")
    print(f"Phase {phase_id}: {description}")
    print(f"{'='*72}")

    if skip:
        print("  SKIPPED (--from-phase > current)")
        return True

    # Check if output already exists
    if output_check.exists():
        print(f"  Output exists: {output_check}")
        print(f"  SKIPPING (already complete)")
        return True

    # Run all commands (parallel for multi-command phases)
    procs = []
    for cmd in commands:
        print(f"  Running: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, cwd=str(ROOT))
        procs.append(proc)

    # Wait for all to complete
    failed = False
    for i, proc in enumerate(procs):
        ret = proc.wait()
        if ret != 0:
            print(f"  ERROR: command {i} failed with code {ret}")
            failed = True

    if failed:
        print(f"  PHASE {phase_id} FAILED")
        return False

    # Verify output
    if output_check.exists():
        print(f"  ✓ Output verified: {output_check}")
        return True
    else:
        # Some outputs take a moment
        time.sleep(1)
        if output_check.exists():
            print(f"  ✓ Output verified (delayed): {output_check}")
            return True
        print(f"  ✗ Output NOT FOUND: {output_check}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="R2 Full Pipeline Runner")
    parser.add_argument("--from-phase", type=int, default=1,
                        help="Start from this phase (skip earlier phases)")
    parser.add_argument("--skip-thematic", action="store_true",
                        help="Skip Phase 5 (A2A thematic open-coding)")
    parser.add_argument("--skip-figures", action="store_true",
                        help="Skip Phase 10 (figures)")
    parser.add_argument("--prereq-only", action="store_true",
                        help="Only check prerequisites, then exit")
    args = parser.parse_args()

    print("=" * 72)
    print("R2 Pipeline Runner")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 72)

    # Check prerequisites
    print("\n--- Prerequisites: A2A annotation status ---")
    if not check_prerequisites():
        print("\nERROR: A2A annotation not complete. Wait for annotation jobs to finish.")
        print("Check: tail -3 logs/annotate_a2a_*.log")
        sys.exit(1)

    if args.prereq_only:
        print("\nAll prerequisites satisfied. Ready to run pipeline.")
        return

    # Run phases
    results = {}
    for phase_id, desc, cmds, out_path in PHASES:
        skip = phase_id < args.from_phase
        if phase_id == 5 and args.skip_thematic:
            print(f"\nPhase 5: SKIPPED (--skip-thematic)")
            continue
        if phase_id == 10 and args.skip_figures:
            print(f"\nPhase 10: SKIPPED (--skip-figures)")
            continue

        ok = run_phase(phase_id, desc, cmds, out_path, skip=skip)
        results[phase_id] = ok
        if not ok and not skip:
            print(f"\nPipeline stopped at Phase {phase_id} due to error.")
            print("Fix the issue, then resume with: --from-phase {phase_id}")
            break

    # Summary
    print(f"\n{'='*72}")
    print("Pipeline Summary")
    print(f"{'='*72}")
    all_passed = True
    for pid, (_, desc, _, _) in enumerate(PHASES, 1):
        status = results.get(pid, None)
        if status is True:
            mark = "✓"
        elif status is False:
            mark = "✗"
            all_passed = False
        elif status is None:
            mark = "—"
        print(f"  Phase {pid}: {mark}  {desc}")

    if all_passed:
        print(f"\nAll phases complete! Next: fill \\tbd{{}} values in paper-acm/acm.tex")
    else:
        print(f"\nSome phases failed or were skipped. Review and retry.")

    print(f"Finished: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
