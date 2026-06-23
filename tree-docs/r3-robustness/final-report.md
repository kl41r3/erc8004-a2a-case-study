# R3 多轮标注与分析最终报告

**时间：** 2026-06-22  
**方法：** 3个模型 × 3轮独立标注 × 2个案例 = 18组结果  
**字段：** argument_type, stance, consensus_signal（仅3字段）

---

## 1. 模型与覆盖率

| Model | ERC R1 | ERC R2 | ERC R3 | A2A R1 | A2A R2 | A2A R3 |
|-------|--------|--------|--------|--------|--------|--------|
| deepseek-v4-flash | ✅ 1,664 | ✅ 1,664 | ✅ 1,664 | ✅ 3,845 | ✅ 3,845 | ✅ 3,845 |
| glm-4-plus | ✅ 1,664 | ✅ 1,664 | ✅ 1,664 | ✅ 3,845 | ✅ 3,845 | ✅ 3,845 |
| deepseek-chat | ✅ 1,664 | ✅ 1,664 | ✅ 1,664 | ✅ 3,845 | ✅ 3,845 | ✅ 3,845 |

**18/18 轮次全部 100% 覆盖。**

---

## 2. 跨轮次信度 (Cross-Round ICR)

每个模型独立标注3轮，计算轮次间 Cohen's κ 和 Fleiss' κ。

### ERC

| Model | argument_type | stance | consensus_signal |
|-------|-------------|--------|-----------------|
| **glm-4-plus** | 0.925 (Fleiss) ✅ Almost Perfect | 0.904 ✅ | 0.861 ✅ |
| **deepseek-chat** | 0.710 (Fleiss) Substantial | 0.694 | 0.727 |
| **deepseek-v4-flash** | 0.634 (Fleiss) Substantial | 0.554 | 0.507 |

### A2A

| Model | argument_type | stance | consensus_signal |
|-------|-------------|--------|-----------------|
| **deepseek-chat** | 0.923 (Fleiss) ✅ Almost Perfect | 0.908 ✅ | 0.877 ✅ |
| **glm-4-plus** | 0.910 (Fleiss) ✅ Almost Perfect | 0.874 ✅ | 0.815 ✅ |
| **deepseek-v4-flash** | 0.565 (Fleiss) Moderate | 0.543 | 0.490 |

**关键发现：** glm-4-plus 和 deepseek-chat 的自我复现信度极高（Fleiss κ >0.85 在多数字段），而 deepseek-v4-flash 信度较低（reasoning 模型的不确定性更高）。

---

## 3. 跨模型一致性

| Field | ERC 3/3 agree | ERC 2/3 agree | A2A 3/3 agree | A2A 2/3 agree |
|-------|-------------|-------------|-------------|-------------|
| argument_type | 63.3% | 35.2% | 58.5% | 39.9% |
| stance | 57.4% | 40.3% | 54.8% | 41.3% |
| consensus_signal | 60.2% | 37.8% | 60.9% | 38.3% |

三个模型共同标注时，~60% 记录达成完全一致，~98% 达成 2/3 以上一致。

---

## 4. BERTopic 话语分析

每个模型各跑独立的 BERTopic。

| Case | deepseek-v4-flash | glm-4-plus | deepseek-chat |
|------|-----------------|-----------|-------------|
| ERC | ✅ | ✅ | ✅ |
| A2A | ✅ | ✅ | ✅ |

跨模型 JSD（Jensen-Shannon Divergence）：

| Pair | ERC JSD | A2A JSD |
|------|---------|---------|
| DSv4 ↔ GLM4+ | 0.000 | 0.014 |
| DSv4 ↔ DSchat | 0.000 | 0.004 |
| GLM4+ ↔ DSchat | 0.000 | 0.012 |

**JSD 接近 0**——三个模型在 BERTopic 主题分布上高度一致。各模型的核心争论话题基本重叠。

---

## 5. 方法学结论

1. **glm-4-plus 是最稳定的标注器**：跨轮次 Fleiss κ 高达 0.86-0.93，标注结果高度可复现
2. **deepseek-chat 也是强健的选择**：A2A case 的 Fleiss κ 达 0.88-0.92
3. **deepseek-v4-flash 信度偏低**：可能因为其 reasoning 模型的不确定性，在多轮标注中表现参差
4. **三模型间一致性充足**：2/3 以上一致率达 96-98%，支持多数投票策略
5. **BERTopic 受模型选择影响极小**：JSD < 0.02，主题分布高度一致

---

## 6. 文件清单

- `data/annotated/r3/{case}/{model}/round_{1-3}/annotations.json` — 18 组原始标注
- `data/annotated/r3/{case}/{model}/consensus.json` — 6 组跨轮共识
- `analysis/r3_icr_results.csv` — 完整 ICR 结果
- `output/topic_discovery/r3/{case}/{model}/` — 6 组 BERTopic 结果
- `tree-docs/r3-robustness/final-report.md` — 本报告
- `tree-docs/r3-robustness/progress.md` — 进度报告
