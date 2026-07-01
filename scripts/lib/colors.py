"""
Institution color palettes and colour-blind safe fallback palette.

All colour assignments are canonicalised here so that every visualisation script
produces consistent institution colours.
"""

# ── ERC-8004 institution palette ──────────────────────────────────────────────

ERC_COLORS: dict[str, str] = {
    "Ethereum Foundation": "#627EEA",
    "MetaMask": "#F6851B",
    "Consensys": "#0077B6",
    "Google": "#34A853",
    "Coinbase": "#0052FF",
    "OpenZeppelin": "#4E5EE4",
    "Hats Protocol": "#5FE3A1",
    "Edge and Node / The Graph Protocol": "#6F4CBA",
    "Nethermind": "#D01F36",
    "Peeramid Labs": "#00B4D8",
    "RnDAO": "#FB8500",
    "Carrefour": "#004494",
    "Mure": "#A855F7",
    "Prophetic": "#EC4899",
    "Sparsity.ai": "#06B6D4",
    "Ethereal.news": "#FF6B35",
    "Unruggable Labs": "#84CC16",
    "Ten.IO": "#14B8A6",
    "Treza Labs": "#F59E0B",
    "Brothers of DeFi Consortium": "#92400E",
    "World Foundation": "#F43F5E",
    "Wivity Inc. / OMA3 DAO": "#64748B",
    "Basement Enterprises": "#65A30D",
    "PIN AI": "#8B5CF6",
    "Olas": "#EC4899",
    "TensorBlock": "#F97316",
    "Freysa / Eternis": "#E11D48",
    "Eigen Labs": "#1E40AF",
    "Deepcrypto": "#059669",
    "Operator Labs": "#7C3AED",
    "Independent": "#505050",
    "Unknown": "#808080",
}

# ── A2A institution palette ───────────────────────────────────────────────────

A2A_COLORS: dict[str, str] = {
    "Google": "#4285F4",
    "Microsoft": "#00A4EF",
    "Cisco": "#1BA0D7",
    "Cisco Systems": "#1BA0D7",
    "Red Hat": "#EE0000",
    "IBM": "#006699",
    "IBM Research": "#006699",
    "Apoco": "#5F6368",
    "CNCF": "#0086FF",
    "Intuit": "#365EBF",
    "Weave": "#9B59B6",
    "AGENIUM": "#2ECC71",
    "Independent": "#505050",
    "Unknown": "#808080",
}

# ── Dark-background institution palette (for white-on-dark figures) ────────────

INST_PALETTE_DARK: dict[str, str] = {
    "Google": "#FF5252",
    "MetaMask": "#FF9F43",
    "Ethereum Foundation": "#748EFF",
    "Coinbase": "#26D9C7",
    "Microsoft": "#FFD93D",
    "AWS": "#82EDB2",
    "Others": "#6B7280",
}

ERC_HUB_DARK = "#FFD700"  # gold
A2A_HUB_DARK = "#DA70D6"  # orchid

# ── Light-background institution palette (for paper figures) ───────────────────

# Re-use colours from the dark palette for the matching institutions.
INST_PALETTE: dict[str, str] = {
    "Google": INST_PALETTE_DARK["Google"],
    "MetaMask": INST_PALETTE_DARK["MetaMask"],
    "Ethereum Foundation": INST_PALETTE_DARK["Ethereum Foundation"],
    "Coinbase": INST_PALETTE_DARK["Coinbase"],
    "Microsoft": INST_PALETTE_DARK["Microsoft"],
    "AWS": INST_PALETTE_DARK["AWS"],
    "Others": "#c0bdb8",  # Independent + Unknown merged
}

# ── Colour-blind friendly fallback (Wong 2011, Nature Methods) ─────────────────

CB_PALETTE: list[str] = [
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7",
    "#56B4E9", "#F0E442", "#000000", "#661100", "#332288",
    "#117733", "#44AA99", "#882255", "#AA4499", "#DDCC77",
]

# ── Project colour card ────────────────────────────────────────────────────────

COLOR_CARD: list[str] = [
    "#a30543", "#f36f43", "#fbda83", "#e9f4a3", "#80cba4", "#4965b0",
]

# ── BERTopic / CryptoBERT semantic labels ──────────────────────────────────────

BERT_SEMANTIC: dict[int, str] = {
    0: "Agent Discourse",
    1: "Task / Message Protocol",
    2: "PR Review Chatter",
    3: "JSON / Proto Spec",
    4: "Contributing / PR Flow",
    5: "Python SDK Samples",
    6: "Versioning",
    7: "UI Assets",
    8: "Voting / Governance",
    9: "Corporate Actors (SAP, LinkedIn)",
    10: "Push Notifications",
    11: "Code of Conduct",
    12: "Partner / Discord Links",
    13: "Gemini AI Review",
    14: "Lint / CI Config",
    15: "UI Polling / Demo",
    16: "Docs / MkDocs",
    17: "OpenAI / Azure",
    18: "Null / None Types",
}

CRYPTO_SEMANTIC: dict[int, str] = {
    0: "Onchain Agent Registry",
    1: "Implementation Scope",
    2: "Trust & Reputation",
    3: "Reviewer / Admin",
    4: "GitHub PR Process",
}
