"""
Canonical model registry, backend configurations, bot list, and institution patterns.

All model references throughout the codebase should use the canonical MODEL_ID
(not the legacy short key) for filesystem paths.
"""

import os

# ── Canonical model IDs ────────────────────────────────────────────────────────

MODEL_IDS = {
    "deepseek": "deepseek-v4-flash",
    "glm": "glm-4-plus",
    "moonshot": "moonshot-v1-auto",
}

# Canonical IDs in iteration order
CANONICAL_MODELS = ["deepseek-v4-flash", "glm-4-plus", "moonshot-v1-auto"]

# Legacy short keys → canonical ID (for backward compatibility in CLI args)
LEGACY_KEYS = {
    "deepseek": "deepseek-v4-flash",
    "glm": "glm-4-plus",
    "kimi": "moonshot-v1-auto",
    "moonshot": "moonshot-v1-auto",
}

# ── Backend configurations ─────────────────────────────────────────────────────


def _env(key: str) -> str:
    return os.environ.get(key, "")


# R2 annotation backends (5-field schema, temperature=0.0, max_tokens=1024)
BACKENDS_ANNOTATION: dict[str, dict] = {
    "deepseek-v4-flash": {
        "name": "DeepSeek-V4-Flash",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_key": _env("DEEPSEEK_API_KEY"),
        "max_tokens": 1024,
        "temperature": 0.0,
        "sleep": 0.1,
    },
    "glm-4-plus": {
        "name": "GLM-4-Plus",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus",
        "api_key_env": "GLM_API_KEY",
        "api_key": _env("GLM_API_KEY"),
        "max_tokens": 1024,
        "temperature": 0.0,
        "sleep": 0.2,
    },
    "moonshot-v1-auto": {
        "name": "Moonshot-v1-Auto",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto",
        "api_key_env": "KIMI_API_KEY",
        "api_key": _env("KIMI_API_KEY"),
        "max_tokens": 1024,
        "temperature": 0.0,
        "sleep": 0.15,
    },
}

# Cross-round backends (3-field schema, lower max_tokens, core=True)
# Used for 3-model × 3-round test-retest self-consistency (R2 robustness appendix)
BACKENDS_CROSS_ROUND: dict[str, dict] = {
    "deepseek-v4-flash": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_key": _env("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "max_tokens": 512,
        "temperature": 0.0,
        "sleep": 0.05,
        "core": True,
    },
    "glm-4-plus": {
        "api_key_env": "GLM_API_KEY",
        "api_key": _env("GLM_API_KEY"),
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus",
        "max_tokens": 256,
        "temperature": 0.0,
        "sleep": 0.05,
        "core": True,
    },
    "moonshot-v1-auto": {
        "api_key_env": "KIMI_API_KEY",
        "api_key": _env("KIMI_API_KEY"),
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto",
        "max_tokens": 256,
        "temperature": 0.0,
        "sleep": 0.0,
        "core": True,
    },
}

# Thematic-LM backends (no temperature/max_tokens — API defaults)
BACKENDS_THEMATIC: dict[str, dict] = {
    "deepseek-v4-flash": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_key": _env("DEEPSEEK_API_KEY"),
    },
    "glm-4-plus": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-plus",
        "api_key_env": "GLM_API_KEY",
        "api_key": _env("GLM_API_KEY"),
    },
    "moonshot-v1-auto": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-auto",
        "api_key_env": "KIMI_API_KEY",
        "api_key": _env("KIMI_API_KEY"),
    },
}

# ── Bot exclusion list ─────────────────────────────────────────────────────────

BOTS: set[str] = {
    "github-actions[bot]",
    "eip-review-bot",
    "dependabot[bot]",
    "gemini-code-assist[bot]",
    "git-vote[bot]",
    "google-cla[bot]",
    "actions-user",
    "github-actions",
    "dependabot",
}


def is_bot(author: str) -> bool:
    """Check whether an author handle is a known bot account."""
    if not author:
        return True
    return author in BOTS or author.endswith("[bot]") or author.endswith("-bot")


def canonical_handle(raw: str) -> str:
    """Normalise an author handle to a canonical form."""
    if not raw:
        return "unknown"
    return raw.strip().strip("@").lower()


# ── Institution patterns (for enrich_institutions.py) ──────────────────────────

INSTITUTION_PATTERNS: list[tuple[str, str]] = [
    (r"\bmetamask\b", "MetaMask"),
    (r"\bconsenSys\b|\bconsensys\b", "ConsenSys"),
    (r"\bethereumfoundation\b|\bethereum foundation\b|\bef\b|\befdn\b", "Ethereum Foundation"),
    (r"\bgoogle\b", "Google"),
    (r"\bmicrosoft\b", "Microsoft"),
    (r"\bcoinbase\b", "Coinbase"),
    (r"\bopenai\b", "OpenAI"),
    (r"\banthropic\b", "Anthropic"),
    (r"\bprotocol labs\b", "Protocol Labs"),
    (r"\boasis\b", "Oasis"),
    (r"\bgnosisguild\b|\bgnosis guild\b|\bgnosis\b", "Gnosis"),
    (r"\bsafe\b", "Safe"),
    (r"\barkham\b", "Arkham"),
    (r"\bzk ?sync\b|\bmatter labs\b", "Matter Labs"),
    (r"\bstarkware\b", "StarkWare"),
    (r"\boptimism\b", "Optimism"),
    (r"\barbitrum\b|\boffchain labs\b", "Offchain Labs"),
    (r"\bpolygon\b", "Polygon"),
    (r"\bchainlink\b", "Chainlink"),
    (r"\bender labs\b|\bender\b", "Ender Labs"),
    (r"\balchemy\b", "Alchemy"),
    (r"\binfura\b", "Infura"),
    (r"\buniversity\b|\buniv\b|\bcollege\b|\bacademia\b|\bphd\b", "Academia"),
    (r"\bindependent\b|\bfreelance\b|\bself.?employed\b", "Independent"),
]

# ── ERC-8004 core lifecycle PRs ────────────────────────────────────────────────

ERC8004_CORE_PRS: dict[int, str] = {
    1170: "Add ERC: Trustless Agents (initial submission)",
    1244: "Update ERC-8004: Move to Review",
    1248: "Update ERC-8004: Add Requires field",
    1458: "Update ERC-8004: Update erc-8004.md",
    1462: "Update ERC-8004: Update erc-8004.md (typos)",
    1470: "Update ERC-8004: Move to Draft",
    1472: "Update ERC-8004: align metadataValue to bytes",
    1477: "Update ERC-8004: add co-author (Onchain Metadata; see PR #1237)",
    1488: "Update ERC-8004: Updates from community feedback",
}
