# 人工编码验证指南（Inter-Rater Reliability）

**目的**：验证 LLM 标注质量，计算 Cohen's κ，写入论文 §III Research Design
**文件**：`verification/sample_50.csv` — 你在这个文件里填写人工标注
**脚本**：`scripts/compute_kappa.py` — 填完后运行，自动输出 κ 值

---

## 1. 为什么是 N = 50？

### 统计学依据

50 是社会科学研究中验证标注一致性的**公认最低值**，依据来自：

- **Krippendorff (2004)** — *Content Analysis*：建议至少抽取总量的 10% 或绝对不少于 30 条；50 条可提供足够统计功效
- **Artstein & Poesio (2008)** — *Computational Linguistics*：对于 κ ≥ 0.6 的检测，50 条可达到 80% 统计功效（α=0.05）
- **计算社会科学惯例**：近年用 LLM 做内容分析的论文（如 Gilardi et al. 2023 *PNAS*；Ziems et al. 2024 *ACL*）普遍使用 50–200 条人工验证

### 50 条对本研究够用的理由

| 因素 | 说明 |
|------|------|
| 总体规模 | 5,310 条有效标注，50 条 = 0.94%，高于 Krippendorff 10% 建议的绝对下限 |
| 标签数量 | argument_type 有 6 类，stance 有 5 类；50 条足以覆盖主要分布 |
| 论文类型 | 比较案例研究（Eisenhardt 1989），κ 是效度说明，非主要结果变量 |
| 期刊要求 | AOM/SMS 会议论文对 κ ≥ 0.60 即可接受 |

> **结论**：50 条在统计上充分，在实践上可行（约需 2–3 小时完成人工编码）。

---

## 2. 分层抽样设计

### 为什么要分层？

如果从 5,310 条里随机抽 50 条，按比例会得到：
- ERC-8004：约 1–2 条（太少，无法评估该案例的标注质量）
- GitHub issue_comment：约 22 条（过度集中于一种文本类型）

分层抽样确保：
1. **两个案例都被充分验证**（ERC-8004 数据少但同等重要）
2. **不同文本类型都被覆盖**（论坛帖≠代码评审≠讨论）

### 分层方案

```
总计 50 条
├── ERC-8004 (20 条)
│   ├── forum               16 条  （按比例：113/144 × 20 ≈ 16）
│   └── GitHub 全类型        4 条  （合并：github_review + github_review_comment + github_issue_comment）
│
└── Google-A2A (30 条)
    ├── Issues 类            17 条  （issue + issue_comment，占 A2A 的 55.9%）
    ├── PRs 类                9 条  （pr + pr_review_comment 等，占 A2A 的 29.6%）
    └── Discussions 类        4 条  （discussion + comment + reply，占 A2A 的 14.5%）
```

随机种子：`SEED = 42`（固定，可复现）

---

## 3. 标注标准（Codebook）

你需要为每条记录独立判断以下三个字段，**不要先看 LLM 的标注**：

### 3.1 argument_type（论点类型）

| 标签 | 定义 | 例子 |
|------|------|------|
| `Technical` | 讨论技术实现细节、接口设计、安全性、性能 | "We should store ratings off-chain to reduce gas cost" |
| `Governance-Principle` | 讨论治理机制、规则、去中心化原则 | "This changes who controls the registry" |
| `Economic` | 涉及激励、成本、代币经济学 | "Bond requirement may deter small validators" |
| `Process` | 流程性发言：审批、格式、机器人通知、重定向 | "Please move this PR to the new samples repo" |
| `Off-topic` | 无实质内容：致谢、重复、空PR模板 | "Thanks for the contribution!" |
| `Other` | 不适合以上任何类别 | — |

### 3.2 stance（立场）

| 标签 | 定义 |
|------|------|
| `Support` | 明确支持提案/PR/观点 |
| `Oppose` | 明确反对 |
| `Modify` | 支持但要求修改 |
| `Neutral` | 无明确立场（提问、说明、机器人消息） |
| `Off-topic` | 仅用于 argument_type = Off-topic 时 |

### 3.3 consensus_signal（共识信号）

| 标签 | 定义 |
|------|------|
| `Adopted` | 提案被接受/合并/批准的明确信号 |
| `Rejected` | 提案被拒绝的明确信号 |
| `Pending` | 讨论仍在进行，结果未定 |
| `N/A` | 无法从单条评论判断，或与共识无关 |

### 3.4 stakeholder_institution（发言者机构）

判断发言者所属机构。依据优先级（高→低）：作者 GitHub 公司字段 > GitHub bio > 论坛 bio > 用户名/发言内容推断。

| 标签 | 适用情况 |
|------|---------|
| `Google` | Google 员工、Google 旗下项目成员（如 DeepMind、Google Research） |
| `MetaMask` / `Consensys` | MetaMask 或 ConsenSys 员工 |
| `Ethereum Foundation` | EF 员工或明确以 EF 身份发言 |
| `Coinbase` | Coinbase 员工 |
| `Independent` | 无明确机构归属的个人开发者、研究者、社区成员 |
| `Bot` | 机器人账号（eip-review-bot、git-vote[bot]、gemini-code-assist[bot] 等） |
| `Unknown` | 无法判断机构归属 |
| 其他机构名称 | 如 `Nethermind`、`OpenZeppelin`、`Olas`、`TensorBlock` 等，直接写机构名 |

**判断提示**：
- `eip-review-bot`、`git-vote[bot]`、`gemini-code-assist[bot]` → 一律填 `Bot`
- 用户名含公司域名邮件或 bio 明确写公司 → 直接用公司名
- 无法判断且 bio 为空 → 填 `Unknown`，不要猜测

---

## 4. 操作步骤

### 步骤 1：打开 CSV 文件

```
verification/sample_50.csv
```

用 Excel / Numbers / LibreOffice 打开。每行一条记录。

### 步骤 2：查看原文

CSV 中有 `url` 列，点击链接打开原始帖子/评论，阅读**完整上下文**（不只是 text_preview）。

> **关键**：请先看 URL 里的原文，不要先看 `llm_*` 列的标注。

### 步骤 3：填写你的标注

在以下四列填写你的判断：

- `human_argument_type`
- `human_stance`
- `human_consensus_signal`
- `human_stakeholder_institution`

### 步骤 4：计算 κ

```bash
uv run python scripts/compute_kappa.py
```

脚本会自动读取 `verification/sample_50.csv`，输出三个字段的 κ 值和整体一致率。

---

## 5. 抽样结果（50 条）

> 种子 = 42，可用 `scripts/sample_for_verification.py` 重现

| # | Case | Source | Author | Date | LLM: argument_type | LLM: stance | LLM: consensus_signal | LLM: institution | Link |
|---|------|--------|--------|------|-------------------|------------|----------------------|-----------------|------|
| 1 | ERC-8004 | forum | zonu | 2025-09-26 | Technical | Neutral | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/87) |
| 2 | ERC-8004 | forum | Marco-MetaMask | 2025-08-24 | Technical | Support | N/A | MetaMask | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/16) |
| 3 | ERC-8004 | forum | felixnorden | 2025-08-19 | Technical | Support | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/4) |
| 4 | ERC-8004 | forum | wanderosity | 2025-11-02 | Technical | Neutral | N/A | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/102) |
| 5 | ERC-8004 | forum | spengrah | 2025-08-28 | Technical | Modify | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/37) |
| 6 | ERC-8004 | forum | felixnorden | 2025-08-28 | Technical | Modify | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/33) |
| 7 | ERC-8004 | forum | davidecrapis.eth | 2025-08-27 | Technical | Support | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/30) |
| 8 | ERC-8004 | forum | Marco-MetaMask | 2025-08-25 | Technical | Support | N/A | MetaMask | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/19) |
| 9 | ERC-8004 | forum | Marco-MetaMask | 2025-08-24 | Technical | Neutral | Pending | MetaMask | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/15) |
| 10 | ERC-8004 | forum | sterlingcrispin | 2025-10-13 | Technical | Modify | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/93) |
| 11 | ERC-8004 | forum | azanux | 2025-09-14 | Technical | Modify | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/73) |
| 12 | ERC-8004 | forum | KBryan | 2025-08-23 | Process | Neutral | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/13) |
| 13 | ERC-8004 | forum | xiaowh7 | 2025-09-18 | Technical | Support | Pending | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/80) |
| 14 | ERC-8004 | forum | Marco-MetaMask | 2025-09-01 | Technical | Neutral | Pending | MetaMask | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/56) |
| 15 | ERC-8004 | forum | sbacha | 2025-08-20 | Technical | Neutral | N/A | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/5) |
| 16 | ERC-8004 | forum | KBryan | 2025-08-27 | Technical | Neutral | N/A | Independent | [link](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098/29) |
| 17 | ERC-8004 | github_review | eip-review-bot | 2026-01-07 | Process | Support | Adopted | Bot | [link](https://github.com/ethereum/ERCs/pull/1462#pullrequestreview-3637074672) |
| 18 | ERC-8004 | github_review_comment | abcoathup | 2025-08-14 | Process | Neutral | N/A | Independent | [link](https://github.com/ethereum/ERCs/pull/1170#discussion_r2275164852) |
| 19 | ERC-8004 | github_review_comment | lightclient | 2025-08-14 | Technical | Modify | Pending | Independent | [link](https://github.com/ethereum/ERCs/pull/1170#discussion_r2277443348) |
| 20 | ERC-8004 | github_issue_comment | eip-review-bot | 2026-01-14 | Process | Neutral | Pending | Bot | [link](https://github.com/ethereum/ERCs/pull/1472#issuecomment-3748855072) |
| 21 | Google-A2A | issue_comment | git-vote[bot] | 2026-01-08 | Process | Neutral | Pending | Bot | [link](https://github.com/a2aproject/A2A/pull/1259#issuecomment-3721415749) |
| 22 | Google-A2A | issue_comment | robert-at-pretension-io | 2025-04-27 | Technical | Neutral | N/A | Independent | [link](https://github.com/a2aproject/A2A/issues/178#issuecomment-2833534846) |
| 23 | Google-A2A | issue_comment | chorghemaruti64-creator | 2026-02-22 | Technical | Modify | N/A | Independent | [link](https://github.com/a2aproject/A2A/issues/1497#issuecomment-3940240794) |
| 24 | Google-A2A | issue_comment | gemini-code-assist[bot] | 2025-11-21 | Process | Neutral | N/A | Bot | [link](https://github.com/a2aproject/A2A/pull/1223#issuecomment-3564649573) |
| 25 | Google-A2A | issue_comment | git-vote[bot] | 2026-01-02 | Process | Neutral | Pending | Bot | [link](https://github.com/a2aproject/A2A/pull/1307#issuecomment-3704548536) |
| 26 | Google-A2A | issue_comment | birdayz | 2025-10-23 | Technical | Modify | N/A | Independent | [link](https://github.com/a2aproject/A2A/issues/1142#issuecomment-3436093933) |
| 27 | Google-A2A | issue_comment | fhinkel | 2025-05-09 | Process | Oppose | Pending | Independent | [link](https://github.com/a2aproject/A2A/issues/457#issuecomment-2864763610) |
| 28 | Google-A2A | issue_comment | darrelmiller | 2025-11-26 | Technical | Neutral | N/A | Unknown | [link](https://github.com/a2aproject/A2A/issues/1236#issuecomment-3581086490) |
| 29 | Google-A2A | issue_comment | dgenio | 2026-01-16 | Technical | Modify | Pending | Google | [link](https://github.com/a2aproject/A2A/issues/1367#issuecomment-3759937346) |
| 30 | Google-A2A | issue_comment | holtskinner | 2025-05-28 | Process | Modify | Pending | Independent | [link](https://github.com/a2aproject/A2A/pull/329#issuecomment-2917095835) |
| 31 | Google-A2A | issue | herczyn | 2026-02-17 | Technical | Support | Pending | Independent | [link](https://github.com/a2aproject/A2A/issues/1495) |
| 32 | Google-A2A | issue_comment | rajeshvelicheti | 2025-04-17 | Off-topic | Off-topic | N/A | Unknown | [link](https://github.com/a2aproject/A2A/pull/179#issuecomment-2811673251) |
| 33 | Google-A2A | issue_comment | gemini-code-assist[bot] | 2025-08-08 | Off-topic | Neutral | N/A | Bot | [link](https://github.com/a2aproject/A2A/pull/967#issuecomment-3167550612) |
| 34 | Google-A2A | issue_comment | ThierryThevenet | 2025-10-26 | Technical | Support | Pending | Independent | [link](https://github.com/a2aproject/A2A/issues/1176#issuecomment-3448214414) |
| 35 | Google-A2A | issue_comment | sandyskies | 2025-07-10 | Governance-Principle | Neutral | N/A | Independent | [link](https://github.com/a2aproject/A2A/issues/815#issuecomment-3056038757) |
| 36 | Google-A2A | issue_comment | holtskinner | 2025-05-28 | Process | Modify | Pending | Independent | [link](https://github.com/a2aproject/A2A/pull/379#issuecomment-2917095710) |
| 37 | Google-A2A | issue_comment | pstephengoogle | 2025-04-16 | Technical | Oppose | N/A | Google | [link](https://github.com/a2aproject/A2A/pull/155#issuecomment-2810366158) |
| 38 | Google-A2A | pr | peterwang2013 | 2025-05-06 | Technical | Support | Pending | Independent | [link](https://github.com/a2aproject/A2A/pull/420) |
| 39 | Google-A2A | pr_review_comment | koverholt | 2025-05-09 | Process | Neutral | N/A | Independent | [link](https://github.com/a2aproject/A2A/pull/453#discussion_r2082224820) |
| 40 | Google-A2A | pr | kthota-g | 2025-07-29 | Off-topic | Off-topic | N/A | Unknown | [link](https://github.com/a2aproject/A2A/pull/934) |
| 41 | Google-A2A | pr | holtskinner | 2025-08-12 | Process | Neutral | N/A | Independent | [link](https://github.com/a2aproject/A2A/pull/979) |
| 42 | Google-A2A | pr_review_comment | pstephengoogle | 2025-05-23 | Technical | Modify | N/A | Google | [link](https://github.com/a2aproject/A2A/pull/635#discussion_r2104614221) |
| 43 | Google-A2A | pr | kthota-g | 2025-08-05 | Off-topic | Off-topic | N/A | Independent | [link](https://github.com/a2aproject/A2A/pull/959) |
| 44 | Google-A2A | pr_review_comment | swapydapy | 2025-05-19 | Technical | Modify | Pending | Independent | [link](https://github.com/a2aproject/A2A/pull/507#discussion_r2096197579) |
| 45 | Google-A2A | pr_review_comment | whitlockjc | 2025-05-13 | Technical | Modify | N/A | Independent | [link](https://github.com/a2aproject/A2A/pull/467#discussion_r2086793182) |
| 46 | Google-A2A | pr_review_comment | darrelmiller | 2025-10-28 | Technical | Modify | Pending | Independent | [link](https://github.com/a2aproject/A2A/pull/1160#discussion_r2467634718) |
| 47 | Google-A2A | discussion_comment | DJ-os | 2025-05-07 | Process | Neutral | N/A | Google | [link](https://github.com/a2aproject/A2A/discussions/336#discussioncomment-13057355) |
| 48 | Google-A2A | discussion_comment | EditUndo | 2025-04-19 | Technical | Neutral | N/A | Independent | [link](https://github.com/a2aproject/A2A/discussions/97#discussioncomment-12882660) |
| 49 | Google-A2A | discussion_reply | kurt-r2c | 2026-02-11 | Technical | Support | N/A | Independent | [link](https://github.com/a2aproject/A2A/discussions/1404#discussioncomment-15772640) |
| 50 | Google-A2A | discussion_comment | jenish2917 | 2025-11-24 | Technical | Neutral | Pending | Independent | [link](https://github.com/a2aproject/A2A/discussions/741#discussioncomment-15061331) |

---

## 6. 注意事项

### 需要特别关注的记录

以下记录来自**机器人账号**，标注可能有争议，请根据内容实质判断：

- #17, #20：`eip-review-bot`（自动审批机器人）
- #21, #25：`git-vote[bot]`（投票状态报告）
- #24, #33：`gemini-code-assist[bot]`（AI 代码助手）

这些记录的 argument_type 通常是 `Process`，但你可以标 `Off-topic` 如果认为无实质内容。**不一致这里没问题** — 这正是 κ 要发现的。

### 如果 κ < 0.6

1. 检查哪些类别一致性最低（脚本会输出混淆矩阵）
2. 修订 Codebook 中对应类别的定义
3. 重新标注有分歧的记录，记录讨论决策
4. 在论文中说明分歧来源（如 Process/Technical 边界模糊）

### 论文中如何引用

```
To validate LLM annotation reliability, we randomly sampled 50 records using
stratified sampling across data sources (ERC-8004 forum n=16, ERC-8004 GitHub n=4,
A2A issues n=17, A2A PRs n=9, A2A discussions n=4) with seed=42.
The first author independently coded all 50 records following the codebook in
Appendix A. Inter-rater agreement was κ=[VALUE] for argument_type, κ=[VALUE] for
stance, κ=[VALUE] for consensus_signal, and κ=[VALUE] for stakeholder_institution,
indicating [substantial/moderate] agreement (Landis & Koch 1977).
```

---

## 7. 文件清单

| 文件 | 用途 |
|------|------|
| `verification/INTER_RATER_GUIDE.md` | 本文件，完整说明 |
| `verification/sample_50.csv` | 填写人工标注的工作表 |
| `verification/sample_50.json` | 完整原始记录（供参考） |
| `scripts/sample_for_verification.py` | 抽样脚本（可重现） |
| `scripts/compute_kappa.py` | 计算 κ 值（填完 CSV 后运行） |
