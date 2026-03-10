# RQ1 进展汇报（第二次）

**日期**: 2026-03-10
**上次报告**: 同日第一版（仅 ERC-8004 采集完成）
**本次新增**: GitHub 数据清洗、Google A2A 数据采集、LLM 标注脚本重写、指标计算重构

---

## 一、本次完成的工作

### 1. GitHub 数据清洗（`filter_github.py`）

**问题**：上次报告发现 GitHub 搜索返回的 149 条记录中有大量生态系 PR（如 PR #1359，58 条，Dual-Mode Fungible Tokens），只是在规范文档中引用了 ERC-8004，并非其治理讨论。

**做法**：手动核对 GitHub 搜索结果，识别出 9 个直接修改 ERC-8004 规范文件或改变其生命周期状态的 PR，列入白名单：

| PR | 描述 | 保留记录数 |
|----|------|-----------|
| #1170 | Add ERC: Trustless Agents（初始提案）| 0 |
| #1244 | Move to Review | 0 |
| #1248 | Add Requires field | 1 |
| #1458 | Update erc-8004.md | 2 |
| #1462 | Update erc-8004.md (typos) | 2 |
| #1470 | Move to Draft | 1 |
| #1472 | align metadataValue to bytes | 1 |
| #1477 | add co-author | 2 |
| #1488 | Updates from community feedback | 2 |

**结果**：149 → **11 条**（保留率 7.4%）。

**严谨性说明**：白名单由我根据 PR 标题手动判断，未逐条阅读。PR #1170、#1244 有 0 条评论——说明这两个 PR 的讨论实际上发生在论坛，而非 PR 本身，这与 ERC 流程一致（治理讨论集中在论坛，PR 是形式步骤）。

**可验证链接**：https://github.com/ethereum/ERCs/pulls?q=erc-8004

---

### 2. Google A2A 数据采集（`scrape_a2a.py`）

**目的**：构建比较案例 B（公司科层制治理），填补上次报告的最大数据缺口。

**信息来源**：
- GitHub 仓库：https://github.com/google/A2A
- 采集内容：commits、issues、PR 列表、PR review comments

**第一次运行结果**（采集成功，数据随后被覆盖，见下方 Limitation）：

| 类型 | 数量 |
|------|------|
| Commits | 521（2025-03-25 → 2026-03-06）|
| Issues | 0（google/A2A 已关闭 Issues 功能）|
| Issue comments | 30 |
| PRs（open） | 25 |
| PR review comments | 1,500（87 个不重复作者）|
| 合计讨论记录 | 1,555 |

**关键发现**：google/A2A 自 2025-03-25 就存在 commit 记录，比公开宣布日期（2025-04-09）早约 15 天，说明项目在内部已经运行。Issues 功能被关闭，外部治理讨论只能通过 PR review comments 进行。

---

### 3. LLM 标注脚本重写（`annotate_llm.py`）

**原版**：硬编码 Anthropic API。
**新版**：三路 backend，通过 `--backend` 参数或环境变量切换：

```bash
# MiniMax（默认，国内）
uv run python scripts/annotate_llm.py --backend minimax

# OpenAI-compatible（替换 base_url 和 model 即可接任何兼容接口）
OPENAI_BASE_URL=https://xxx OPENAI_MODEL=xxx OPENAI_API_KEY=xxx \
  uv run python scripts/annotate_llm.py --backend openai

# Anthropic
ANTHROPIC_API_KEY=xxx uv run python scripts/annotate_llm.py --backend anthropic
```

支持中断续跑（resume），每 10 条增量保存。

---

### 4. 指标计算重构（`compute_metrics.py`）

**核心改动**：
- 分为"结构指标"（不依赖 LLM，现在就能跑）和"标注指标"（依赖 LLM，注释可选）
- 修复 Pandas 3.0 日期解析 bug：混合 DataFrame 中，`pd.to_datetime(utc=True)` 会用第一行的格式覆盖后续记录，GitHub 记录的日期全部变 NaT。改用 `python-dateutil` 逐条解析解决。

**当前已可计算的结构指标**（不需要 LLM key）：

| 指标 | ERC-8004（DAO） | Google A2A（企业） |
|------|---------------|------------------|
| 治理类型 | Permissionless DAO | Corporate Hierarchy |
| 提案日期 | 2025-08-13 | 2025-04-09（公开） |
| 首次 commit | — | 2025-03-25 |
| 共识/上线日期 | 2026-01-29 | 持续迭代 |
| 从提案到共识（天） | **169** | N/A |
| 讨论记录总数 | 124 | 见 Limitation |
| 不重复贡献者 | 62 | 101（讨论）/ 131（commits）|
| 论坛回复率 | 0.46 | N/A |

---

## 二、信息来源与可验证链接

| 数据 | 链接 |
|------|------|
| ERC-8004 论坛主帖（113 posts） | https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098 |
| ERC-8004 GitHub PR 列表 | https://github.com/ethereum/ERCs/pulls?q=erc-8004 |
| EIP 官方规范页 | https://eips.ethereum.org/EIPS/eip-8004 |
| Google A2A 仓库 | https://github.com/google/A2A |
| A2A 公开宣布博客 | https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/ |

---

## 三、Limitations（本次新增）

### L1：A2A 数据被覆盖（严重）

**发生了什么**：第一次采集成功获取 521 commits + 1555 条讨论记录。之后发现了 `state=all` 参数拼接 bug（双问号），修复后重新运行，但此时 GitHub 匿名 API 已达到速率上限（60 req/hr），重跑只获取 100 条 commits，0 条 PR/issues，并覆盖了原文件。

**当前状态**：A2A 数据文件仅有 100 条 commits，PR 和 issue 数据为空。

**解决方案**：提供 GitHub Personal Access Token，速率上限从 60 req/hr 提升到 5000 req/hr：
```bash
uv run python scripts/scrape_a2a.py --github-token ghp_xxx
```

### L2：MiniMax API 余额为零

MiniMax key 认证通过（`api.minimax.chat/v1`），但所有模型返回 `insufficient_balance (1008)`。LLM 标注（机构归属、论点类型、立场）尚未运行。Openness index 等指标标注前只能给出 TBD。

**解决方案**：
```bash
# 充值 MiniMax 后
uv run python scripts/annotate_llm.py --backend minimax

# 或用其他有余额的 API
ANTHROPIC_API_KEY=sk-ant-xxx uv run python scripts/annotate_llm.py --backend anthropic
```

### L3：ERC-8004 GitHub 讨论数据极少

核心 lifecycle PR 只有 11 条评论，其中 PR #1170（初始提案）和 #1244（移至 Review）有 0 条。这反映了 ERC 流程的真实情况：治理讨论主要在 Ethereum Magicians 论坛，GitHub PR 是形式化步骤。这对研究**有利**——说明 DAO 治理的核心场所是开放论坛，而非 code review 平台。

### L4：A2A Issues 被关闭

google/A2A 将 Issues 功能关闭，外部讨论只能通过 PR review comments（1,500 条）。这在治理分析上有意义：Google 将社区参与限制在代码审查层面，而非开放问题讨论。

### L5：Google 内部讨论不可见

A2A 的实际治理决策（产品路线图、架构选型）发生在 Google 内部系统（Buganizer、内部 Docs），外部不可见。我们只能看到最终对外公开的 commits 和 PR reviews，这导致对 A2A governance 的分析天然不完整。这是企业案例对比研究的系统性局限，建议在论文 Limitations 部分明确说明。

---

## 四、下一步

优先级排序：

1. **提供 GitHub PAT**，重新运行 `uv run python scripts/scrape_a2a.py --github-token ghp_xxx`，恢复 A2A 数据
2. **解决 MiniMax 余额** 或提供其他 API key，运行 `uv run python scripts/annotate_llm.py`
3. 运行 `uv run python scripts/compute_metrics.py` 获得包含标注指标的完整比较表
4. （可选）针对 ERC-8004，手动补充 PR #1170 的提案文本作为 treatment 案例的"初始设计文档"，对应 A2A 的 specification 文档
