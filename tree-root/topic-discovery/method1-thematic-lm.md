# Method 1 — Thematic-LM (Multi-Agent LLM Thematic Analysis)

**Status:** DONE ✓  
**完成时间:** 2026-04-10  
**Reference:** Thematic-LM: A LLM-based Multi-agent System for Large-scale Thematic Analysis. ACM Web Conference 2025. DOI: 10.1145/3696410.3714595

## 目标

用 4 个 LLM Agent 协作，从裸文本中归纳出 governance 话语的主题 codebook，再给每条记录分配主题。相比 BERTopic，输出的主题标签是自然语言，可直接用于论文。

## 方法：4 阶段流程

```
raw_text × 4329 条
       │
       ▼
[Stage 1] Coder Agent (批量, 每批 15 条, thinking=OFF)
  → 给每条文本生成 3–7 词的 open code
  → 输出: stage1_codes.json  {record_id → code}
       │
       ▼
[Stage 2] Aggregator Agent (单次调用, thinking=ON)
  → 采样 300/4314 个 unique codes → 聚合为 14 个 raw theme cluster
  → 输出: stage2_clusters.json  {theme_label → [codes]}
       │
       ▼
[Stage 3] Reviewer Agent (单次调用, thinking=ON)
  → 合并冗余 theme，分拆过宽 theme，写每个 theme 的描述
  → 输出: stage3_codebook.json  [{theme_id, label, description, codes}]
  → 最终: 19 个 theme (T01–T19)
       │
       ▼
[Stage 4] Theme Coder Agent (批量, 每批 15 条, thinking=ON)
  → 给每条文本分配 codebook 里最匹配的 theme
  → 输出: coded_records.json  [{record_id, theme_id, confidence}]
           themes.json         (codebook 最终副本)
```

## 最终结果

**全语料：** 4,329 条记录，19 个主题，6.8% Unclassified

**每 case 主题分布（按 ERC-8004 占比排序）：**

| theme_id | 主题标签 | ERC-8004 n | ERC% | A2A% | Δ |
|----------|---------|-----------|------|------|---|
| T08 | Trust & Security Mechanisms | 49 | **34.5%** | 4.0% | **+30.5pp** |
| T01 | Protocol Specification & Versioning | 19 | 13.4% | 7.9% | +5.5pp |
| T07 | Community Collaboration & Contributions | 14 | 9.9% | 9.9% | ≈0 |
| T18 | Spec Clarifications & Info Requests | 12 | 8.5% | 10.2% | -1.7pp |
| T03 | Agent Discovery & Registry | 7 | 4.9% | 6.3% | -1.4pp |
| T14 | Project Governance & Process | 6 | 4.2% | 4.1% | +0.1pp |
| T10 | AgentCard & Metadata Structures | 6 | 4.2% | 3.8% | +0.4pp |
| T13 | Integrations & External Systems | 6 | 4.2% | 2.2% | +2.0pp |
| T12 | Testing & Validation Tools | 5 | 3.5% | 1.2% | +2.3pp |
| T06 | Documentation & Examples | 3 | 2.1% | **10.8%** | -8.7pp |
| T09 | Transport & Protocol Mechanisms | 0 | **0%** | 3.2% | -3.2pp |
| T16 | Streaming & Real-time Communication | 0 | **0%** | 2.1% | -2.1pp |

**JS 散度（Thematic-LM）：** 0.216

### 关键发现

1. **T08（信任机制）是 ERC-8004 最主导的 discourse**：34.5% vs 4.0%（差距 30.5pp）。涵盖链上声誉评分、可验证凭证、vouch-chain、去中心化信任架构。这反映了无许可环境下治理的核心问题：如何在没有中心化权威的前提下建立可信的 agent identity。

2. **A2A 话语更分散、更偏工程实现**：文档（10.8%）、澄清请求（10.2%）、社区协作（9.9%）等主题均匀分布，反映大型工程项目的多线程工作模式。

3. **两个完全缺席于 ERC-8004 的主题**：T09（传输机制）和 T16（流式通信），表明 EIP 治理论坛不讨论底层实现细节——实现决策下放给生态系统，这本身就是一种治理机制。

4. **社区协作（T07）是唯一均衡主题**：两个 case 均约 9.9%。无论 DAO 还是企业项目，OSS 协作基础设施（PR review、合规检查、投票流程）都占据结构性固定的治理带宽份额。

## 技术说明

**Record ID 方案**：使用 `url` 字段作为主键（ERC-8004 GitHub 记录有 URL，A2A 记录均有 URL）。Forum 帖子无 URL，回退到 `ERC-8004_forum_{post_id}` 格式。这修复了早期 `post_id` 方案导致的 4245 条 A2A 记录 ID 碰撞问题。

**Stage 2 采样**：4314 个 unique codes 超出 MiniMax 上下文限制，采样 300 个（seed=42）。

**Thinking 设置**：Stage 1 关闭（`think_budget_tokens=0`，提速）；Stage 2/3/4 开启（确保概念精度）。

## 运行说明

```bash
# 全量运行（有 checkpoint，安全重启）
uv run python scripts/analyse/topic_discovery/thematic_lm/run.py --backend minimax

# 限量测试
uv run python scripts/analyse/topic_discovery/thematic_lm/run.py --limit 30
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/topic_discovery/thematic_lm/themes.json` | 19 个主题的 codebook（含 label、description、member codes） |
| `output/topic_discovery/thematic_lm/coded_records.json` | 4329 条记录 → theme_id + confidence |
| `output/topic_discovery/thematic_lm/stage3_codebook.json` | 同上，标准 Stage 3 格式 |
