# R2 论文对比报告

> ⚠ **快照说明（2026-06-22 标注）：** 本文件是 2026-06-21 的过程快照，第二节列出的标注进度、TBD 占位符清单等已过时（A2A 标注当时仍在跑）。最终结果以 [`final-report.md`](final-report.md) 为准；本文件保留用于追溯新旧论文的结构性差异（第一、三节仍有效）。
>
> **2026-06-23 更新：** `paper-extended-2/`（下文「新版」）已**停用并删除**（用户不再需要该论文），其多模型 / 稳健性内容已并入 `paper-acm/acm.tex` 附录。本文件仅作历史结构对比留存，不再有交付意义。
>
> 生成时间：2026-06-21  
> 对比对象：`paper-acm/acm.tex`（保留版）vs ~~`paper-extended-2/acm.tex`~~（已删除）

---

## 一、新旧论文核心差异

### 1.1 数据规模

| 维度 | 旧版 (R1) | 新版 (R2) |
|---|---|---|
| DAO 案例 | ERC-8004 单个提案，保留 **142 条**记录 | ERC agent cluster：ERC-8004 + 33 个依赖/被依赖 ERC，共 **34 个 ERC、1,664 条**记录 |
| 企业案例 | Google A2A，保留 **4,181 条**记录 | 同一批 A2A 原始数据，按新标准过滤（≥50 字符），保留约 **4,920 条**记录 |
| 总数据量 | 4,323 条 | ~6,584 条（待 A2A 标注完毕确认） |
| DAO 来源 | 仅 ERC-8004 论坛帖 + 9 个 lifecycle PR | 34 个 ERC 的论坛帖 + 对应 GitHub PR |

**影响：** ERC 侧从单一 ERC 扩展为整个 agent 提案生态圈，DAO 案例的论证从"一个 ERC 的行为"升级为"去中心化提案生态系统的结构性规律"。

---

### 1.2 标注方法

| 维度 | 旧版 (R1) | 新版 (R2) |
|---|---|---|
| 标注模型 | **单模型**：MiniMax-M2.5（一次标注） | **三模型**：deepseek-v4-flash + glm-4-plus + moonshot-v1-auto |
| 共识策略 | 无 | **多数投票**（2/3 同意采纳；3 方不一致时用 tiebreaker 模型） |
| Tiebreaker | 无 | argument\_type → Moonshot；stance → Moonshot；consensus\_signal → DeepSeek；institution → GLM |
| ICR 验证 | **无**（不可复现性风险） | **有**：Cohen's κ（三对 pairwise）+ Fleiss' κ（三模型联合） |
| 机构词汇表 | ERC：MetaMask/EF/Coinbase/OpenAI/Independent；A2A 同 | ERC 同旧版；A2A：Google/Microsoft/Salesforce/Atlassian/Cisco/Independent |

**影响：** 这是方法论上最核心的升级——从"单一 LLM 输出即结果"变为"三独立评分员 + 信度报告"，使标注质量可量化、可审计，直接支撑顶会方法论贡献声明。

---

### 1.3 已知 ERC 标注 ICR 结果（真实数据，已写入论文）

| 字段 | DS↔GLM | DS↔KM | GLM↔KM | Fleiss' κ | 等级 |
|---|---|---|---|---|---|
| Argument Type | .691 | .634 | .730 | **0.683** | **Substantial** |
| Stance | .451 | .250 | .460 | 0.369 | Fair |
| Consensus Signal | .321 | .282 | .329 | 0.299 | Fair |
| Stakeholder Inst. | .187 | .223 | .139 | 0.161 | Slight |

三方全同意率：argument\_type 79.1%，stance 40.1%。

---

### 1.4 论文结构差异

| 章节位置 | 旧版 | 新版 |
|---|---|---|
| 标题 | *An LLM-Powered Pipeline for Comparative Governance…* | *Multi-Model LLM Triangulation for Comparative Governance…* |
| Abstract | 单模型、4,323 条 | 三模型、ERC 1,664 条 + A2A TBD |
| §1 Introduction | 贡献中无 ICR | 新增 **multi-model ICR validation** 作为第一方法贡献 |
| §2 Related Work | 2 段计算方法综述 | 新增第 3 段：**LLM annotation reliability**（Gilardi 2023, Binz 2023） |
| §3 Methodology | §3.1 数据收集 → §3.2 话语分析 → §3.3 网络分析 | **新增 §3.1 Multi-Model Annotation & ICR**，原有小节顺延 |
| §4 Results | 无 ICR 子节 | **新增 §4.1 Annotation Validation**（含 ERC ICR 表，A2A TBD） |
| §4 Results 其余 | 旧版真实数值全部填写 | **全部为 \tbd{} 占位符**（待流水线完成） |
| §5 Discussion | 3 个子节，无方法论讨论 | 同样 3 个子节，最后增加 **三条方法论启示** |
| Appendix | 6 个 App（A-F） | 6 个 App：新增 **App ICR Heatmap**，App Institution 改写为多模型版本 |
| 参考文献 | 62 条 | **71 条**（新增：cohen1960, fleiss1971, landis1977, gilardi2023, binz2023, reiss2023, deepseek2025, glm2024, moonshot2024, mcinnes\_umap\_2018） |

---

### 1.5 图表差异

| 图/表 | 旧版 | 新版 |
|---|---|---|
| ICR 表（ERC） | 无 | **Table 1 新增**（已填真实 κ 值） |
| ICR 表（A2A） | 无 | **Table 2 新增**（全部 TBD） |
| ICR Heatmap | 无 | **Figure（App）新增**（TBD） |
| Fig: argument-type pie | `topic-pie-erc.pdf` | `r2-topic-pie-erc.pdf`（TBD） |
| Fig: stance heatmap | `topic-stance-heatmap.png` | `r2-topic-stance-heatmap.png`（TBD） |
| Fig: BERTopic | `fig-bertopic-divergence.pdf` | `r2-fig-bertopic-divergence.pdf`（TBD） |
| Fig: Thematic-LM | `fig-combined-themes.pdf` | `r2-fig-combined-themes.pdf`（TBD） |
| Tab: Thematic divergence | 填写完整 | `tab:r2-themes-compact`（全 TBD） |
| Tab: SNA metrics | 填写完整 | `tab:r2-sna`（全 TBD） |
| Tab: DNA metrics | 填写完整 | `tab:r2-dna`（全 TBD） |
| Tab: Socio-semantic | 填写完整 | `tab:r2-ss`（全 TBD） |
| Fig: SNA network | `network-sna-2col.pdf` | `r2-network-sna-2col.pdf`（TBD） |
| Fig: SS entropy | `fig-ss-entropy.pdf` | `r2-fig-ss-entropy.pdf`（TBD） |

---

## 二、当前进度与待完成任务

### 2.1 标注进度（▶ 运行中，2026-06-21 13:10 重启）

三个 A2A 标注后台进程正在运行：

| 模型 | 已完成 | 剩余 | 进度 | ETA |
|---|---|---|---|---|
| deepseek-v4-flash | 1,140 条 | 3,780 | 23% | ~314 min |
| glm-4-plus | 2,280 条 | 2,640 | 46% | ~67 min |
| moonshot-v1-auto | 1,420 条 | 3,500 | 29% | ~103 min |

**监控命令：** `tail -3 logs/annotate_a2a_*.log`

标注完成后执行：`uv run python scripts/analyse/run_r2_pipeline.py`（一键跑完 Phase 2-10）

---

### 2.2 完整待办清单（按执行顺序）

```
Phase 1  ✅ ERC 标注（3 模型 × 1,664 条）— 已完成
Phase 1' ⚠ A2A 标注（3 模型 × 4,920 条）— 中断，需重启
         进度：DS 20% / GLM 39% / KM 22%
         预计剩余时间（重启后）：DS ~3.5h / GLM ~1.5h / KM ~3h

Phase 2  ⬜ A2A ICR 验证
         命令：uv run python scripts/analyse/validate_multimodel.py --dataset a2a
         输出：data/annotated/r2/a2a/validation/validation_report.json
         → 填入论文 Table 2（A2A ICR 表）和 §4.1 段落

Phase 3  ⬜ 构建共识标注（ERC + A2A）
         命令：uv run python scripts/process/build_consensus.py
         输出：data/annotated/r2/consensus/{erc,a2a}_annotations.json

Phase 4  ⬜ 结构性指标计算
         命令：uv run python scripts/analyse/compute_metrics_r2.py
         输出：analysis/r2_structural_metrics.csv
         → 填入 Abstract 中 A2A N 值，以及 §4.1 数据来源表

Phase 5a ⬜ Chi-square 检验（含 Cramér's V）
         已集成在 compute_metrics_r2.py
         → 填入 §4.2.1 argument-type 段落

Phase 5b ⬜ BERTopic
         命令：uv run python scripts/analyse/topic_discovery/comparative_discourse/run_r2.py
         → 填入 §4.2.2、Fig r2-fig-bertopic-divergence.pdf

Phase 5c ⬜ A2A Thematic 开放编码（Stage 1）
         命令（并行）：
           uv run python scripts/process/annotate_thematic_a2a.py --model deepseek &
           uv run python scripts/process/annotate_thematic_a2a.py --model glm &
           uv run python scripts/process/annotate_thematic_a2a.py --model kimi &
         注：ERC Thematic 已完成（data/annotated/r2/thematic/ 3 个模型 × 1,034 条）

Phase 5d ⬜ Thematic-LM Stages 2-4（合并 ERC + A2A open codes）
         命令：uv run python scripts/analyse/topic_discovery/thematic_lm/run_r2.py
         输出：output/topic_discovery/r2/thematic_lm/
         → 填入 §4.2.3、Tab r2-themes-compact、Fig r2-fig-combined-themes.pdf

Phase 6a ⬜ SNA 协同参与网络
         命令：uv run python scripts/analyse/build_network_r2.py
         → 填入 Tab r2-sna（15 项指标）

Phase 6b ⬜ DNA 话语网络分析
         命令：uv run python scripts/analyse/network_discourse/dna/run_r2.py
         → 填入 Tab r2-dna（10 项指标）

Phase 6c ⬜ Socio-semantic 双模网络
         命令：uv run python scripts/analyse/network_discourse/sociosemantic/run_r2.py
         → 填入 Tab r2-ss（8 项指标）

Phase 7  ✅ 生成论文图表脚本 — build_paper_figures_r2.py 已写好
         ⬜ 执行生成：uv run python scripts/visualise/build_paper_figures_r2.py

Phase 8  ✅ 论文框架写作 — 已完成（paper-extended-2/acm.tex，15 页，可编译）
         ⬜ 填写所有 76 个 \tbd{} 占位符
```

---

### 2.3 论文中 TBD 占位符清单（76 个）

按位置分类：

| 位置 | 占位符内容 | 来源阶段 |
|---|---|---|
| Abstract | A2A N 值；A2A ICR 摘要句 | Phase 4 + Phase 2 |
| §1 引言 | A2A N 值 | Phase 4 |
| §3.1 方法 | A2A N 值 | Phase 4 |
| §4.1 验证 | A2A ICR 全部 κ 值（Table 2，12 格）；A2A ICR 文字段落 | Phase 2 |
| §4.2.1 | Argument-type 分布百分比；χ² 统计量；Cramér's V；图说明 | Phase 4+5a |
| §4.2.2 | BERTopic JSD 值；Top 话题段落；图说明 | Phase 5b |
| §4.2.3 | Codebook 大小；Thematic-LM JSD；Top 话题表（整行）；图说明 | Phase 5d |
| §4.3.1 | SNA 表（15 行 × 2 列 = 30 格）；SNA 段落 | Phase 6a |
| §4.3.2 | DNA 表（10 行 × 2 列 = 20 格）；DNA 段落；JSD 比较 | Phase 6b |
| §4.3.3 | SS 表（8 行 × 2 列 = 16 格）；SS 段落 | Phase 6c |
| §5 讨论 | JSD 数值对比句；DNA density 比较句 | Phase 5b/6b |
| Appendix | 数据表文件行数；A2A 总 N；Actor filter 表（8 格）；SNA 图说明；ICR heatmap 说明 | 多个 Phase |

---

## 三、Paper 1 (旧版) 的 Robustness Check 附录 — ✅ 已完成

`paper-acm/acm.tex` 已在原来的 `\end{document}` 之前新增 **Appendix I: Multi-Model Robustness Check**（`\label{app:robustness}`），包含：

1. **Re-annotation design** — 描述三模型多数投票设计，引用 ji2026 验证框架
2. **ERC ICR 表** — 真实 3×4 pairwise κ 数据 + Fleiss' κ（Table `tab:icr-erc-rb`）
3. **A2A ICR 表** — TBD 占位（Table `tab:icr-a2a-rb`）
4. **Key finding replication** — argument-type 分布对比表 R1 vs R2（TBD）
5. **Implications** — 三条稳健性结论

编译状态：✅ 通过，13 页，0 个 undefined citation。A2A κ 值和分布对比待标注完成后填。

---

## 四、一键流水线脚本 — ✅ 已写好

`scripts/analyse/run_r2_pipeline.py` — 自动按序执行 Phase 2-10，支持：
- `--from-phase N` 断点续跑
- `--skip-thematic` / `--skip-figures` 跳过指定阶段
- `--prereq-only` 仅检查前置条件

标注完成后运行：`uv run python scripts/analyse/run_r2_pipeline.py`

---

## 五、论文当前编译状态

| 项目 | 状态 |
|---|---|
| `paper-extended-2/acm.tex` | ✅ 已写完，15 页，可编译 |
| 参考文献解析 | ✅ 71 条全部解析（0 个 undefined citation） |
| 图片文件 | ⚠ 8 个占位图（draft mode，等待 Phase 7 生成） |
| TBD 占位符 | ⚠ 76 个（红色标注，等待各分析阶段完成） |
| 与旧版 PDF 差异 | 方法论完全改写；数据量 ×4；ERC 侧 ICR 真实值已填写 |
