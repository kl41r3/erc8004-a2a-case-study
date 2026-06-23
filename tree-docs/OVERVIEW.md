# RQ1 项目总览 (OVERVIEW)

> **这是唯一的入口文件。** 想用一个文件了解整个项目的全部结果，看本文件即可；需要细节时再按文末的「文档索引」跳到对应节点。
>
> 最后更新：2026-06-23 ｜ 分支：`research/round-2-update`

---

## 0. 项目一句话

RQ1 比较两种治理形态在 AI agent 协议标准化中的差异：
**Case A — ERC-8004**（Trustless Agents，去中心化 DAO / EIP rough-consensus）vs **Case B — Google A2A**（公司层级 TSC + GitVote）。
方法是统一的：抓取治理讨论 → LLM 结构化标注 → 话语分析 (BERTopic / Thematic-LM) + 社会网络分析 (SNA / DNA / 社会语义二分网络)。

## 1. 核心结论（一句话回答 RQ1）

> **去中心化是「革命」还是「幻象」？从本领域看，更接近幻象。** 治理形态变了，参与结构没变。

支撑三点（详见 [r1-baseline/paper/draft.md](r1-baseline/paper/draft.md)，并在 R2 扩样后保持稳健）：

1. **相反的治理架构，相同的结构性结果。** ERC-8004 靠无正式投票的 rough consensus 推进，A2A 把约束性权力交给 8 席 TSC；两者都产生寡头化参与。
2. **过程开销不对称。** 两者都技术主导，但 A2A 投入约 2× 的 Process 论据份额（R1: 25.4% vs 13.9%，χ²(3)=52.88, p<.001, V=.103）。
3. **参与不平等可比。** 度 Gini 0.804 (ERC) vs 0.779 (A2A)。无门槛准入改变了治理精英的「身份」（声誉持有者 vs 公司代表），但没改变集中度的「量级」。

## 2. 三轮状态板

| 轮次 | 方法升级 | 数据规模 | 状态 | 主报告 |
|---|---|---|---|---|
| **R1 baseline** | 单模型 MiniMax-M2.5；首版 SNA/话语分析；IEEE 论文初稿 | ERC 142 ｜ A2A 4,181 | ✅ 完成 | [r1-baseline/](r1-baseline/) 各节点 |
| **R2 multi-model** | 三模型独立标注 + 多数投票 + ICR；ERC 扩为 34-ERC 集群 | ERC 1,664 ｜ A2A 4,059 | ✅ 完成 | [r2-multimodel/final-report.md](r2-multimodel/final-report.md) |
| **R3 robustness** | 3 模型 × 3 轮 × 2 案例 = 18 组；跨轮 + 跨模型信度 | ~49,500 条标注 | ✅ 完成 | [r3-robustness/final-report.md](r3-robustness/final-report.md) |

## 3. 案例对照

| | Case A — ERC-8004 | Case B — Google A2A |
|---|---|---|
| 治理类型 | 无门槛 DAO / EIP editor rough-consensus，无正式投票 | 公司 TSC（8 席全公司），争议变更走 GitVote |
| 关键时点 | 提案 2025-08-13，主网 2026-01-29 | 首次提交 2025-03-25，2025-06 捐给 Linux Foundation |
| 数据源 | ethereum-magicians 论坛 + `ethereum/ERCs` GitHub PR | A2A 仓库 issues / PR / commits / GitVote |
| 正式投票 | 无（editor 合并判断） | GitVote，仅 2/755 PR 触发（#831 通过，#1206 关闭） |

---

## 4. 各轮关键结果

### 4.1 R1 baseline（单模型，首版完整分析）

- **结构指标**（[r1-baseline/preliminary-analysis/structural-metrics.md](r1-baseline/preliminary-analysis/structural-metrics.md)）：ERC 149 条 / 71 人，A2A 5,272 条 / 826 人；Independent 占比两边都约 44%；Google、Coinbase 是 ERC-8004 正式 co-author 但零公开讨论记录。
- **投票机制**（[r1-baseline/round-b-analysis/voting-mechanism.md](r1-baseline/round-b-analysis/voting-mechanism.md)）：ERC 无正式投票机制；A2A 38 个 `/vote` 命令，但只在 2 个 PR 上真正触发（治理升级才用）。
- **话语分布**（[r1-baseline/round-b-analysis/topic-analysis.md](r1-baseline/round-b-analysis/topic-analysis.md)）：ERC Technical 74.3% / Process 13.9%；A2A Technical 64.7% / Process 25.4%（近 2×）。跨案例 χ²(3)=52.88, V=.103；ERC 生命周期内 χ²(6)=25.32, V=.315。
- **社会网络**（[r1-baseline/round-b-analysis/network-analysis.md](r1-baseline/round-b-analysis/network-analysis.md)）：ERC 67 节点 / 65 边 / Gini 0.804；A2A 771 / 1,230 / Gini 0.779。两边都高度不平等；A2A 的中介权被 Google 捕获（top-5 brokers 中 4 个是 Google，holtskinner 一人占 13.6% 最短路径），ERC 的 brokers 来自 5 个不同机构。
- **论文**：IEEE 初稿 `paper/RQ1.tex`（[r1-baseline/paper/draft.md](r1-baseline/paper/draft.md)）。

### 4.2 R2 multi-model（方法论主升级）

详见 [r2-multimodel/final-report.md](r2-multimodel/final-report.md)。

- **数据扩充**：ERC 从单提案扩为 34-ERC agent 集群，1,664 条；A2A 三模型全部完成 4,059 条（原 DeepSeek 因限流缺 214 条，已于 2026-06-23 补完），共识 N=4,058。采集倍率相对 R1 约 11.5×（[data-collection.md](r2-multimodel/data-collection.md)）。
- **三模型 ICR**（deepseek-v4-flash / glm-4-plus / moonshot-v1-auto；R2 原计划的第 4 个模型 MiniMax-M3 因 API 额度耗尽 429 全数失败，已从代码与结果中移除，仅在文档留存失败记录，[data-processing.md](r2-multimodel/data-processing.md)）：

  | 字段 | ERC Fleiss κ (N=1,664) | A2A Fleiss κ (N=4,045) |
  |---|---|---|
  | **argument_type** | **0.683 Substantial** | **0.619 Substantial** |
  | stance | 0.369 Fair | 0.484 Moderate |
  | consensus_signal | 0.299 Fair | 0.465 Moderate |
  | stakeholder_institution | 0.161 Slight | 0.165 Slight |

  > 数据来源（权威）：`data/annotated/r2/validation/validation_report.json`（ERC）+ `data/annotated/r2/a2a/validation/validation_report.json`（A2A），2026-06-23 v2 用 `validate_multimodel.py` 重算（DeepSeek A2A 补完后 N=4,045）。argument_type A2A κ 从 0.602（N=3,831）升至 0.619（N=4,045），越过 Substantial 阈值。早期 `r2-multimodel/final-report.md` 曾把 A2A argument_type 误记为 0.706，已于 2026-06-23 v1 更正；v2 进一步更新为 0.619。paper-acm 附录 Table `tab:icr-crossmodel` 与本表、final-report.md 三处现已完全一致。

  关键：`argument_type` ERC 与 A2A 现均达 Substantial（κ=0.683/0.619），可靠用于结构推断；`stance` / `consensus_signal` / `institution` 信度偏低，论文中已降权并改用外部数据。Moonshot 有系统性 Support 偏误（+30pp），实证了多模型 triangulation 的必要性。
- **社会网络（关键发现，与原论文相反）**：扩样后 ERC 巨连通分量比 GCR 从 R1 的 0.328 升到 **0.917**（13 个分量，连成一张网）；A2A 仍碎片化 **GCR 0.285**（435 个分量，43% 孤立）。原论文结论是 A2A 更连通（GCR 0.534 > ERC 0.328），扩样后**排序反转**：DAO 成了更连通、更可观测的一方。解读：A2A 大量内容 invisible（链下 TSC 会议 / Discord / 公司内部），并非完全 public；ERC 在生态尺度上把完整审议留在公开记录里。已写入 `paper-acm/acm.tex` 附录「Multi-Model and Multi-Round Robustness Check」。数据：`output/stats/r2_network_metrics.json`。
- **话语网络 DNA**：ERC 态度一致性密度 **0.729** > A2A 0.519（去中心化社区在更少主题上达成更深一致）。
- **论文交付**：唯一正式论文为 `paper-acm/acm.tex`（R1 + 多模型/多轮稳健性附录，含网络反转发现），可编译、引用全解析。原 `paper-extended-2/`（多模型独立版）已于 **2026-06-23 停用并删除**（用户决定不再需要该论文）；其多模型 / 稳健性内容已并入 paper-acm 附录「Multi-Model and Multi-Round Robustness Check」。

### 4.3 R3 robustness（标注稳健性验证）

详见 [r3-robustness/final-report.md](r3-robustness/final-report.md)。

- **设计**：3 模型 × 3 轮独立标注 × 2 案例 = 18 组，仅 3 字段（argument_type / stance / consensus_signal），约 49,500 条标注，18/18 轮次 100% 覆盖。
- **跨轮信度（自我复现）**：glm-4-plus Fleiss κ 0.86–0.93（最稳）；deepseek-chat 0.69–0.92；deepseek-v4-flash 0.51–0.63（reasoning 模型方差最大）。
- **跨模型一致**：3/3 全同意 ~55–63%，2/3+ 一致 ~96–99%。
- **BERTopic 跨模型 JSD 0.000–0.014**（近乎一致）。
- **结论**：模型选择对 BERTopic 话语构成影响极小（JSD < 0.02）；标注信度因模型而异。
- 弃用模型（API 问题）：glm-5.x 全空响应、glm-4.7 限流、kimi-k2.6 异常（[progress.md](r3-robustness/progress.md)）。

### 4.4 方法学规划

[methodology/auto-research-integration.md](methodology/auto-research-integration.md)：把静态三模型标注升级为 auto-research 迭代 agent 流水线的三阶段方案（Phase B 迭代标注验证为推荐起点）。待用户决策，未实施。

---

## 5. 交付物速查

| 类型 | 位置 |
|---|---|
| 论文（**唯一正式版**：R1 + 多模型/多轮稳健性附录） | `paper-acm/acm.tex` + `.pdf` |
| ~~论文（多模型独立版）~~ | ~~`paper-extended-2/`~~ — 2026-06-23 停用并删除 |
| R2 共识标注 | `data/annotated/r2/consensus/{erc,a2a}_annotations.json` |
| R3 多轮标注 + 共识 | `data/annotated/r3/{case}/{model}/...` |
| 话语分析输出 | `output/topic_discovery/r2/`、`output/topic_discovery/r3/` |
| 网络分析输出 | `output/network_discourse/r2/{dna,sociosemantic}/` |
| 论文图表 | `output/figures/r2/` |
| 原始数据 + 校验 | `data/raw/r2/`（`CHECKSUMS.json` SHA-256） |

---

## 6. 完整文档索引（tree-docs 全树）

```
tree-docs/
├── OVERVIEW.md                         ← 本文件，唯一入口
├── methodology/
│   └── auto-research-integration.md    自动研究流水线集成方案（规划，未实施）
├── r1-baseline/                        R1 单模型基线 + 首版完整分析
│   ├── data-collection/                scraping / filtering / annotation / data-inventory
│   ├── preliminary-analysis/           structural-metrics（结构指标）
│   ├── topic-discovery/                README + Thematic-LM / Comparative-Discourse / CryptoBERT
│   ├── network-discourse/              README + DNA / 社会语义二分网络
│   ├── round-b-analysis/               network / topic / voting-mechanism 三张图的分析
│   └── paper/                          draft（IEEE 初稿状态）+ literature-table
├── r2-multimodel/                      R2 三模型 + 扩样 + ICR
│   ├── data-collection.md              Tier1/Tier2 采集（1,713 条，11.5×）
│   ├── data-processing.md              三模型标注 + κ + 偏差 + thematic
│   ├── execution-log.md                全流程执行日志（决策/采集/标注/验证）
│   ├── paper-comparison.md             新旧论文结构对比（⚠ 06-21 快照；extended-2 已删）
│   ├── models-final-and-cleanup.md     ★ 最终模型清单 + MiniMax-M3 失败 + 06-23 清理
│   └── final-report.md                 ★ R2 综合结果报告
└── r3-robustness/                      R3 多轮稳健性
    ├── progress.md                     模型/API/覆盖率进度
    ├── analysis.md                     精简结果摘要
    └── final-report.md                 ★ R3 综合结果报告
```

---

## 7. 跨轮已知局限

1. **ERC-8004 本体审议体量偏小**（R1 142 / R2 本体 264 条），代表性主要靠 34-ERC 集群补足；论文须明示「单案例 vs 小总体」口径（[execution-log.md §7](r2-multimodel/execution-log.md)）。
2. **`stance` / `consensus_signal` / `institution` 三字段 LLM-only 标注不可靠**（κ 偏低）；consensus 需 PR merge status，institution 需 `enrich_profiles.py` 外部数据，不应只靠文本推断。
3. **两案例边类型不同**（ERC 用 reply/quote/PR 共参；A2A 仅 PR/issue 共参），直接度比较假设两者都代理「治理互动」。
4. **A2A 大量孤立节点**可能反映链下讨论（TSC 电话会、Discord）未被采集，而非真实不参与。
5. **paper-comparison.md 第二节为 2026-06-21 过程快照已过时**，最终数据以 final-report 为准。
