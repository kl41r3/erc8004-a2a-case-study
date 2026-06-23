# Network Discourse Analysis — Extended Analysis

**Initiated:** 2026-04-12  
**Status:** Method 1 (DNA) DONE ✓ · Method 2 (Socio-semantic) DONE ✓

## 背景 / Why this folder exists

`round-b-analysis/network-analysis.md` 记录的是基于 co-participation 的无向结构网络（密度、Gini、Louvain 社区检测、Borgatti-Everett 核心-外围）——即纯粹的拓扑层分析。

本文件夹做的是**话语层网络分析**：把 Thematic-LM 输出的主题标签（`coded_records.json`）与 LLM 注释的 `stance` 字段结合，回答：

> - **谁和谁在哪些议题上立场一致/对立？**（DNA 话语共识/冲突网络）
> - **谁主导哪些话题？话语劳动是否分工？**（Socio-semantic 双模网络）

## 数据来源

- `data/annotated/annotated_records.json` — author, _case, stance, stakeholder_institution
- `output/topic_discovery/thematic_lm/coded_records.json` — record_id → theme_id（T01–T19）
- 连接键：`record_id = url`（有 URL 字段时）或 `{case}_{source}_{uid}`

有效记录：**3,885 条**（ERC-8004: 126，Google-A2A: 3,759），剔除 Off-topic 和 Unclassified

## 两种方法

| | Method 1 | Method 2 |
|---|---|---|
| **名称** | Discourse Network Analysis (DNA) | Socio-semantic Bipartite Network |
| **来源** | Policy Studies Journal 2013, DOI: 10.1177/0190292813477083 | Social Networks 2010, DOI: 10.1016/j.socnet.2009.04.005 |
| **核心思路** | Actor × Theme 仿射矩阵（stance 加权）→ 共识/冲突 Actor-Actor 网络 | Actor ↔ Theme 双模图 → 投影到 Actor 网络 + Theme 网络，量化话语分工 |
| **是否需要 LLM** | 否（用已有 Thematic-LM 输出） | 否（同上） |
| **状态** | **完成** ✓ | **完成** ✓ |
| **详细文档** | [method1-dna.md](method1-dna.md) | [method2-sociosemantic.md](method2-sociosemantic.md) |

## 代码位置

```
scripts/analyse/network_discourse/
├── loader.py             # 共享数据加载（join annotated + coded_records）
├── dna/
│   ├── run.py            # 入口：uv run python ... [--min-shared N]
│   ├── build.py          # affiliation matrix → congruence/conflict networks
│   └── metrics.py        # density, modularity, polarization index, betweenness
└── sociosemantic/
    ├── run.py            # 入口：uv run python ...
    ├── build.py          # Actor × Theme count matrix → projections
    └── compare.py        # entropy, gatekeepers, cross-case thematic overlap
```

## 输出位置

```
output/network_discourse/
├── dna/
│   ├── congruence_erc8004.csv      ✓  边表：actor_a, actor_b, weight, shared
│   ├── congruence_a2a.csv          ✓
│   ├── conflict_erc8004.csv        ✓
│   ├── conflict_a2a.csv            ✓
│   ├── dna_metrics.json            ✓  density, modularity, polarization, betweenness
│   └── dna_comparison.png          ✓  双案例共识网络可视化
└── sociosemantic/
    ├── actor_topic_matrix_*.csv    ✓  Actor × Theme 计数矩阵
    ├── actor_diversity_*.csv       ✓  per-actor entropy, gini, top_theme
    ├── theme_concentration_*.csv   ✓  per-theme gini, HHI
    ├── theme_actor_comparison.csv  ✓  跨案例主题参与率对比
    ├── ss_metrics.json             ✓  汇总指标 + 跨案例 overlap
    ├── specialization_compare.png  ✓  Actor entropy 分布直方图对比
    └── theme_actor_comparison.png  ✓  横向条形图：各主题参与率
```

## 关键发现摘要

| 指标 | ERC-8004 | Google-A2A | 解读 |
|------|----------|------------|------|
| 共识网络密度 | **0.1483** | 0.0820 | ERC-8004 参与者彼此共识率更高 |
| 冲突边数 | 74 | **2,531** | A2A 明显更多异见 |
| 跨机构互动比 | 0.138 | **0.253** | A2A 跨公司交流更活跃 |
| Actor 话题多样性（mean entropy） | 0.348 | **0.617** | A2A 参与者涉及更多话题 |
| 话语分工（Gini entropy） | 0.773 | **0.707** | 两案例均存在明显分工，ERC-8004 更极端 |
| 最主导话题 | T08 Trust & Security (45.5%) | T06 Documentation (21.3%) | ERC-8004 极度集中于安全机制 |
| 主题重叠系数 | — | — | 1.0（ERC-8004 主题是 A2A 的严格子集） |
