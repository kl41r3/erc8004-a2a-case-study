# Method 2 — Socio-semantic Bipartite Network

**Status:** DONE ✓  
**完成时间:** 2026-04-12  
**Reference:** Roth, C. & Cointet, J.-P. (2010). Social and Semantic Coevolution in Knowledge Networks. *Social Networks*, 32(1), 16–29. DOI: 10.1016/j.socnet.2009.04.005

## 目标

将参与者与 Thematic-LM 主题建模为双模（bipartite）图，量化话语劳动分工：  
> *哪些参与者横跨多个议题（generalists）？哪些只深耕单一议题（specialists）？两个案例的话语分工结构有何差异？*

## 方法

```
coded_records.json  ×  4,329 条 (record_id → theme_id)
annotated_records.json (author, stakeholder_institution)
       │
       ▼
[Actor × Theme count matrix B]
  B[actor][theme] = # comments actor made on theme
       │
       ├──► [Actor-Actor projection]   W = B @ B.T  (co-participation weight)
       │         self-loops removed
       │
       ├──► [Theme-Theme projection]   T = B.T @ B  (co-discussed by same actors)
       │
       ├──► [Actor diversity metrics]
       │         n_themes · Shannon entropy H(actor) · Gini(actor's theme counts)
       │
       └──► [Theme concentration metrics]
                 n_actors · Gini(per-actor counts) · HHI
       │
       ▼
[Cross-case] thematic overlap coefficient · gatekeepers (betweenness in actor projection)
```

**指标定义：**
- **Shannon entropy**: $H = -\sum_t p_t \log_2 p_t$，其中 $p_t$ = 演员在 topic $t$ 上的评论比例；H=0 表示只涉及一个话题
- **Gini(entropy)**: 各演员熵值的 Gini 系数，量化"话语多样性本身的集中程度"
- **Thematic overlap coefficient**: $|T_{ERC} \cap T_{A2A}| / \min(|T_{ERC}|, |T_{A2A}|)$，1.0 = ERC-8004 主题完全被 A2A 覆盖

## 结果

### ERC-8004

| 指标 | 值 |
|------|-----|
| Actors | 66 |
| Active themes | 16 / 19 |
| Actor-actor projection edges | 645 |
| Actor modularity (Louvain) | 0.1901 |
| Mean actor entropy | **0.348** |
| Median actor entropy | **0.0** |
| Gini(entropy) | 0.773 |
| Max actor entropy | 2.664 |
| Mean theme Gini (concentration) | 0.085 |
| Most concentrated theme | T08 (Trust & Security) |

**Top gatekeepers（actor-actor 投影 betweenness）：**  
Nithin-Varma (0.134) · Cyberpaisa (0.111) · SumeetChougule (0.100) · abcoathup (0.088) · Moshiii (0.088)

**T08 在 ERC-8004 中的参与率：45.5%**（30/66 演员）

### Google-A2A

| 指标 | 值 |
|------|-----|
| Actors | 710 |
| Active themes | 19 / 19 |
| Actor-actor projection edges | 59,007 |
| Actor modularity (Louvain) | 0.1814 |
| Mean actor entropy | **0.617** |
| Median actor entropy | **0.0** |
| Gini(entropy) | 0.707 |
| Max actor entropy | 3.834 |
| Mean theme Gini (concentration) | 0.453 |
| Most concentrated theme | T06 (Documentation & Examples) |

**Top gatekeepers：**  
vinoo999 (0.028) · vongosling (0.024) · ToddSegal (0.020) · princejha95 (0.019) · edenreich (0.017)

### 跨案例对比：主题参与率（按分歧排序，前 10）

| theme_id | 标签 | ERC% | A2A% | Δ |
|----------|------|------|------|---|
| T08 | Trust & Security Mechanisms | **45.5%** | 10.0% | **35.5pp** |
| T06 | Documentation & Examples | 3.0% | **21.3%** | 18.3pp |
| T01 | Protocol Specification & Versioning | **22.7%** | 11.0% | 11.7pp |
| T05 | SDK Development & Libraries | 1.5% | **11.8%** | 10.3pp |
| T15 | Tooling Fixes & Automation | 1.5% | **11.5%** | 10.0pp |
| T19 | Bug Fixes & Implementation Improvements | 4.5% | **13.9%** | 9.4pp |
| T17 | Multi-Agent Systems Architecture | 1.5% | **10.7%** | 9.2pp |
| T09 | Transport & Protocol Mechanisms | 0.0% | **8.7%** | 8.7pp |
| T04 | Task & Message Management | 1.5% | **9.6%** | 8.1pp |
| T18 | Spec Clarifications & Info Requests | 16.7% | **24.6%** | 7.9pp |

**主题重叠系数：1.0**（ERC-8004 的 16 个主题全部被 A2A 覆盖；A2A 另有 T09/T16/T04 等 3 个独有主题）

### 关键发现

1. **话语极度专业化（median H=0 in both cases）**：两个案例中，大多数参与者只评论过一个主题，话语劳动天然分工——这与 CSCW 文献中开源社区的"peripheral participation"模式一致。

2. **A2A 参与者更多元（mean H: 0.617 vs 0.348）**：A2A 的核心贡献者跨越更多话题，而 ERC-8004 的核心贡献者也只平均涉及 1.47 个主题（DNA 结果）。反映 DAO 社区的议题聚焦性。

3. **ERC-8004 话语高度集中于安全机制**：45.5% 的演员参与了 T08（Trust & Security），远高于 A2A 的 10.0%（差值 35.5pp）。说明链上治理的安全信任问题是 ERC-8004 社区的核心关切。

4. **A2A 工程实现话题主导**：T06（Documentation）、T05（SDK）、T15（Tooling）、T19（Bug Fixes）在 A2A 中参与率均超 10%，而 ERC-8004 接近 0%——反映企业开源项目以工程执行为主，而非治理原则讨论。

5. **Gini(entropy) 两案例均高**（0.773 vs 0.707）：话语多样性本身也是不均等分布的——少数 generalist 演员横跨多个议题，大多数人是单一主题 specialist。这与 Gini(degree) 的高不平等结论相互印证。

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/network_discourse/sociosemantic/actor_topic_matrix_*.csv` | Actor × Theme 计数矩阵 |
| `output/network_discourse/sociosemantic/actor_diversity_*.csv` | per-actor entropy, gini, top_theme |
| `output/network_discourse/sociosemantic/theme_concentration_*.csv` | per-theme gini, HHI |
| `output/network_discourse/sociosemantic/theme_actor_comparison.csv` | 跨案例主题参与率表 |
| `output/network_discourse/sociosemantic/ss_metrics.json` | 汇总指标 |
| `output/network_discourse/sociosemantic/specialization_compare.png` | Actor entropy 分布直方图 |
| `output/network_discourse/sociosemantic/theme_actor_comparison.png` | 主题参与率横向条形图 |

## 局限

- Actor-actor 投影（B @ B.T）对 A2A 产生 59,007 条边——网络极密，Louvain 结果受大密度图影响，模块度偏低（0.18）属正常范围
- Median entropy = 0 意味着大多数演员只发了一条评论，这在评估"专业化"时存在边际参与者干扰——更准确应只统计≥3条评论的演员
- ERC-8004 仅 66 个演员，参与率百分比的统计不确定性较高（1位演员 ≈ 1.5pp）
