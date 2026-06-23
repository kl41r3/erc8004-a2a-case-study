# Method 1 — Discourse Network Analysis (DNA)

**Status:** DONE ✓  
**完成时间:** 2026-04-12  
**Reference:** Leifeld, P. (2013). Reconceptualizing Major Policy Change in the Advocacy Coalition Framework: A Discourse Network Analysis of German Pension Politics. *Policy Studies Journal*, 41(1), 169–198.

## 目标

从 Actor 对 Theme 的立场（Support / Modify / Neutral / Oppose）中构建共识网络和冲突网络，回答：  
> *在 ERC-8004 与 Google-A2A 两个治理案例中，参与者的话语立场如何聚合？是否存在跨机构的共识联盟或冲突结构？*

## 方法

```
coded_records.json  ×  4,329 条 (record_id → theme_id)
annotated_records.json (author, stance, stakeholder_institution)
       │
       ▼
[Join] URL-based + composite-key join → 3,885 条 matched records
       │
       ▼
[Affiliation Matrix] Actor × Theme  (value = mean stance_val)
  stance encoding: Support=+1, Modify=+0.5, Neutral=0, Oppose=-1
       │
       ├──► [Congruence Network] edge(a,b) if same-sign stance on ≥1 shared theme
       │         weight = # themes where both actors agree
       │
       └──► [Conflict Network]   edge(a,b) if opposite stance on ≥1 shared theme
                 weight = # themes where actors disagree
       │
       ▼
[Metrics] density · Louvain modularity · polarization index · betweenness centrality
```

**参数：**
- `min_shared = 1`（至少在 1 个主题上共同表态，才算关联）
- Louvain modularity seed = 42
- Betweenness centrality: normalized, weight-aware

**Stance 编码说明：** Off-topic 记录在 join 阶段排除，Unclassified theme 同步排除。

## 结果

### ERC-8004

| 指标 | 值 |
|------|-----|
| Actors | 66 |
| Active themes | 16 / 19 |
| Records | 126 |
| Congruence edges | 318 |
| Congruence density | **0.1483** |
| Congruence modularity | 0.2886 |
| Polarization index | 0.138 |
| Conflict edges | 74 |
| Mean actor theme diversity | 1.47 |

**Top betweenness（共识网络）：**  
bransdotcom (0.061) · voidcenter (0.061) · azanux (0.059) · Marco-MetaMask (0.059) · SumeetChougule (0.057)

**最活跃主题：** T08 Trust & Security Mechanisms（48 条），T01 Protocol Specification（19 条），T18 Spec Clarifications（12 条）

### Google-A2A

| 指标 | 值 |
|------|-----|
| Actors | 710 |
| Active themes | 19 / 19 |
| Records | 3,759 |
| Congruence edges | 20,638 |
| Congruence density | 0.0820 |
| Congruence modularity | **0.2453** |
| Polarization index | **0.253** |
| Conflict edges | **2,531** |
| Mean actor theme diversity | 2.211 |

**Top betweenness（共识网络）：**  
darrelmiller (0.018) · holtskinner (0.014) · pstephengoogle (0.012) · ognis1205 (0.009) · Tehsmash (0.009)

**最活跃主题：** T06 Documentation & Examples（429 条），T18（421 条），T07（363 条），T01（332 条）

### 关键发现

1. **ERC-8004 共识密度更高**（0.148 vs 0.082）：小社区内参与者彼此更易达成话语共识，反映 EIP 流程的凝聚性。

2. **A2A 冲突规模是 ERC-8004 的 34 倍**（2,531 vs 74 edges）：大型工程项目的多元技术路线自然产生大量分歧。值得注意的是，绝对数字受样本规模影响——A2A 有 710 演员 vs ERC-8004 有 66 演员。

3. **Polarization index：A2A 更高（0.253 vs 0.138）**：A2A 中有更高比例的共识边跨越机构边界（Google、外部贡献者互动更多），而 ERC-8004 的共识更多发生在同类参与者之间。

4. **ERC-8004 话题更集中**：T08（Trust & Security）占 38.1% 的 ERC-8004 记录，是单一主导话题，而 A2A 话题分布更分散（最大 T06 占 11.4%）。

5. **Betweenness 中心性平坦化**：A2A 最高 betweenness 只有 0.018（vs ERC-8004 的 0.061），说明 A2A 中没有单一"话语枢纽"，网络更分布式。

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/network_discourse/dna/congruence_erc8004.csv` | ERC-8004 共识网络边表 |
| `output/network_discourse/dna/congruence_a2a.csv` | A2A 共识网络边表 |
| `output/network_discourse/dna/conflict_erc8004.csv` | ERC-8004 冲突网络边表 |
| `output/network_discourse/dna/conflict_a2a.csv` | A2A 冲突网络边表 |
| `output/network_discourse/dna/dna_metrics.json` | 所有指标汇总 |
| `output/network_discourse/dna/dna_comparison.png` | 双案例共识网络可视化 |

## 局限

- ERC-8004 只有 126 条有效记录（66 演员），stance 分布估算的置信区间较宽
- `min_shared=1` 是宽松标准——可能引入低质量共识边（仅 1 主题上偶然相同立场）
- Louvain 模块度对小图（N=66）结果不稳定，重跑可能略有差异（seed 固定为 42）
- 冲突绝对值受样本规模影响，未归一化比较有局限
