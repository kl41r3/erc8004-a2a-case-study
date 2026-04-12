# Topic Discovery — Extended Analysis

**Initiated:** 2026-04-10  
**Status:** Method 1 DONE ✓ · Method 2 DONE ✓ · Paper sections written ✓

## 背景 / Why this folder exists

`round-b-analysis/topic-analysis.md` 记录的是基于 LLM 已有 annotation（`argument_type` 字段）的分布分析——即"用已知标签做统计"。

本文件夹做的是**完全不同的事**：把 4,372 条原始文本当作无标签裸数据，用无监督/LLM 方法重新发现内容结构，回答"数据里自然涌现出什么主题/话题"。

## 数据来源

`data/annotated/annotated_records.json` — 取 `raw_text` 字段，过滤掉：
- bot 作者（`github-actions[bot]` 等）
- 文本少于 20 字符的记录
- 非 `ERC-8004` / `Google-A2A` case

有效记录：**4,372 条**（ERC-8004: 142 条，Google-A2A: 4,230 条）

## 两种方法

| | Method 1 | Method 2 |
|---|---|---|
| **名称** | Thematic-LM | Comparative Discourse |
| **来源** | ACM Web Conference 2025, DOI: 10.1145/3696410.3714595 | ACM SMSociety 2020, DOI: 10.1145/3400806.3400816 |
| **核心思路** | 4 个 LLM Agent 协作：open coding → 聚类 → 精炼 codebook → 分配主题 | BERTopic（embedding 聚类）+ Jensen-Shannon 散度跨案例对比 |
| **是否需要 LLM API** | 是（MiniMax M2.5） | 否（本地 sentence-transformers） |
| **状态** | Stage 1 运行中（119/5421 已编码） | **完成** |
| **详细文档** | [method1-thematic-lm.md](method1-thematic-lm.md) | [method2-comparative-discourse.md](method2-comparative-discourse.md) |

## 代码位置

```
scripts/analyse/topic_discovery/
├── thematic_lm/
│   ├── run.py       # 入口：uv run python ... [--backend minimax] [--limit N]
│   ├── pipeline.py  # 4阶段流程 + checkpoint/resume
│   ├── agents.py    # LLM 调用封装（含 6 次重试，500 错误不崩溃）
│   └── prompts.py   # 所有 prompt 模板
└── comparative_discourse/
    ├── run.py       # 入口：uv run python ... [--n-topics 20]
    ├── model.py     # BERTopic 拟合
    └── compare.py   # JS 散度 + 可视化
```

## 输出位置

```
output/topic_discovery/
├── thematic_lm/
│   ├── stage1_codes.json      # checkpoint：每条记录的 open code（可中断恢复）
│   ├── stage2_clusters.json   # raw theme clusters
│   ├── stage3_codebook.json   # 精炼后的 codebook
│   ├── coded_records.json     # 最终：每条记录 → theme_id
│   └── themes.json            # codebook 副本（最终输出）
└── comparative_discourse/
    ├── divergence_table.csv   # 每个 topic 在两个 case 的占比 + abs_diff ✓
    ├── topics_per_case.json   # 全局 JS 散度 + top 5 分歧 topic ✓
    └── topic_comparison.png   # 横向条形图对比图 ✓
```
