# R2 多模型标注与分析最终报告

**生成时间：** 2026-06-22  
**方法：** 三 LLM（deepseek-v4-flash、glm-4-plus、moonshot-v1-auto）独立标注，多数投票共识，Cohen's κ + Fleiss' κ 验证

---

## 1. 数据概况

| 案例 | DeepSeek | GLM-4-Plus | Moonshot | 共识 (多数投票) |
|------|---------|-----------|----------|------|
| **ERC Agent Cluster** (34 ERCs) | 1,664 / 1,664 ✅ | 1,664 / 1,664 ✅ | 1,664 / 1,664 ✅ | **1,664** |
| **Google A2A** | 4,059 / 4,059 ✅ | 4,059 / 4,059 ✅ | 4,059 / 4,059 ✅ | **4,058** |

A2A 唯一记录 4,059 条（text≥50 字符、URL 去重后）。DeepSeek 原因速率限制剩约 214 条未标注，已于 2026-06-23 补跑完成（`scripts/process/complete_a2a_deepseek.py`）；三模型共有交集 N=4,045 用于 ICR κ 计算，共识 N=4,058。

> **标注模型说明：** R2 计划用 4 个模型，**MiniMax-M3 因 API 额度耗尽（429）全数失败**，已从代码与最终结果中移除，失败记录见 `data-processing.md` §1b、`execution-log.md`。最终成功并进入分析的为 3 个：**deepseek-v4-flash、glm-4-plus、moonshot-v1-auto**。

---

## 2. 评分者间信度 (Inter-Coder Reliability)

| 字段 | ERC Fleiss κ (N=1,664) | ERC Band | A2A Fleiss κ (N=4,045) | A2A Band |
|------|------------|----------|-------------|----------|
| **Argument Type** | **0.683** | Substantial | **0.619** | Substantial |
| Stance | 0.368 | Fair | 0.484 | Moderate |
| Consensus Signal | 0.299 | Fair | 0.465 | Moderate |
| Stakeholder Institution | 0.161 | Slight | 0.165 | Slight |

> **更新记录（2026-06-23 v2）：** DeepSeek A2A 214 条缺失记录已通过 `scripts/process/complete_a2a_deepseek.py` 补标完成（4,059 条全覆盖）。ICR 用三模型共有交集 N=4,045（原 3,831）重算，argument_type κ 从 0.602 升至 0.619，越过 Substantial 阈值（≥0.61）。共识 N 从 3,844 升至 4,058。所有权威值来源：`data/annotated/r2/a2a/validation/validation_report.json`（重算命令：`uv run python scripts/analyse/validate_multimodel.py --dataset a2a`）。
>
> **早期更正记录（2026-06-23 v1）：** 此前 A2A 列曾误记（argument_type 0.706、stance 0.497、consensus 0.531、institution 0.241），已于 2026-06-23 首次更正。

**关键发现：** Argument_type 是论文核心结构字段：ERC 与 A2A 现均达 Substantial（κ=0.683 / 0.619），可用于结构推断。GLM-Kimi 在两案例均为最强配对（ERC AT κ=0.730，A2A AT κ=0.671）。institution（κ=0.161/0.165，Slight）、stance、consensus_signal 信度偏低，论文中仅作粗分层或需外部数据（`enrich_profiles.py` / PR merge status）补齐。

---

## 3. Argument Type 与 Stance 分布

| Argument Type | ERC (R2) | ERC (R1, 对比) | A2A (R2) |
|--------------|---------|--------------|---------|
| Technical | 70.9% | 74.3% (−3.4) | 72.4% |
| Process | 26.5% | 13.9% (+12.6) | 24.4% |
| Governance-Principle | 0.8% | 5.4% (−4.6) | 1.8% |
| Economic | 0.4% | 1.4% (−1.0) | 0.1% |
| Off-topic | 1.4% | 5.0% (−3.6) | 1.3% |

| Stance | ERC (R2) | A2A (R2) |
|--------|---------|---------|
| Support | 46.9% | 42.8% |
| Modify | 25.3% | 29.5% |
| Neutral | 25.0% | 23.6% |
| Oppose | 1.6% | 3.1% |
| Off-topic | 1.3% | 1.0% |

**χ² 检验 (ERC vs A2A)：**

| 字段 | χ² | Cramér's V |
|------|-----|-----------|
| argument_type | 13.42 | 0.050 |
| stance | 24.08 | 0.067 |
| consensus_signal | 63.41 | 0.108 |
| stakeholder_institution | 1887.12 | 0.590 |

---

## 4. BERTopic 话语主题分析

- **19 个主题**，Global JSD = 0.372（R1: 0.288，同量级扩大）
- ERC 集中在 Topic 0（通用 agent 话语，Δ=31.2pp ERC 主导）
- A2A 分散到工程执行主题（Task/Message、JSON/Protobuf、PR 工作流）

---

## 5. 社会网络分析 (SNA)

| 指标 | ERC Cluster | ERC (R1) | Google A2A | A2A (R1) |
|------|-----------|---------|-----------|---------|
| Nodes | **204** | 67 | **607** | 771 |
| Edges | 4,955 | 65 | 1,588 | 1,230 |
| Density | 0.239 | 0.029 | 0.009 | 0.004 |
| Giant Component Ratio | **0.917** | 0.328 | **0.288** | 0.534 |
| Top-3 Degree Share | 3.8% | 32.3% | 7.1% | 14.9% |

**关键发现：** Tier-2 ERC 扩展大幅提升网络连通性（GCR 0.328→0.917），将原先孤立的提案线程编织成连贯的话语网络。A2A 网络仍然碎片化（GCR 0.288），59% 参与者为完全孤立节点。

---

## 6. 话语网络分析 (DNA)

| 指标 | ERC-8004 | Google A2A |
|------|---------|-----------|
| Actors | 200 | 717 |
| Active Themes | 5 | 5 |
| Congruence Edges | 14,503 | 133,330 |
| Congruence Density | **0.729** | 0.519 |
| Conflict Edges | 1,214 | 9,468 |

**关键发现：** ERC 态度一致性密度 (0.729) 显著高于 A2A (0.519)，去中心化社区在更少主题但更深度的议定态。

---

## 7. 社会语义二分网络

| 指标 | ERC Cluster | Google A2A |
|------|-----------|-----------|
| Actors | 200 | 717 |
| Active Themes | 5 | 5 |
| Mean Actor Entropy H | 0.200 | 0.199 |
| H Gini | 0.785 | 0.807 |
| Thematic Overlap Ω | **1.000** | |

两个案件的绝大多数参与者专注单一话语功能（median H=0），主题专业化程度相似。

---

## 8. 与 R1 的主要对比

| 维度 | R1 (MiniMax-M2.5, 单模型) | R2 (三模型, 多数投票) |
|------|------------------------|---------------------|
| DAO 数据量 | 142 条 (1 ERC) | **1,664 条 (34 ERCs)** |
| A2A 数据量 | 4,181 条 | **4,058 条 (三模型共识)** |
| 标注可复现性 | 无 ICR | **Substantial AT κ, 双案例** |
| ERC Process % | 13.9% | 26.5% (Tier-2 扩展发现) |
| ERC SNA GCR | 0.328 | **0.917** (多 ERC 生态效应) |
| BERTopic JSD | 0.288 | 0.372 |
| 论文定位 | 单模型经验报告 | 多模型方法论 + 稳健性验证 |

---

## 9. 文件产出清单

### 数据文件
- `data/annotated/r2/consensus/erc_annotations.json` — ERC 1,664 条共识
- `data/annotated/r2/consensus/a2a_annotations.json` — A2A 4,058 条共识
- `data/annotated/r2/validation/validation_report.json` — ERC ICR 报告
- `data/annotated/r2/a2a/validation/validation_report.json` — A2A ICR 报告

### 分析文件
- `analysis/r2_structural_metrics.csv` — 结构指标
- `output/stats/r2_findings_summary.md` — 发现总结
- `output/stats/r2_chi2_results.json` — χ² 检验结果
- `output/stats/r2_annotation_stats.json` — 标注分布统计
- `output/topic_discovery/r2/comparative_discourse/` — BERTopic 结果
- `output/network_discourse/r2/dna/dna_metrics.json` — DNA 指标
- `output/network_discourse/r2/sociosemantic/ss_metrics.json` — 社会语义指标
- `analysis/r2_network_metrics_table.csv` — SNA 指标

### 论文图表
- `output/figures/r2/r2-topic-pie-erc.pdf` — Argument type 分布
- `output/figures/r2/r2-topic-stance-heatmap.png` — Stance × Argument heatmap
- `output/figures/r2/r2-fig-bertopic-divergence.pdf` — BERTopic 话题分歧
- `output/figures/r2/r2-fig-combined-themes.pdf` — Thematic-LM 组合图
- `output/figures/r2/r2-network-sna-2col.pdf` — SNA 双栏网络图
- `output/figures/r2/r2-fig-ss-entropy.pdf` — Actor 熵分布
- `output/figures/r2/r2-fig-icr-heatmap.pdf` — ICR κ 热力图

### 论文
- `paper-acm/acm.tex` + `paper-acm/acm.pdf` — **唯一正式论文**（R1 + 多模型/多轮稳健性附录）
- ~~`paper-extended-2/`~~ — 多模型独立版，**2026-06-23 停用并删除**（用户不再需要；内容已并入 paper-acm 附录）
