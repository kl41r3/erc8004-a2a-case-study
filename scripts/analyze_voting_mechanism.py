"""
analyze_voting_mechanism.py

Produces:
  output/voting_mechanism_comparison.png  — two-panel process diagram
  output/voting_stats.json                — key statistics for paper

Evidence sources:
  - data/raw/github_comments_filtered.json  (ERC-8004 lifecycle)
  - data/raw/a2a_gitvote_prs.json           (A2A TSC git-vote PRs)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "output"


# ── helpers ──────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_eip_lifecycle(gh_records):
    """
    Extract ERC-8004 EIP stage transitions from PR metadata.
    Returns list of (date, stage, pr_number, actor) tuples in chronological order.
    """
    stages = []
    for r in gh_records:
        source = r.get("source", "")
        date = (r.get("date") or "")[:10]
        author = r.get("author", "")
        text = r.get("raw_text", "") or ""
        state = r.get("state", "")

        if source == "github_pr_body":
            # PR opened = proposal submitted
            stages.append((date, "PR Submitted", r.get("post_id", ""), author))
        elif source == "github_review" and state == "APPROVED":
            if "eip-review-bot" in author.lower():
                stages.append((date, "Auto-merge (bot)", "", author))
            else:
                stages.append((date, "EIP Editor Approved", "", author))
        elif source == "github_review_comment":
            stages.append((date, "Review Comment", "", author))

    stages.sort(key=lambda x: x[0])
    return stages


def build_gitvote_lifecycle(gitvote_records, pr_number):
    """
    Extract vote lifecycle events for a specific PR.
    Returns list of (date, event_type, actor) tuples.
    """
    pr_recs = [r for r in gitvote_records if r.get("pr_number") == pr_number]
    events = []

    for r in pr_recs:
        date = (r.get("date") or "")[:10]
        author = r.get("author", "")
        text = r.get("text", "") or ""
        record_type = r.get("record_type", "")

        if record_type == "pr_body":
            events.append((date, "PR Opened", author))
        elif "/vote" in text and record_type == "issue_comment" and "bot" not in author.lower():
            if "/cancel-vote" in text:
                events.append((date, "/cancel-vote issued", author))
            else:
                events.append((date, "/vote issued", author))
        elif record_type == "issue_comment" and "bot" in author.lower():
            if "vote created" in text.lower():
                events.append((date, "Vote opened (bot)", "git-vote[bot]"))
            elif "vote closed" in text.lower() or "passed" in text.lower():
                events.append((date, "Vote closed (bot)", "git-vote[bot]"))
        elif record_type == "review" and r.get("state") == "APPROVED":
            events.append((date, "Merged", author))

    events.sort(key=lambda x: x[0])
    return events


# ── drawing helpers ───────────────────────────────────────────────────────────

def draw_process_box(ax, x, y, width, height, text, color, fontsize=8.5):
    rect = mpatches.FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.03", linewidth=1.2,
        edgecolor="#333333", facecolor=color, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight="normal",
            wrap=True, zorder=4, color="#111111",
            multialignment="center")


def draw_arrow(ax, x1, y1, x2, y2, color="#555555"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.2, mutation_scale=12))


def draw_diamond(ax, x, y, width, height, text, color, fontsize=8):
    dx, dy = width / 2, height / 2
    diamond = plt.Polygon(
        [[x, y + dy], [x + dx, y], [x, y - dy], [x - dx, y]],
        closed=True, linewidth=1.2,
        edgecolor="#333333", facecolor=color, zorder=3
    )
    ax.add_patch(diamond)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, zorder=4, color="#111111",
            multialignment="center")


# ── figure ────────────────────────────────────────────────────────────────────

def make_figure():
    fig, (ax_eip, ax_tsc) = plt.subplots(1, 2, figsize=(11, 9))
    fig.patch.set_facecolor("white")

    # ── Palette ───────────────────────────────────────────────────────────────
    C_START   = "#D6EAF8"   # light blue — start/end
    C_PUBLIC  = "#D5F5E3"   # light green — public/open action
    C_EDITOR  = "#FEF9E7"   # light yellow — editor/authority action
    C_GATE    = "#FAD7A0"   # orange — decision gate
    C_TSC     = "#F9EBEA"   # light red — TSC-restricted action
    C_BOT     = "#EBF5FB"   # pale blue — automated/bot

    # ══════════════════════════════════════════════════════════════════════════
    # Left panel: EIP Editor-Approval Flow
    # ══════════════════════════════════════════════════════════════════════════
    ax = ax_eip
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("white")
    ax.set_title("ERC-8004: EIP Editor-Approval\n(Permissionless DAO)",
                 fontsize=11, fontweight="bold", pad=10)

    # Steps (x, y, label, color)
    eip_steps = [
        (0.50, 0.93, "Proposal Submitted\n(PR to ethereum/EIPs)", C_PUBLIC),
        (0.50, 0.80, "Public Deliberation\nEthereum Magicians Forum\n(open to all)", C_PUBLIC),
        (0.50, 0.67, "GitHub PR Review\n(EIP co-authors + community)", C_PUBLIC),
        (0.50, 0.54, "EIP Editor Review\n(lightclient / others)", C_EDITOR),
        (0.50, 0.41, "Editor Decision\n(APPROVE / REQUEST CHANGES)", C_GATE),
        (0.50, 0.27, "Auto-merge\n(eip-review-bot)", C_BOT),
        (0.50, 0.14, "Mainnet Inclusion\n(EIP status = Final)", C_START),
    ]

    W, H = 0.54, 0.085
    for x, y, label, color in eip_steps:
        draw_process_box(ax, x, y, W, H, label, color, fontsize=8)

    for i in range(len(eip_steps) - 1):
        _, y1, _, _ = eip_steps[i]
        _, y2, _, _ = eip_steps[i + 1]
        draw_arrow(ax, 0.50, y1 - H / 2, 0.50, y2 + H / 2)

    # Side note: who can participate
    ax.text(0.03, 0.55, "Anyone\ncan\nparticipate", ha="center", va="center",
            fontsize=7.5, color="#1a6b3c",
            bbox=dict(boxstyle="round,pad=0.2", fc="#D5F5E3", ec="#1a6b3c", lw=0.8))
    ax.annotate("", xy=(0.23, 0.80), xytext=(0.10, 0.68),
                arrowprops=dict(arrowstyle="-", color="#1a6b3c",
                                lw=0.8, linestyle="dashed"))

    # Timeline annotation
    ax.text(0.50, 0.03,
            "ERC-8004: proposal → mainnet in 169 days  |  71 contributors  |  No formal vote",
            ha="center", va="bottom", fontsize=7.5, color="#555555",
            style="italic")

    # ══════════════════════════════════════════════════════════════════════════
    # Right panel: A2A TSC Git-Vote Flow
    # ══════════════════════════════════════════════════════════════════════════
    ax = ax_tsc
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("white")
    ax.set_title("Google A2A: TSC Git-Vote\n(Corporate Hierarchy)",
                 fontsize=11, fontweight="bold", pad=10)

    tsc_steps_main = [
        (0.50, 0.93, "PR Opened\n(any contributor)", C_PUBLIC),
        (0.50, 0.81, "Standard Review\n(community + TSC members)", C_PUBLIC),
        (0.50, 0.69, "Rough Consensus\nReached?", C_GATE),          # diamond
        (0.50, 0.38, "TSC Member Issues /vote\n(triggers git-vote[bot])", C_TSC),
        (0.50, 0.26, "TSC Binding Vote\n(emoji reactions, majority threshold)", C_TSC),
        (0.50, 0.14, "Vote Result:\nPASS → Merge  |  FAIL → Close", C_GATE),
    ]

    W, H = 0.52, 0.085

    # Draw boxes 0,1 (above diamond)
    for x, y, label, color in tsc_steps_main[:2]:
        draw_process_box(ax, x, y, W, H, label, color, fontsize=8)
    draw_arrow(ax, 0.50, tsc_steps_main[0][1] - H/2,
                   0.50, tsc_steps_main[1][1] + H/2)
    draw_arrow(ax, 0.50, tsc_steps_main[1][1] - H/2,
                   0.50, tsc_steps_main[2][1] + H*0.55)

    # Diamond at step 2
    draw_diamond(ax, 0.50, 0.69, 0.36, 0.10,
                 "Rough\nconsensus?", C_GATE, fontsize=8)

    # YES branch → merge (right side)
    draw_process_box(ax, 0.82, 0.58, 0.28, 0.075,
                     "Merged\n(standard review)", C_BOT, fontsize=7.5)
    ax.annotate("", xy=(0.82, 0.58 + 0.075/2), xytext=(0.68, 0.69),
                arrowprops=dict(arrowstyle="-|>", color="#27ae60", lw=1.2,
                                mutation_scale=11))
    ax.text(0.76, 0.675, "YES", ha="center", fontsize=7.5, color="#27ae60",
            fontweight="bold")

    # NO branch → escalate
    draw_arrow(ax, 0.50, 0.69 - 0.05,
                   0.50, tsc_steps_main[3][1] + H/2)
    ax.text(0.56, 0.52, "NO\n(contested)", ha="left", fontsize=7.5,
            color="#c0392b", fontweight="bold")

    # Draw steps 3,4,5
    for x, y, label, color in tsc_steps_main[3:]:
        draw_process_box(ax, x, y, W, H, label, color, fontsize=8)
    for i in range(3, len(tsc_steps_main) - 1):
        _, y1, _, _ = tsc_steps_main[i]
        _, y2, _, _ = tsc_steps_main[i + 1]
        draw_arrow(ax, 0.50, y1 - H/2, 0.50, y2 + H/2)

    # Side note: TSC restriction
    ax.text(0.10, 0.32, "TSC\nmembers\nonly", ha="center", va="center",
            fontsize=7.5, color="#922b21",
            bbox=dict(boxstyle="round,pad=0.2", fc="#F9EBEA", ec="#922b21", lw=0.8))
    ax.annotate("", xy=(0.24, 0.38), xytext=(0.15, 0.35),
                arrowprops=dict(arrowstyle="-", color="#922b21",
                                lw=0.8, linestyle="dashed"))

    # Off-platform escalation note
    ax.text(0.50, 0.48,
            "★ contested decisions may migrate\n    to TSC calls / Discord (off-platform)",
            ha="center", fontsize=7.2, color="#7d6608",
            bbox=dict(boxstyle="round,pad=0.25", fc="#FEF9E7",
                      ec="#d4ac0d", lw=0.8, alpha=0.9))

    ax.text(0.50, 0.03,
            "A2A: 38 /vote commands on 32 threads  |  826 contributors  |  TSC-only binding votes",
            ha="center", va="bottom", fontsize=7.5, color="#555555",
            style="italic")

    plt.tight_layout(pad=2.0)
    out_path = OUTPUT / "voting_mechanism_comparison.png"
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Figure saved → {out_path}")
    return out_path


# ── statistics ────────────────────────────────────────────────────────────────

def compute_voting_stats(gh_records, gitvote_records):
    """Return a dict of key statistics for both mechanisms."""
    # ERC-8004
    eip_approvals = [r for r in gh_records
                     if r.get("source") == "github_review"
                     and r.get("state") == "APPROVED"
                     and "eip-review-bot" not in (r.get("author","") or "").lower()]
    eip_bot_merges = [r for r in gh_records
                      if r.get("source") == "github_review"
                      and "eip-review-bot" in (r.get("author","") or "").lower()]

    # A2A GitVote
    pr_831 = [r for r in gitvote_records if r.get("pr_number") == 831]
    pr_1206 = [r for r in gitvote_records if r.get("pr_number") == 1206]

    vote_commands = [r for r in gitvote_records
                     if "/vote" in (r.get("text","") or "")
                     and "bot" not in (r.get("author","") or "").lower()]
    cancel_commands = [r for r in gitvote_records
                       if "/cancel-vote" in (r.get("text","") or "")
                       and "bot" not in (r.get("author","") or "").lower()]
    bot_msgs = [r for r in gitvote_records
                if "bot" in (r.get("author","") or "").lower()]

    stats = {
        "erc8004": {
            "human_approvals": len(eip_approvals),
            "approvers": list({r.get("author") for r in eip_approvals}),
            "bot_auto_merges": len(eip_bot_merges),
            "formal_vote_mechanism": False,
            "decision_venue": "GitHub PR + Ethereum Magicians forum",
            "open_to_all": True,
        },
        "a2a": {
            "gitvote_prs_total": 2,
            "pr_831_outcome": "PASSED (merged)",
            "pr_1206_outcome": "CLOSED (superseded by #1358)",
            "vote_commands_issued": len(vote_commands),
            "cancel_vote_commands": len(cancel_commands),
            "bot_messages": len(bot_msgs),
            "pr_831_participants": len({r.get("author") for r in pr_831
                                        if "bot" not in (r.get("author","") or "").lower()}),
            "pr_1206_participants": len({r.get("author") for r in pr_1206
                                         if "bot" not in (r.get("author","") or "").lower()}),
            "formal_vote_mechanism": True,
            "tsc_binding": True,
            "decision_venue": "GitHub PR + TSC git-vote (+ Discord/TSC call for contested cases)",
            "open_to_all": False,
        },
    }
    return stats


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    gh_records = load_json(DATA_RAW / "github_comments_filtered.json")
    gitvote_records = load_json(DATA_RAW / "a2a_gitvote_prs.json")

    print("Computing statistics...")
    stats = compute_voting_stats(gh_records, gitvote_records)

    stats_path = OUTPUT / "voting_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved → {stats_path}")

    print("\n── ERC-8004 Voting Stats ──")
    erc = stats["erc8004"]
    print(f"  Human approvals: {erc['human_approvals']}")
    print(f"  Approvers: {erc['approvers']}")
    print(f"  Bot auto-merges: {erc['bot_auto_merges']}")
    print(f"  Formal vote mechanism: {erc['formal_vote_mechanism']}")
    print(f"  Decision venue: {erc['decision_venue']}")

    print("\n── Google A2A Voting Stats ──")
    a2a = stats["a2a"]
    print(f"  GitVote PRs: {a2a['gitvote_prs_total']}")
    print(f"  PR #831 outcome: {a2a['pr_831_outcome']}")
    print(f"  PR #1206 outcome: {a2a['pr_1206_outcome']}")
    print(f"  /vote commands issued: {a2a['vote_commands_issued']}")
    print(f"  /cancel-vote commands: {a2a['cancel_vote_commands']}")
    print(f"  Bot messages in voted PRs: {a2a['bot_messages']}")
    print(f"  PR #831 participants (human): {a2a['pr_831_participants']}")
    print(f"  PR #1206 participants (human): {a2a['pr_1206_participants']}")
    print(f"  TSC binding only: {a2a['tsc_binding']}")

    print("\nGenerating figure...")
    make_figure()
    print("\nDone.")


if __name__ == "__main__":
    main()
