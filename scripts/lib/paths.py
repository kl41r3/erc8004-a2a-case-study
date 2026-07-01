"""
Single source of truth for all filesystem paths.

Import from scripts as:  from lib.paths import ROOT, DATA_RAW, ...
"""

from pathlib import Path

# Workspace root (scripts/lib/paths.py → scripts/lib/ → scripts/ → workspace/)
ROOT = Path(__file__).resolve().parent.parent.parent

# ── Data paths ─────────────────────────────────────────────────────────────────

DATA_RAW = ROOT / "data" / "raw"
DATA_RAW_R2 = DATA_RAW / "r2"
DATA_RAW_R2_TIER1 = DATA_RAW_R2 / "tier1"
DATA_RAW_R2_TIER2 = DATA_RAW_R2 / "tier2"

DATA_ANNOTATED_R1 = ROOT / "data" / "annotated" / "r1"
DATA_ANNOTATED_R1_RECORDS = DATA_ANNOTATED_R1 / "annotated_records.json"
DATA_ANNOTATED_R1_PROFILES = DATA_ANNOTATED_R1 / "author_profiles.json"

DATA_ANNOTATED_R2_CROSS_MODEL = ROOT / "data" / "annotated" / "r2" / "cross-model"
DATA_ANNOTATED_R2_CONSENSUS = DATA_ANNOTATED_R2_CROSS_MODEL / "consensus"
DATA_ANNOTATED_R2_THEMATIC = DATA_ANNOTATED_R2_CROSS_MODEL / "thematic"
DATA_ANNOTATED_R2_VALIDATION = DATA_ANNOTATED_R2_CROSS_MODEL / "validation"
DATA_ANNOTATED_R2_ERC = DATA_ANNOTATED_R2_CROSS_MODEL / "erc"
DATA_ANNOTATED_R2_A2A = DATA_ANNOTATED_R2_CROSS_MODEL / "a2a"

DATA_ANNOTATED_R2_CROSS_ROUND = ROOT / "data" / "annotated" / "r2" / "cross-round"
DATA_ANNOTATED_R2_CROSS_ROUND_ERC = DATA_ANNOTATED_R2_CROSS_ROUND / "erc"
DATA_ANNOTATED_R2_CROSS_ROUND_A2A = DATA_ANNOTATED_R2_CROSS_ROUND / "a2a"

# ── Analysis paths ─────────────────────────────────────────────────────────────

ANALYSIS_DIR = ROOT / "analysis"

ANALYSIS_METRICS = ANALYSIS_DIR / "metrics"
ANALYSIS_METRICS_R1 = ANALYSIS_METRICS / "r1"
ANALYSIS_METRICS_R2 = ANALYSIS_METRICS / "r2"

ANALYSIS_ND = ANALYSIS_DIR / "network_discourse"
ANALYSIS_ND_R1 = ANALYSIS_ND / "r1"
ANALYSIS_ND_R1_DNA = ANALYSIS_ND_R1 / "dna"
ANALYSIS_ND_R1_SS = ANALYSIS_ND_R1 / "sociosemantic"
ANALYSIS_ND_R2 = ANALYSIS_ND / "r2"
ANALYSIS_ND_R2_DNA = ANALYSIS_ND_R2 / "dna"
ANALYSIS_ND_R2_SS = ANALYSIS_ND_R2 / "sociosemantic"

ANALYSIS_TD = ANALYSIS_DIR / "topic_discovery"
ANALYSIS_TD_R1 = ANALYSIS_TD / "r1"
ANALYSIS_TD_R1_THEMATIC = ANALYSIS_TD_R1 / "thematic_lm"
ANALYSIS_TD_R1_COMPARATIVE = ANALYSIS_TD_R1 / "comparative_discourse"
ANALYSIS_TD_R1_CRYPTOBERT = ANALYSIS_TD_R1 / "crypto_bert"
ANALYSIS_TD_R2 = ANALYSIS_TD / "r2"
ANALYSIS_TD_R2_CROSS_MODEL = ANALYSIS_TD_R2 / "cross-model"
ANALYSIS_TD_R2_CROSS_MODEL_THEMATIC = ANALYSIS_TD_R2_CROSS_MODEL / "thematic_lm"
ANALYSIS_TD_R2_CROSS_MODEL_COMPARATIVE = ANALYSIS_TD_R2_CROSS_MODEL / "comparative_discourse"
ANALYSIS_TD_R2_CROSS_ROUND = ANALYSIS_TD_R2 / "cross-round"

# ── Output paths ───────────────────────────────────────────────────────────────

OUTPUT_DIR = ROOT / "output"
OUTPUT_FIGURES = OUTPUT_DIR / "figures"
OUTPUT_INTERACTIVE = OUTPUT_DIR / "interactive"
OUTPUT_FLOWCHART = OUTPUT_DIR / "flow-chart"

# ── Paper paths ────────────────────────────────────────────────────────────────

PAPER_ACM = ROOT / "paper-acm"
PAPER_ACM_FIG = PAPER_ACM / "fig"

# ── Raw data file paths ────────────────────────────────────────────────────────

# R1 raw data
RAW_FORUM_POSTS = DATA_RAW / "forum_posts.json"
RAW_GITHUB_COMMENTS_FILTERED = DATA_RAW / "github_comments_filtered.json"
RAW_A2A_COMMITS = DATA_RAW / "a2a_commits.json"
RAW_A2A_ISSUES = DATA_RAW / "a2a_issues.json"
RAW_A2A_PRS = DATA_RAW / "a2a_prs.json"
RAW_A2A_DISCUSSIONS = DATA_RAW / "a2a_discussions.json"
RAW_A2A_GITVOTE_PRS = DATA_RAW / "a2a_gitvote_prs.json"
RAW_A2A_MANIFEST = DATA_RAW / "a2a_manifest.json"
RAW_FORUM_MANIFEST = DATA_RAW / "manifest.json"

# R1 profiles
RAW_PROFILES_FORUM = DATA_RAW / "profiles_forum.json"
RAW_PROFILES_GITHUB = DATA_RAW / "profiles_github.json"
RAW_MANUAL_INSTITUTIONS = DATA_RAW / "manual_institutions.json"

# ── Key analysis file paths ────────────────────────────────────────────────────

# R1 metrics
METRICS_R1_STRUCTURAL = ANALYSIS_METRICS_R1 / "structural_metrics.csv"
METRICS_R1_CORE_CONTRIBUTORS = ANALYSIS_METRICS_R1 / "core_contributors.csv"
METRICS_R1_CROSS_CASE_OVERLAP = ANALYSIS_METRICS_R1 / "cross_case_overlap.csv"
METRICS_R1_NETWORK_NODES_ERC = ANALYSIS_METRICS_R1 / "network_nodes_erc8004.csv"
METRICS_R1_NETWORK_EDGES_ERC = ANALYSIS_METRICS_R1 / "network_edges_erc8004.csv"
METRICS_R1_NETWORK_NODES_A2A = ANALYSIS_METRICS_R1 / "network_nodes_a2a.csv"
METRICS_R1_NETWORK_EDGES_A2A = ANALYSIS_METRICS_R1 / "network_edges_a2a.csv"
METRICS_R1_NETWORK_NODES_A2A_TOP50 = ANALYSIS_METRICS_R1 / "network_nodes_a2a_top50.csv"
METRICS_R1_NETWORK_EDGES_A2A_TOP50 = ANALYSIS_METRICS_R1 / "network_edges_a2a_top50.csv"
METRICS_R1_VERIFICATION_CHECKLIST = ANALYSIS_METRICS / "institution_verification_checklist.csv"

# R2 metrics
METRICS_R2_STRUCTURAL = ANALYSIS_METRICS_R2 / "structural_metrics.csv"
METRICS_R2_NETWORK_NODES_ERC = ANALYSIS_METRICS_R2 / "network_erc_nodes.csv"
METRICS_R2_NETWORK_EDGES_ERC = ANALYSIS_METRICS_R2 / "network_erc_edges.csv"
METRICS_R2_NETWORK_NODES_A2A = ANALYSIS_METRICS_R2 / "network_a2a_nodes.csv"
METRICS_R2_NETWORK_EDGES_A2A = ANALYSIS_METRICS_R2 / "network_a2a_edges.csv"
METRICS_R2_NETWORK_NODES_A2A_TOP50 = ANALYSIS_METRICS_R2 / "network_a2a_top50_nodes.csv"
METRICS_R2_NETWORK_EDGES_A2A_TOP50 = ANALYSIS_METRICS_R2 / "network_a2a_top50_edges.csv"
METRICS_R2_AGENT_ERC_UNIVERSE = ANALYSIS_METRICS_R2 / "agent_erc_universe.csv"

# R2 consensus
CONSENSUS_ERC = DATA_ANNOTATED_R2_CONSENSUS / "erc_annotations.json"
CONSENSUS_A2A = DATA_ANNOTATED_R2_CONSENSUS / "a2a_annotations.json"
CONSENSUS_STATS = DATA_ANNOTATED_R2_CONSENSUS / "consensus_stats.json"

# R2 cross-round
CROSS_ROUND_ERC = DATA_ANNOTATED_R2_CROSS_ROUND / "erc_cross_consensus.json"
CROSS_ROUND_A2A = DATA_ANNOTATED_R2_CROSS_ROUND / "a2a_cross_consensus.json"
