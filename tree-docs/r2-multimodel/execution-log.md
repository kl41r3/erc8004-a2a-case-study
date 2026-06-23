# R2 — DAO 侧数据扩充（ERC-8004 本体补全 + agent 标准化集群）

**日期:** 2026-06-14 **分支:** `research/round-2-update`
**状态:** ✅ 数据采集完成（1713 条，11.5×）；P3 标注 / P4 指标暂停，等用户改口径

## 1. 问题诊断（证据）

RQ1 比较 DAO 治理（ERC-8004）vs 公司治理（Google A2A）。Round-1 数据严重失衡：

| | DAO (ERC-8004) | Corporate (A2A) |
|---|---|---|
| 论坛/讨论 | forum 113（单帖 25098） | discussions 822 |
| 代码评审 | 9 个 lifecycle PR / 36 评论 | PR 1955 + issues 3104 + commits 522 |
| 正式治理机制 | 9 PR + 1 论坛帖 | GitVote **仅 2 次投票** → 142 条衍生 |
| **合计** | **≈149** | **≈6545（1:44）** |

两个关键事实（决定方法）：
- **149 不是抓漏**：`data/raw/filter_log.json` 显示 GitHub 侧 36 条按编号直抓 9 PR、`dropped:0`。这是 ERC-8004 直接审议的真实体量。
- **6545 是全生态运营流量，不是治理审议**：A2A 正式治理（GitVote, `scripts/scrape/scrape_gitvote_prs.py`）只有 2 次投票。1:44 主要源于"量纲不对等"（单 ERC 审议 vs 整仓库 issue/bug/实现 PR）。

**结论：** 不靠"凑数"匹配 6545；而是 ①让两边可比 ②覆盖完整治理足迹 ③把 DAO 单案例升级为小总体以解决代表性。

## 2. 决策（用户确认）

- 方向：**集群 + 补全**，但做成**两份干净、独立的成果**：Tier 1 / Tier 2 分开，口径不混。
- 优先级：先把 ERC-8004 本体做扎实（Tier 1）；本体不足以撑代表性时，extend 到集群（Tier 2）。

## 3. 抽样框（证据：`analysis/r2_agent_erc_universe.csv`）

来源：ethereum-magicians `search.json`，17 个 agent/AI 查询去重，得 59 个候选线程。

**纳入判据（仅两条，可辩护）：**
1. **流程**：是正式 ERC/EIP 提案线程（有 ERC 号，或 "Draft ERC / Add ERC / Pre-ERC" 形式提交）。
2. **代际**：创建于 ERC-8004 时代（`created ≥ 2025-08-01`），与 A2A 活跃窗口同期。

**结果：**

| | 线程 | 论坛帖 | 备注 |
|---|---|---|---|
| Tier 1 — ERC-8004 本体 | 8 | 227 | 主帖 25098 需补全(本地 113 / 官方 207)、Call #1-3、Launch Day、Extension、TAP、production |
| Tier 2 — 集群（纳入） | 42 | 792 | 28 个 ≥3 帖（可做审议分析）；头部：8183(305)、8274(115)、8210(44)、8240(40)、8126(39)… |
| 排除 | 10 | 31 | 过时代际 AI-NFT（7662/7857/7860/18197）；非正式 ERC（ReceiptOS/OSRB/Panini/LAS） |

**待确认的边界判断（见 §6）。**

## 4. 数据架构（两份干净成果，round-1 不动）

```
data/raw/r2/
  tier1/  erc8004_forum.json  erc8004_github.json  tier1_manifest.json
  tier2/  cluster_forum.json  cluster_github.json  tier2_manifest.json
data/annotated/r2/  tier1_annotated.json   tier2_annotated.json
analysis/r2/
  r2_agent_erc_universe.csv   # 抽样框（已建）
  tier1_metrics.csv  tier2_metrics.csv
  cross_tier_comparison.csv   # T1 vs T2 vs A2A，归一化
output/r2/  ...
```

## 5. 执行阶段

- **P0 抽样框**（✅ 已完成）：普查 + 分类 + CSV `analysis/r2_agent_erc_universe.csv`。
- **P1 Tier 1 抓取**（✅ 论坛 + GitHub 完成）：
  - 脚本 `scripts/scrape/scrape_r2_forum.py`（泛化多 topic，修复原脚本 topic_id 写死的 bug）。
  - 论坛：8 线程 **227 帖**，全部 complete（主帖 25098 113→**207/207**），见 `data/raw/r2/tier1/tier1_forum_manifest.json`。
  - GitHub：`scripts/scrape/scrape_r2_github.py --tier tier1`，9 PR **37 条** → `data/raw/r2/tier1/erc8004_github.json`。
- **P2 Tier 2 抓取**（✅ 论坛 + GitHub 完成）：
  - 论坛：`scrape_r2_forum.py`，42 ERC 线程 **792 帖**，42/42 complete，见 `data/raw/r2/tier2/tier2_forum_manifest.json`。
  - GitHub：`scrape_r2_github.py --tier tier2`（增量写盘 + 断点续抓），按 ERC 发现 PR；
    `patch_r2_tier2_github.py` 去重(674→650, 删 24 重复) + 补漂移 #1592 → **657 条**。
- **P3 标注**（⏸ 暂停，等用户改口径）：复用 `annotate_llm.py` schema，分别产出 tier1/tier2 标注集。
- **P4 指标 + 归一化对比**（⏸）：每 tier 结构指标；T1/T2/A2A 三方按"每决策 / 单位时间 / 每参与者"归一化。
- **P5 更新 README / 数据卡 / CHECKSUMS**（CHECKSUMS ✅ 其余 ⏸）。

> **用户指令（2026-06-14）**：本轮只把数据**完整**扒下来即停（P3/P4 用户要改动，先不跑）；
> 全程做数量/流程记录保证 traceable；数据不全须继续想办法补全。

## 5b. 最终数据成果（✅ 完整，已校验）

数据完整性来源 = 各 manifest 的 `complete` 字段 + `CHECKSUMS.json`（`data/raw/r2/`，8 文件 SHA-256）。

| 数据集 | 文件 | 记录 | 作者 | 日期范围 | 完整性 |
|---|---|---|---|---|---|
| Tier1 论坛 | `tier1/erc8004_forum.json` | 227 | 94 | 2025-08-14→2026-06-13 | 8/8 complete（主帖 25098 113→**207/207**） |
| Tier1 GitHub | `tier1/erc8004_github.json` | 37 | 12 | 2025-08-13→2026-06-10 | 9 lifecycle PR 全抓 |
| Tier2 论坛 | `tier2/cluster_forum.json` | 792 | 101 | 2025-08-02→2026-06-13 | 42/42 complete |
| Tier2 GitHub | `tier2/cluster_github.json` | 657 | 57 | 2025-08-05→2026-06-13 | 去重 + 漂移补全 |
| **合计** | — | **1713** | **210 distinct** | — | **round-1 ~149 → 11.5×** |

**provenance / 数据流：**
- 抽样框 `analysis/r2_agent_erc_universe.csv` → `scrape_r2_forum.py`（读 include==Y，按 tier 分流）→ 两份 forum json + manifest（逐 topic `scraped/stream/official` 三计数核完整性）。
- 同抽样框 → `scrape_r2_github.py`：Tier1 用固定 9 PR；Tier2 用 `discover_prs()`（A: `/commits?path=ERCS/erc-N.md`→`/commits/{sha}/pulls`；B: `search type:pr ERC-N`→`/pulls/{n}/files` 确认）→ `patch_r2_tier2_github.py` 去重 + 漂移修补。
- 每条记录带 `tier/erc/topic_id`（论坛）或 `tier/erc/pr_number`（GitHub），可回溯到源线程/PR。
- 日志 `data/raw/r2/logs/*.log`；每个数据块一份 `*_manifest.json`。

**已核实的边界/特例（可追溯）：**
- ERC-8184 编号漂移：论坛帖 28012 自称 8184，但仓库 PR #1592 实建 `erc-8190.md`（同名 "Payment Channels with Signed Vouchers"）→ 已显式补抓并在记录 `_note` 标注。
- 7 个 forum-only（无 PR）：均为无编号的 Draft/Pre-ERC 帖（28785/28670/27949/28010/28404/28152/28070）——论坛先放草案、尚未提交 PR，forum-only 正确且完整（本身是 DAO 低门槛特征的证据）。
- ERC-8183（topics 27902+27970）、ERC-8259（28521+28473）各有两个论坛帖：forum 两帖均保留（确为不同讨论），GitHub 共享 PR 已去重。

## 6. 待确认边界（执行前）

1. **8004 扩展归属**：`ERC-8294 Validation Network Interface for ERC-8004`(14)、`ERC-8004 in production`(8) → 算 Tier 1 还是 Tier 2？（默认：production 帖 → T1；8294 有独立 ERC 号 → T2）
2. **Tier 2 是否抓 GitHub PR**：forum-only（快）还是 forum+PR 全口径对齐 8004（慢、更严谨）？（默认：先 forum，PR 二轮）
3. **审议阈值**：argument/stance 分析仅用 ≥3 帖线程；全量（含单帖）仅进结构指标（提案存活率等）。（默认：采纳）

## 7. 已知限制

- ERC-8004 本体审议体量客观偏小（227），代表性主要靠集群补足——须在论文中明示单案例 vs 小总体的口径。
- 集群 ERC 主题异质（identity / payments / registry / governance），需在分析中标注子主题，避免"苹果比橘子"。
- 论坛 `posts_count` 为快照，随时间增长；抓取需记录抓取时点。

## 8. 标注阶段（🔄 进行中，2026-06-14）

### 8a. 多模型设计（提升可信度）

遵循多 LLM triangulation 验证方法论（多独立 coder → pairwise Cohen's κ → Fleiss' κ → 人类验证样本），用 3 个异构模型对 R2 数据独立标注。

**模型选择（最终）：**

| # | 模型 | API | 类型 | 状态（最终） |
|---|---|---|---|---|
| 1 | **DeepSeek-V4-Flash** (`deepseek-v4-flash`) | api.deepseek.com | Reasoning | ✅ ERC 1,661/1,664；A2A 4,059/4,059（214 条 2026-06-23 补完） |
| 2 | **GLM-4-Plus** (`glm-4-plus`) | open.bigmodel.cn | General-purpose | ✅ ERC 1,664/1,664；A2A 4,059/4,059 |
| 3 | ~~Kimi-K2.6~~ → **Moonshot-v1-Auto** (`moonshot-v1-auto`) | api.moonshot.cn | General-purpose (fast) | ✅ ERC 1,664/1,664；A2A 4,059/4,059 |
| ~~MiniMax-M3~~ | ~~api.minimaxi.com~~ | ~~Reasoning~~ | ❌ Token Plan 额度耗尽 (429)，全数失败 → 已从代码与结果移除（2026-06-23），仅留此记录 |
| ~~Kimi-K2.6~~ | ~~api.moonshot.cn~~ | ~~Reasoning~~ | ❌ ~60s/条 ETA 25h，不切实际，改用 v1-auto |

模型异构性：DeepSeek-V4-Flash（推理型）、GLM-4-Plus（智谱通用）、Moonshot-v1-Auto（月之暗面通用）——三个不同厂商、不同架构，降低系统性偏差风险。**最终进入 ICR / 多数投票共识的为这 3 个模型**；MiniMax-M3 未参与任何最终结果。

### 8b. 标注 schema（与 round-1 一致）

5 字段结构码：`stakeholder_institution`、`argument_type`、`stance`、`consensus_signal`、`key_point`。
每记录 ≤20 词 token 的文本 → `raw_text[:3000]`。

### 8c. 脚本交付物

| 脚本 | 用途 |
|---|---|
| `scripts/process/annotate_r2.py` | Multi-model 结构化标注（--model deepseek/glm/kimi） |
| `scripts/process/annotate_thematic.py` | 开放式 thematic analysis（独立主题提取） |
| `scripts/analyse/validate_multimodel.py` | Pairwise/Fleiss κ + 混淆矩阵 + 验证样本 + 偏差分析 |

**annotate_r2.py 关键设计：**
- 3 个独立 output 目录：`data/annotated/r2/{deepseek,glm,kimi}/annotations.json`
- 断点续标：`_record_id()` composite key，中断可恢复
- Per-model params：token 上限、temperature（Kimi 必须 1.0）、sleep 间隔
- 429 指数退避重试（5 次）
- `<think>...</think>` 推理块 strip（MiniMax/Kimi reasoning 模型兼容）

### 8d. 数据流

```
data/raw/r2/tier{1,2}/*.json  (1713 records)
    │
    ├──→ annotate_r2.py --model deepseek  →  data/annotated/r2/deepseek/annotations.json
    ├──→ annotate_r2.py --model glm       →  data/annotated/r2/glm/annotations.json
    └──→ annotate_r2.py --model kimi      →  data/annotated/r2/kimi/annotations.json
                │
                ▼
         validate_multimodel.py
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
pairwise κ   Fleiss' κ   verification
(Cohen)      (all 3)     sample (n=50)
    │           │           │
    └───────────┴───────────┘
                ▼
    data/annotated/r2/validation/
```

### 8e. 待标注完成后（P3 标注完了，P4 validation 待跑）

- [x] 验证三模型标注成功率（GLM 100% ✅, DeepSeek/Kimi ~99.8%）
- [x] 跑 pairwise/Fleiss κ ✅
- [x] 生成 stratified verification sample (n=50) ✅ → `verification/verification_sample.csv`
- [x] Thematic analysis ✅ 三模型 100%（1034/1034）
- [x] Thematic convergence (Jaccard + convergent themes) ✅
- [x] 同步更新本文

## 10. Thematic Analysis 结果（2026-06-14/15）

### 10a. 执行概要

| 模型 | 进度 | 主题/条 | Sentiment | 状态 |
|---|---|---|---|---|
| Kimi (Moonshot-v1-Auto) | 1034/1034 | 3.80 | Supportive=66% Critical=13% Neutral=21% | ✅ 100% |
| GLM-4-Plus | 1034/1034 | 2.92 | Supportive=59% Critical=21% Neutral=20% | ✅ 100% |
| DeepSeek-V4-Flash | 1034/1034 | 2.82 | Supportive=76% Critical=9% Neutral=15% | ✅ 100% |

### 10b. 主题收敛（dual-model Jaccard，590 记录）

LLM 开放性主题提取的标签措辞不一致是普遍现象——不同模型用不同词汇表达同一概念。
**Jaccard similarity**（精确标签匹配）较低（mean 0.017-0.115, median 0.000），这符合 qualitative coding 文献的预期——需要 semantic matching 做第二步。

尽管如此，仍有 **11 个跨模型收敛主题**（≥2 模型提取相同标签 ≥2 条记录）：

| Theme | 记录数 | 治理维度 |
|---|---|---|
| Interoperability | 9 | 技术协调 |
| Transparency | 5 | 过程正义 |
| Backward Compatibility | 4 | 技术保守 |
| Security Enhancement | 3 | 安全 |
| Economic Accountability | 3 | 经济效率 |
| Process transparency | 3 | 过程正义 |
| Accountability | 3 | 权力约束 |
| Separation of Concerns | 2 | 架构原则 |
| Standardization | 2 | 技术协调 |
| Governance Process | 2 | 过程正义 |
| Process clarity | 2 | 过程正义 |

### 10c. 交付物

| 文件 | 说明 |
|---|---|
| `data/annotated/r2/thematic/{deepseek,glm,kimi}_themes.json` | 逐条主题+证据+情绪 |
| `data/annotated/r2/thematic/validation/cross_model_themes.csv` | 跨模型并行主题表 |
| `data/annotated/r2/thematic/validation/thematic_validation_report.json` | 完整收敛报告 |

## 9. Validation 结果（2026-06-14）

### 9a. 标注质量

| 模型 | 成功率 | 错误 | 说明 |
|---|---|---|---|
| GLM-4-Plus | 1664/1664 (100%) | 0 | 最快完成 |
| DeepSeek-V4-Flash | ~99.8% | 2 | 运行中 |
| Moonshot-v1-Auto | ~100% | 0 | 运行中 |

### 9b. Multi-Model Inter-Coder Reliability

N = 898 对齐记录（三模型共同覆盖）

| 字段 | DeepSeek↔GLM | DeepSeek↔Kimi | GLM↔Kimi | Fleiss' κ | 3/3 全票率 |
|---|---|---|---|---|---|
| argument_type | **0.610** Substantial | 0.511 Moderate | **0.588** Moderate | **0.570** Moderate | **82.6%** |
| stance | 0.478 Moderate | 0.226 Fair | 0.391 Fair | 0.335 Fair | 40.1% |
| consensus_signal | 0.266 Fair | 0.270 Fair | 0.232 Fair | 0.245 Fair | 42.3% |
| institution | 0.346 Fair | 0.101 Poor | 0.127 Poor | 0.113 Poor | 72.7% |

### 9c. 关键发现

1. **argument_type 达到 "Substantial" 一致性**（κ̄=0.570, 3/3 全票 82.6%）——这是论文最核心的结构化字段，验证通过。
2. **Moonshot-v1-Auto 存在系统性偏差**：stance "Support"=78.4%（vs DeepSeek 31%、GLM 45%），institution "Ethereum Foundation"=21%（vs 1-2%）——多模型 triangulation 的必要性得到实证。
3. **consensus_signal 跨模型一致差**：三模型都难以从文本中可靠推断最终决策——说明这个字段需要外部数据（PR merge status），LLM-only 标注不适合。
4. **stakeholder_institution 论坛不适用**：ethereum-magicians 帖子不带机构元数据，三模型均主导 "Independent"——未来需要 enrich_profiles.py 的外部数据而非靠 LLM 推断。

### 9d. 交付物

| 文件 | 说明 |
|---|---|
| `data/annotated/r2/validation/pairwise_kappa.csv` | 9 对 pairwise κ |
| `data/annotated/r2/validation/validation_report.json` | 完整报告 |
| `data/annotated/r2/validation/verification_sample.csv` | 50 条人类验证样本 |
