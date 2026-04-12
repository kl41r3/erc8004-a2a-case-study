# Method 2 — Comparative Discourse Analysis (BERTopic)

**Status:** DONE ✓  
**完成时间:** 2026-04-10 14:39  
**Reference:** Stine & Agarwal, "Comparative Discourse Analysis Using Topic Models: Contrasting Perspectives on China from Reddit." ACM SMSociety 2020. DOI: 10.1145/3400806.3400816

## 目标

不依赖任何预设标签，用 embedding 聚类自动发现话题，再用 Jensen-Shannon 散度量化 ERC-8004 与 Google-A2A 两个 case 的话语差异。

## 方法

1. **语料**：4,372 条原始文本（ERC-8004: 142，A2A: 4,230），取前 1,000 字符
2. **Embedding**：`sentence-transformers/all-MiniLM-L6-v2`（本地，无 API 成本）
3. **降维**：UMAP（n_neighbors=15, n_components=5, cosine metric, seed=42）
4. **聚类**：HDBSCAN（min_cluster_size=10, min_samples=5）
5. **主题表示**：c-TF-IDF，nr_topics=20（实际产出 19 个有效 topic + 1 噪音类）
6. **跨案例对比**：计算每个 topic 在两个 case 中的占比，再算全局 JS 散度

## 结果

### 全局 JS 散度

```
JS divergence (ERC-8004 ‖ Google-A2A) = 0.2880
```

中等分歧（范围 0–1）。两个 case 共享部分话语空间，但差异显著。

### 主题分布对比（按分歧排序，前 10）

| topic | keywords | ERC-8004 % | A2A % | diff (abs. value) |
|-------|----------|-----------|-------|------|
| 0 | agent, agents, for, of | **67.6%** | 21.2% | 46.4pp |
| 1 | task, message, artifact | 0.0% | 8.2% | 8.2pp |
| 3 | json, a2a, proto, message | 0.0% | 7.7% | 7.7pp |
| 4 | pull, contributing, format | 0.0% | 7.2% | 7.2pp |
| 2 | this, you, pr, thanks | 0.7% | 7.7% | 7.0pp |
| 5 | python, samples, sdk | 0.0% | 5.9% | 5.9pp |
| 9 | suggestion, sap, linkedin | 2.8% | 0.9% | 1.9pp |
| 6 | version, versions, changes | 1.4% | 2.7% | 1.3pp |
| 8 | vote, favor, 2025/2026 | 0.0% | 1.2% | 1.2pp |
| 10 | pushnotificationconfig, push | 0.0% | 0.9% | 0.9pp |

### 关键发现

1. **ERC-8004 话语高度集中**：67.6% 的文本落入 Topic 0（agent 本体讨论），话题极度聚焦，符合小规模、边界清晰的 EIP 提案社区特征。

2. **A2A 话语更分散**：21.2% 在 Topic 0，其余分布在 task/message 协议设计（8.2%）、JSON/proto 技术细节（7.7%）、贡献流程（7.2%）、SDK 样例（5.9%）等，反映大型工程项目的多线程并行工作模式。

3. **A2A 独有话题**（ERC-8004 占比 0%）：json/proto 规范、贡献指引、Python SDK、投票记录、push notification 配置——均为工程实现层面，非治理原则层面。

4. **ERC-8004 相对突出**：suggestion/linkedin/company 类（Topic 9, 2.8%）——外部利益相关方发言特征。

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/topic_discovery/comparative_discourse/divergence_table.csv` | 19 个 topic 的完整对比表 |
| `output/topic_discovery/comparative_discourse/topics_per_case.json` | 全局 JS 散度 + top 5 摘要 |
| `output/topic_discovery/comparative_discourse/topic_comparison.png` | 横向双色条形图（top 20 by abs_diff） |

## 局限

- BERTopic 自动 topic 标签（`0_agent_the_to_and`）由 c-TF-IDF 关键词拼接，可读性差，需人工解读
- ERC-8004 只有 142 条，占比估算的置信区间较宽
- HDBSCAN 将噪音点归入 topic -1（已在对比中排除），A2A 噪音率未单独统计
