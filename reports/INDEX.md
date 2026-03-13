# 研究进展报告索引

**项目**: RQ1 — DAO 治理 vs. 企业治理（ERC-8004 vs. Google A2A）
**目标**: AOM/SMS 会议论文（TIM track）

---

## 报告列表

| 编号 | 日期 | 标题 | Git 范围 | 状态 |
|------|------|------|----------|------|
| [R01](./R01_2026-03-10_数据采集与基础设施.md) | 2026-03-10 | 数据采集与基础设施搭建 | `332eb5a`–`48b7e1b` | 完成 |
| [R02](./R02_2026-03-10_数据清洗与A2A采集.md) | 2026-03-10 | 数据清洗、Google A2A 采集、脚本重构 | `40dbe1d`–`48b7e1b` | 完成 |
| [R03](./R03_2026-03-11_LLM标注与API测试.md) | 2026-03-11 | MiniMax API 测试、缺页补漏、全量标注启动 | `5187b0f`–`731baa6` | 完成 |
| [R04](./R04_2026-03-12_LLM标注结果与治理指标.md) | 2026-03-12 | LLM 标注结果与治理指标全量 | `253a934` | 完成 |
| [R05](./R05_2026-03-13_利益相关者画像与关系网络.md) | 2026-03-13 | 利益相关者画像、机构富化与关系网络 | — | 完成 |

---

## 数据资产快照（截至 R03）

### ERC-8004（Case A，DAO 治理）

| 文件 | 内容 | 记录数 |
|------|------|--------|
| `data/raw/forum_posts.json` | Ethereum Magicians 论坛帖子 | 113 |
| `data/raw/github_comments.json` | GitHub 评论（原始，含生态系 PR） | 149 |
| `data/raw/github_comments_filtered.json` | GitHub 评论（过滤后，核心 lifecycle PR）| 11 |
| `data/raw/filter_log.json` | 过滤日志（保留/丢弃明细） | — |

### Google A2A（Case B，企业治理）

| 文件 | 内容 | 记录数 |
|------|------|--------|
| `data/raw/a2a_commits.json` | Commits（含作者、消息、日期） | 522 |
| `data/raw/a2a_issues.json` | Issues + issue comments（含补漏）| 3,104 |
| `data/raw/a2a_prs.json` | PRs + PR review comments（含补漏）| 1,955 |
| `data/raw/a2a_manifest.json` | 采集元数据 | — |

### 完整性校验

`data/raw/CHECKSUMS.json` — 所有数据文件的 SHA-256 checksum，每次数据更新后重新生成。

---

## 当前治理指标（结构层，不含 LLM 标注）

| 指标 | ERC-8004（DAO） | Google A2A（企业） |
|------|:---:|:---:|
| 治理类型 | Permissionless DAO | Corporate Hierarchy |
| 提案/首次公开 | 2025-08-13 | 2025-04-09 |
| 首次 commit | — | 2025-03-25（早于公开 15 天）|
| 共识达成 | 2026-01-29 | 持续迭代 |
| **从提案到共识（天）** | **169** | N/A |
| 讨论总记录 | 124 | 4,923 |
| 不重复贡献者 | 62 | 596 |
| commit 作者 | — | 131 |
| PR 合并率 | — | 66.2%（755 PR，500 合并）|
| 论坛回复率 | 0.46 | — |
| Openness index | **1.000** | **0.956** |
| 机构分布 | Independent 81.5%，MetaMask 9.7% | Independent 64.1%，Google 23.0% |

---

## 脚本清单

| 脚本 | 功能 | 运行命令 |
|------|------|---------|
| `scrape_erc8004.py` | 采集 ERC-8004 论坛 + GitHub 数据 | `uv run python scripts/scrape_erc8004.py` |
| `filter_github.py` | 过滤 GitHub 数据，保留核心 lifecycle PR | `uv run python scripts/filter_github.py` |
| `scrape_a2a.py` | 采集 Google A2A GitHub 数据 | `uv run python scripts/scrape_a2a.py --github-token $TOKEN` |
| `patch_a2a_missing_pages.py` | 补漏超时缺失的分页数据 | `uv run python scripts/patch_a2a_missing_pages.py` |
| `annotate_llm.py` | LLM 标注（MiniMax-M2.5 默认）| `uv run python scripts/annotate_llm.py --backend minimax` |
| `compute_metrics.py` | 计算治理指标，生成对比表 | `uv run python scripts/compute_metrics.py` |

---

## Git 里程碑

| Tag | Commit | 描述 |
|-----|--------|------|
| `v0.1-data-collection` | `48b7e1b` | ERC-8004 数据采集完成 |
| `v0.2-a2a-data` | `2f5dcf4` | A2A 首次完整采集 |
| `v0.3-a2a-complete` | `1ad220c` | A2A 缺页补漏完成（4,923 条）|
| `v0.4-annotation` | 待创建 | 全量标注完成后打 tag |
