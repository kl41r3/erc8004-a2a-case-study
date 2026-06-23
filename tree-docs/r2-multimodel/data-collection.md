# R2 — DAO 数据扩充：采集报告

**日期:** 2026-06-14 → 2026-06-15
**分支:** `research/round-2-update`
**状态:** ✅ 采集完成，全部校验

## 1. 问题与决策

Round-1 DAO 侧（ERC-8004）仅 149 条记录 vs 公司侧（Google A2A）6545 条，比例 1:44。诊断发现：

- **149 不是抓漏**：`data/raw/filter_log.json` 显示 GitHub 侧 36 条按编号直抓 9 个 lifecycle PR、`dropped:0`，论坛主帖 113 条当时完整（抓取日期 2026-03-10）。
- **6545 是全生态运营流量**：A2A 正式治理（GitVote）仅 2 次投票，差距主要源于"单 ERC 审议 vs 整仓库运营"的量纲不对等。

**决策**（用户确认）：集群 + 补全，分成 Tier 1（ERC-8004 本体）与 Tier 2（agent 标准化集群）两份干净独立的成果。论坛 + GitHub 全口径。只采集，不做处理。

## 2. 纳入判据

从 ethereum-magicians.org 的 17 个 agent/AI 搜索词去重，得到 59 个候选线程。纳入仅需满足两条：

1. **流程合法**：是正式 ERC/EIP 提案线程（有 ERC 编号，或 "Draft ERC / Add ERC / Pre-ERC" 形式提交）。
2. **代际一致**：创建于 ERC-8004 时代（`≥2025-08-01`），与 A2A 活跃窗口同期。

排除：过时代际 AI-NFT（7662/7857/7860/18197，2024-2025初）、非正式 ERC 讨论帖（ReceiptOS/OSRB/Panini/LAS）。

**抽样框**：`analysis/r2_agent_erc_universe.csv`（60 行，含 tier/include/deliberative/erc/topic_id/posts/created/title/reason 全字段）。

---

## 3. Tier 1 — ERC-8004 本体（锚定案例）

### 3a. 论坛：8 个线程，227 帖

| Topic ID | 标题 | 帖数 | 日期 | 理由 |
|---|---|---|---|---|
| 25098 | ERC-8004: Trustless Agents | 207 | 2025-08-14 | 主提案帖（round-1 仅 113，补全至 207） |
| 28562 | ERC-8004 in production: per-collection factory vs chain singleton | 8 | 2026-05-19 | 生产部署讨论 |
| 25487 | Trustless Agents (ERC-8004) Call #1 | 3 | 2025-09-23 | 治理例会（正式事件） |
| 28000 | ERC-8004 Launch Day #1 | 3 | 2026-03-16 | 上线日活动 |
| 26029 | Trustless Agents (ERC-8004) Call #3 | 3 | 2025-11-12 | 治理例会 |
| 28555 | Trustless Agents Plus (TAP) | 1 | 2026-05-18 | 碎片整合倡议 |
| 25434 | ERC-8004 Extension: Verifiable AI System Transparency | 1 | 2025-09-13 | 扩展提案 |
| 25789 | Trustless Agents (ERC-8004) Call #2 | 1 | 2025-10-22 | 治理例会 |

完整性：8/8 topics complete，`scraped == stream_length` 逐帖校验。主帖 25098 从 round-1 的 113 帖补全至 207 帖——缺失的 94 帖全部是 2026-03-15 之后的新帖（非抓取 bug，是时间增长）。

### 3b. GitHub：9 个 Lifecycle PR，37 条

ERC-8004 在 `ethereum/ERCs` 仓库中修改 `ERCS/erc-8004.md` 或变更其 lifecycle 状态的 9 个 PR，按编号直抓：

| PR | 标题 | 记录 | 状态 |
|---|---|---|---|
| #1170 | Add ERC: Trustless Agents (initial submission) | 14 | closed |
| #1244 | Update ERC-8004: Move to Review | 7 | closed |
| #1248 | Update ERC-8004: Add Requires field | 2 | open |
| #1458 | Update ERC-8004: Update erc-8004.md | 3 | closed |
| #1462 | Update ERC-8004: Update erc-8004.md (typos) | 3 | closed |
| #1470 | Update ERC-8004: Move to Draft | 1 | closed |
| #1472 | Update ERC-8004: align metadataValue to bytes | 2 | open |
| #1477 | Update ERC-8004: add co-author | 3 | open |
| #1488 | Update ERC-8004: Updates from community feedback | 2 | closed |

每条 PR 抓取：PR body + issue comments + review comments + reviews (with body text)。共 37 条记录。

**Tier 1 合计：227 (forum) + 37 (GitHub) = 264 条**

---

## 4. Tier 2 — Agent 标准化集群（扩展总体）

### 4a. 论坛：42 个 ERC 线程，792 帖

纳入的 42 个 ERC 均为同期（≥2025-08）、经正式 ERC 流程的 agent/AI 标准化提案。按议质量（帖数）排列：

| ERC | Topic ID | 帖数 | 日期 | 议题 |
|---|---|---|---|---|
| 8183 | 27902 | 305 | 2026-03-04 | Agentic Commerce |
| 8274 | 28083 | 115 | 2026-03-26 | AI Inference Proof Verification |
| 8210 | 28097 | 44 | 2026-03-28 | Agent Assurance |
| 8240 | 28322 | 40 | 2026-04-22 | Trust Infrastructure for Agents and Assets |
| 8126 | 27445 | 39 | 2026-01-15 | AI Agent Verification |
| 8217 | 28339 | 25 | 2026-04-24 | Agent NFT Identity Bindings |
| 8203 | 28041 | 20 | 2026-03-22 | Agent Off-Chain Conditional Settlement |
| 8263 | 28577 | 20 | 2026-05-20 | Onchain Proof Layer for AI Agents |
| 8239 | 28335 | 18 | 2026-04-23 | Agent Skill Registry |
| 8257 | 28457 | 15 | 2026-05-06 | Agent Tool Registry |
| 8294 | 28669 | 14 | 2026-05-31 | Validation Network for ERC-8004 |
| 8275 | 28622 | 13 | 2026-05-26 | Agent Service Discovery & Escrow Payments |
| 8259 | 28521 | 13 | 2026-05-13 | AI Agent Identity, Reputation & Threat Registry |
| 8273 | 28617 | 12 | 2026-05-26 | Attestation-Gated Agentic Actions |
| 8118 | 27402 | 12 | 2026-01-09 | Agent Authorization |
| 8196 | 27987 | 10 | 2026-03-14 | AI Agent Authenticated Wallet |
| 8226 | 28208 | 8 | 2026-04-12 | Regulated Agent Mandate |
| 8150 | 27665 | 8 | 2026-02-06 | ZK Agent Payment Verification |
| 8220 | 28162 | 7 | 2026-04-07 | Onchain AI Governance |
| 8033 | 25638 | 6 | 2025-09-30 | Agent Council Oracles |
| 28785 | 28785 | 6 | 2026-06-13 | Draft: AI Agent Execution (no ERC # yet) |
| 28670 | 28670 | 5 | 2026-06-01 | Draft: Permission Registry (no ERC # yet) |
| 8171 | 27967 | 4 | 2026-03-12 | Token Bound Account (Agent Registry) |
| 8184 | 28012 | 4 | 2026-03-17 | Payment Channels with Signed Vouchers |
| 8041 | 25656 | 3 | 2025-10-03 | Fixed-Supply Agent NFT Collections |
| 8162 | 27751 | 3 | 2026-02-16 | Agent Subscription Protocol |
| 8181 | 27512 | 3 | 2026-01-19 | Self-Sovereign Agent NFTs |
| 27949 | 27949 | 3 | 2026-03-11 | Pre-ERC: Off-Chain Conditional Settlement (no ERC #) |
| 8001 | 24989 | 2 | 2025-08-02 | Secure Intents for Autonomous Agent Coordination |
| 8183 | 27970 | 2 | 2026-03-12 | ERC-8183 production lessons (same ERC, diff post) |
| 28010 | 28010 | 2 | 2026-03-17 | ERC Discussion: Agent Alias Metadata (no ERC #) |
| 8122 | 27405 | 1 | 2026-01-09 | Minimal Agent Registry |
| 8160 | 27727 | 1 | 2026-02-12 | Primary Agent Registry |
| 8259 | 28473 | 1 | 2026-05-08 | AI Agent Identity & Threat Registry (draft v1) |
| 28404 | 28404 | 1 | 2026-04-30 | Draft: Autonomous State Gateway (no ERC #) |
| 28152 | 28152 | 1 | 2026-04-06 | Formal Governance Proof Registry (no ERC #) |
| 8165 | 27773 | 1 | 2026-02-19 | Agentic On-Chain Operation Interface |
| 8166 | 27772 | 1 | 2026-02-19 | Shared Sequencer Interface for Agent L2s |
| 8264 | 28584 | 1 | 2026-05-21 | AI Agent Memory Access Rights |
| 8242 | 28394 | 1 | 2026-04-28 | H3 Spatial Identity Extension |
| 8107 | 27200 | 1 | 2025-12-17 | ENS Trust Registry for Agent Coordination |
| 28070 | 28070 | 1 | 2026-03-25 | Pre-ERC: Agent Service Sessions (no ERC #) |

完整性：42/42 topics complete，逐帖 `scraped == stream_length` 校验通过。单帖线程（posts=1）仅进结构指标（提案存活率），不做审议分析。

### 4b. GitHub：按 ERC 发现 PR，657 条

**发现方法**（每个 ERC 独立执行，provenance 记录在 manifest）：
1. **Method A (主)**：`GET /repos/ethereum/ERCs/commits?path=ERCS/erc-{N}.md` → 对每个 commit 调 `/commits/{sha}/pulls` 反查关联 PR。
2. **Method B (兜底)**：`GET /search/issues?q=repo:ethereum/ERCs+type:pr+ERC-{N}` → 对每个候选 `/pulls/{n}/files` 确认包含 `ERCS/erc-{N}.md`。

每条 PR 抓取：PR body + issue comments + review comments + reviews。

| ERC | Topic | PR 列表 | 记录 |
|---|---|---|---|
| 8126 | 27445 | #1475, #1598, #1605, #1608, #1691, #1734, #1769 | 125 |
| 8274 | 28083 | #1771 | 12 |
| 8033 | 25638 | #1226, #1422 | 54 |
| 8001 | 24989 | #1149, #1243, #1374, #1375, #1408 | 50 |
| 8196 | 27987 | #1606, #1702, #1797 | 47 |
| 8257 | 28457 | #1723, #1809 | 38 |
| 8122 | 27405 | #1463 | 34 |
| 8226 | 28208 | #1679 | 26 |
| 8041 | 25656 | #1237, #1583 | 22 |
| 8118 | 27402 | #1450 | 19 |
| 8242 | 28394 | #1634 | 19 |
| 8183 | 27902+27970 | #1581, #1601, #1732 | 18 |
| 8181 | 27512 | #1579 | 18 |
| 8210 | 28097 | #1632 | 16 |
| 8263 | 28577 | #1748 | 15 |
| 8166 | 27772 | #1550, #1615 | 15 |
| 8239 | 28335 | #1704 | 14 |
| 8217 | 28339 | #1648 | 13 |
| 8273 | 28617 | #1770 | 6 |
| 8259 | 28521+28473 | #1730 | 6 |
| 8294 | 28669 | #1808 | 6 |
| 8275 | 28622 | #1774 | 9 |
| 8264 | 28584 | #1752 | 9 |
| 8162 | 27751 | #1545 | 9 |
| 8184 | 28012 | #1592 | 7 |
| 8240 | 28322 | #1705 | 7 |
| 8203 | 28041 | #1614 | 7 |
| 8220 | 28162 | #1656 | 7 |
| 8107 | 27200 | #1412 | 7 |
| 8160 | 27727 | #1536 | 4 |
| 8165 | 27773 | #1549 | 6 |
| 8171 | 27967 | #1559 | 6 |
| 8150 | 27665 | #1520 | 6 |

**7 个 ERC 无 PR**：均为无编号的 Draft/Pre-ERC 帖（28785/28670/27949/28010/28404/28152/28070）——论坛先放草案，尚未提交仓库 PR。经核对无误杀，forum-only 正确且是 DAO 低门槛特征的证据。

**已知特例**：
- **ERC-8184 编号漂移**：论坛帖 28012 自称 "ERC-8184"，但仓库 PR #1592 实际创建了 `erc-8190.md`（同名 "Payment Channels with Signed Vouchers"）。已显式标注并补抓 #1592（7 条），记录带 `_note` 字段说明漂移。
- **ERC-8183 / ERC-8259 各有两个论坛帖**：两帖均保留（确为不同讨论），GitHub PR 共享，已去重 24 条。

**Tier 2 合计：792 (forum) + 657 (GitHub) = 1449 条**

---

## 5. 排除清单（10 线程，31 帖）

| Topic | 帖数 | 日期 | 标题 | 排除原因 |
|---|---|---|---|---|
| 22391 | 8 | 2025-01-02 | ERC-7857: NFT Standard for AI Agents | pre-ERC-8004 代际 |
| 28103 | 5 | 2026-03-29 | ReceiptOS — verifiable execution receipts | 非正式 ERC 提案 |
| 19371 | 4 | 2024-03-26 | ERC-7662: AI Agent NFTs | pre-ERC-8004 代际 |
| 22502 | 4 | 2025-01-12 | ERC-7860 AgentNFT Extension | pre-ERC-8004 代际 |
| 26808 | 4 | 2025-12-01 | OSRB: AGI Benchmark | 非正式 ERC 提案 |
| 28628 | 2 | 2026-05-27 | Panini Standard v1.0 | 非正式 ERC 提案 |
| 28737 | 1 | 2026-06-06 | Execution receipts for AI agents | 非正式 ERC 提案 |
| 25088 | 1 | 2025-08-13 | Liquid Agent Standard (LAS) | 非正式 ERC 提案 |
| 26822 | 1 | 2025-12-01 | AI Agent Identity Verification | 非正式 ERC 提案 |
| 18197 | 1 | 2024-01-18 | On-chain Autonomous AI Agent NFT | pre-ERC-8004 代际 |

---

## 6. 数据架构与校验

```
data/raw/r2/
├── CHECKSUMS.json                     # SHA-256 (8 raw files)
├── tier1/
│   ├── erc8004_forum.json             # 227 帖 (8 threads)
│   ├── erc8004_github.json            # 37 条 (9 lifecycle PRs)
│   ├── tier1_forum_manifest.json      # {topic_id: scraped/stream/official, complete}
│   └── tier1_github_manifest.json     # {prs, by_source, total_records}
└── tier2/
    ├── cluster_forum.json             # 792 帖 (42 ERC threads)
    ├── cluster_github.json            # 657 条 (PR body+comments+reviews)
    ├── tier2_forum_manifest.json      # {topic_id: scraped/stream/official, complete}
    └── tier2_github_manifest.json     # {per_erc: prs_found, discovery_method, records}
```

- Round-1 数据未动（`data/raw/forum_posts.json`、`github_comments_filtered.json` 完好）。
- 每条记录带 `tier/erc/topic_id`（论坛）或 `tier/erc/pr_number`（GitHub），可回溯到源线程/PR。
- 日志：`data/raw/r2/logs/*.log`。

---

## 7. 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/scrape/scrape_r2_forum.py` | 泛化论坛抓取，读 CSV 抽样框，多 topic，逐帖完整性校验 |
| `scripts/scrape/scrape_r2_github.py` | GitHub PR 发现 + 抓取，commits→pulls 为主/search 兜底，增量写盘+断点续抓 |
| `scripts/scrape/patch_r2_tier2_github.py` | 修补：去重 24 条 + 补 #1592（8184→8190 编号漂移） |

---

## 8. 汇总

| | 论坛 | GitHub | 合计 |
|---|---|---|---|
| Tier 1 — ERC-8004 本体 | 227（8 线程） | 37（9 PR） | **264** |
| Tier 2 — agent 标准化集群 | 792（42 线程） | 657（按 ERC 发现 PR） | **1449** |
| **合计** | **1019 帖** | **694 条** | **1713** |
| Round-1 基准 | 113 | 36 | 149 |

**采集倍率：1713 / 149 ≈ 11.5×**

日期跨度：2025-08-02 → 2026-06-13（与 A2A 活跃窗口一致）
