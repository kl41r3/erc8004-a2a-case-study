Marco De Rossi (@MarcoMetaMask), Davide Crapis (@dcrapis) <davide@ethereum.org>, Jordan Ellis <jordanellis@google.com>, Erik Reppel <erik.reppel@coinbase.com>, "ERC-8004: Trustless Agents [DRAFT]," *Ethereum Improvement Proposals*, no. 8004, August 2025. [Online serial]. Available: https://eips.ethereum.org/EIPS/eip-8004.

ERC-8004 draft

| ERC-8004 EIP 规范 | https://eips.ethereum.org/EIPS/eip-8004 |

A2A protocal
https://a2a-protocol.org/latest/specification/


官方规范文档 (Official Specification): a2a-protocol.org

GitHub 代码仓库: github.com/a2aproject/A2A

Google Cloud 博客介绍: Agent2Agent protocol (A2A) is getting an upgrade

Google Codelabs (实操教程): Getting Started with A2A Protocol


## Data Collection

### ERC-8004
**ethereums-magicians.org**. 
合理。是ERC和EIP的发源地。
**来源**: https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098
**Results**: 113条帖子，60不重复作者。时间跨度 2025-08-14 → 2026-03-10（完整覆盖）. `forum_posts.json`

**github.com/ethereum/ERCs**
合理。提案原文的存放地。pr中搜索关键词8004得到28条pr，经过筛选得到9条直接相关的pr。包含第一个帖子（add erc）或者后续updatee的帖子（pdate ERC-8004）。剔除了只是在讨论中引用该协议，而并非直接相关的帖子。最终得到36条数据。具体如下：
```
PR #          评论数
------------------
#1170          13
#1244           7
#1248           2
#1458           3
#1462           3
#1470           1
#1472           2
#1477           3
#1488           2
```

### A2A


Google -> Linux foundation. 

data provenance
consortium governance 企业联合治理。

Done by AI:




## 如何对比两者

A2A 代表了传统公司的逻辑，而ERC-8004代表了DAO。

1. 为什么选择这两个协议（提案）？
2. 两者为什么具有代表性（specific到Google这样的公司代表）
3. 刻画出两者创新的路径（人类发挥的部分）
4. 资源分配？利益驱动？决策成本？这些理论的解释。
5. 用参数去分析并会发理论。

```
  ┌────────────┬────────────────────────────────┬──────────────────────────────┐
  │    维度    │     Linux Foundation (A2A)     │        DAO (ERC-8004)        │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 准入       │ Permissioned，需加入基金会     │ Permissionless，任何人可参与 │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 投票权来源 │ 付费会员等级                   │ Token 持有 / 链上贡献        │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 决策透明度 │ 会议记录公开，但内部讨论不透明 │ 链上投票完全可审计           │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 执行机制   │ 依赖法律协议（合同、IP归属）   │ 智能合约强制执行             │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 激励机制   │ 企业商业利益驱动               │ Token 经济激励               │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 退出成本   │ 高（法律关系、IP授权）         │ 低（卖出token即可）          │
  ├────────────┼────────────────────────────────┼──────────────────────────────┤
  │ 创新来源   │ 企业工程师，资源集中           │ 分散个体，资源碎片化         │
  └────────────┴────────────────────────────────┴──────────────────────────────┘

```  



## who governs?




## TOMORROW

**完成数据的处理和解读。完成论文的思路整理和初稿。**

Done by human:
- [ ] 我需要做的：自己去看一下github pr和论坛到底讲了什么，有人类的感受和推测。然后在用quantitative的方法去系统得到参数和结果。而不是直接吃二手结果。
- [ ] 核查指标正确性（R02）, 核验每个指标的计算方法。
- [ ] 有关author数据，最大的一些点进行人肉开盒（ bushi 人工核验。
- [ ] 复盘和Claude code的讨论，给出论文的思路。向Claude code学习论文词汇（首先复习extended abstractct）。
- [ ] 针对得到的结果，给出解读。寻找一些相关的理论和参考文献，然后给出针对case AB 的分析。对于每个指标进行分析。关注stakeholder 图谱。
- [ ] **checkpoint**: 完成论文初稿

**The Day After Tomorrow**

- [ ] 完成论文：主体内容。细节待确定。





## ERC-8004 status
29 Jan, 2026 上的mainnet。Permissionless。

  ERC-8004 目前的状态说明了一个有趣的治理现象：标准的社会接受度（14,000+ 主网交易）远超其正式合法性（仍是
  Draft）。这在传统标准化组织里是不可能发生的——A2A 不可能在 Linux Foundation
  正式批准之前就被企业大规模部署。这个差异本身就是你论文里"DAO vs. 企业治理"的一个很好的数据点。

ERC-8004 的真实状态

  正式状态：Draft（草案）

  - 官方 EIP 页面：https://eips.ethereum.org/EIPS/eip-8004
  - 提交于 2025年8月13日，至今未升至 Review 或 Final

  实际部署：已上以太坊主网

  这是关键发现——标准虽然还是 Draft，合约已经在跑了：

  ┌────────────────────┬────────────────────────────────────────────┬───────────┬───────────────┐
  │        合约        │                    地址                    │  交易数   │   部署时间    │
  ├────────────────────┼────────────────────────────────────────────┼───────────┼───────────────┤
  │ IdentityRegistry   │ 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 │ 14,849 笔 │ 2026年1月29日 │
  ├────────────────────┼────────────────────────────────────────────┼───────────┼───────────────┤
  │ ReputationRegistry │ 0x8004BAa17C55a88189AE136b182e5fdA19dE9b63 │ 2,452 笔  │ 2026年1月29日 │
  └────────────────────┴────────────────────────────────────────────┴───────────┴───────────────┘

  - Etherscan IdentityRegistry：https://etherscan.io/address/0x8004A169FB4a3325136EB29fA0ceB6D2e539a432
  - Etherscan ReputationRegistry：https://etherscan.io/address/0x8004BAa17C55a88189AE136b182e5fdA19dE9b63

  生态系统：GitHub 上 30+ 仓库

  - 官方合约仓库：https://github.com/erc-8004/erc-8004-contracts（部署了 30+ 条链）
  - 参考实现（含 74 个测试）：https://github.com/ChaosChain/trustless-agents-erc-ri
  - Rust SDK：https://github.com/qntx/erc8004
  - TypeScript SDK：https://github.com/agent0lab/agent0-ts
  - npx 脚手架工具：https://github.com/Eversmile12/create-8004-agent
  - Awesome list：https://github.com/sudeepb02/awesome-erc8004
  - 官网：https://8004.org

## DOCS
### Scripts

  第一阶段：数据采集

  scrape_erc8004.py
  采集 ERC-8004 的原始数据。两个来源：Ethereum Magicians 论坛（通过 Discourse API 拉取帖子分页），以及 GitHub
  ethereum/EIPs 仓库（搜索与 ERC-8004 相关的 PR 和评论）。输出 forum_posts.json 和 github_comments.json。用
  subprocess + curl 而非 requests，原因是 Python 3.14 的 requests 在 ethereum-magicians.org 上有 SSL EOF 问题。

  scrape_erc8004_prs.py
  看名字是 scrape_erc8004.py 的补充或替代版本，专门针对 PR 数据。可能是在发现原始脚本拉取 PR
  数据有问题后单独拆出来的，具体逻辑我没读过，需要看源码确认。

  scrape_a2a.py
  采集 Google A2A 项目（a2aproject/A2A）的 GitHub 数据：commits、issues（含 issue comments）、PRs（含 PR review
   comments）。需要传入 --github-token，因为数据量大，匿名请求很快触发 rate limit。输出
  a2a_commits.json、a2a_issues.json、a2a_prs.json。

  patch_a2a_missing_pages.py
  A2A 数据量大（issues 3000+ 条），分页采集时容易超时导致某些页缺失。这个脚本专门检测并补漏——对比已采集数据与
  API 返回的总数，找出缺口，只重新拉取缺失的页，避免全量重跑。历史上曾因 URL 参数拼接
  bug（double-?）导致数据丢失，就是靠这个脚本修复的。

  ---
  第二阶段：数据清洗

  filter_github.py
  GitHub 搜索 API 会返回所有"提到 ERC-8004"的 PR，包括依赖它的其他 ERC（Requires:
  ERC-8004）。这个脚本做白名单过滤，只保留直接修改 ERCS/erc-8004.md 或改变其 lifecycle 状态的 9 个核心
  PR（#1170、#1244、#1248 等）。把 149 条原始记录压缩到 36 条有效记录，写入 github_comments_filtered.json。

  ---
  第三阶段：LLM 标注

  annotate_llm.py
  对所有原始记录调用 LLM 打标签，每条记录标注 5 个字段：stakeholder_institution、argument_type、stance、consens
  us_signal、key_point。支持三个后端（MiniMax-M2.5 默认、OpenAI 兼容接口、Anthropic Claude）。关键设计：用复合
  ID（case + source + 主键 + date）支持中断续跑，每 10 条自动落盘。MiniMax 的推理模型会在 JSON 前输出
  <think>...</think> 块，用正则剥除后再解析。

  ---
  第四阶段：指标计算

  compute_metrics.py
  从标注结果和原始数据计算治理指标：贡献者数量、机构分布、Openness
  Index（非发起方贡献者占比）、论点类型分布、立场分布、决策速度等。输出 analysis/structural_metrics.csv 和
  output/findings_summary.md。

  ---
  第五阶段：利益相关者富化（R05 新增）

  enrich_profiles.py
  对所有作者拉取公开档案。ERC-8004 论坛作者走 Discourse API（/u/{username}.json），GitHub 作者走 GitHub
  API（/users/{username}）。顺带做跨平台身份匹配：比对 GitHub name 字段和 Discourse name 字段，找出同一人用不同
   ID 参与两个平台的情况。

  enrich_institutions.py
  把档案数据合并进标注结果，升级机构标签。优先级：GitHub company 字段 > GitHub bio 正则匹配 > Discourse bio
  正则匹配 > LLM 推断兜底。生成 626 个 canonical 作者档案（author_profiles.json），每个档案包含机构来源标记（in
  stitution_source），便于后续区分"确定"vs"推断"。

  identify_core_contributors.py
  遴选核心贡献者（ERC-8004：≥3 条记录或参与≥2 个 PR；A2A：≥50 条记录）。对每个核心贡献者推断角色（Proposer/Core
   Developer/Reviewer/Community Voice），汇总论点类型和立场分布。同时生成人工复核清单，列出前 15 名 ERC-8004
  贡献者的 GitHub 链接和 LinkedIn 搜索链接，供手动填入 manual_overrides.json。

  build_network.py
  构建两个交互式关系网络图。ERC-8004 网络：实线边来自论坛回复链（reply_to_post_number），虚线边来自 GitHub PR
  共同参与。A2A 网络：Top 50 人类作者，所有边均为 issue/PR 共同参与（虚线）。输出自包含的 HTML 文件（嵌入
  vis.js，无需服务器），同时导出 Gephi 兼容的 CSV 边列表。有一个关键 bug 修复：A2A 的 comment 类型记录不含
  issue_number/pr_number，只有 issue_url/pr_url，需要从 URL 正则提取数字才能正确建图。

  ---
  整体流向
```
  scrape_erc8004.py ──┐
  scrape_a2a.py ──────┤  原始数据
  patch_a2a_...py ────┘
          │
  filter_github.py      清洗
          │
  annotate_llm.py       LLM 标注
          │
  compute_metrics.py    治理指标
          │
  enrich_profiles.py ──┐
  enrich_institutions.py│  利益相关者画像
  identify_core_...py ──┤
  build_network.py ─────┘
```

### data

---
  data/raw/ — 原始数据，只写不改

  forum_posts.json · 113 条 · 149 KB
  ERC-8004 的 Ethereum Magicians 论坛帖子，从 Discourse API 拉取。每条记录含 post_id、post_number（帖子在话题内
  的序号）、author、raw_text、reply_to_post_number（被回复的帖子序号，用于建立回复链）、like_count。

  github_comments.json · 36 条 · 19 KB
  ERC-8004 相关的 GitHub 原始评论，来自 GitHub 搜索 API。包含所有"提到 ERC-8004"的 PR，含生态系依赖
  PR（Requires: ERC-8004）。这是过滤前的版本，在当前数据里两个文件内容相同——说明后来改了采集逻辑，scrape
  阶段就直接只拉了 36 条。

  github_comments_filtered.json · 36 条 · 19 KB
  经 filter_github.py 处理后，只保留直接修改 erc-8004.md 的 9 个核心 PR
  的评论。目前与上面大小相同，说明在当前数据快照下原始采集结果恰好就只有这 36 条（历史上曾有 149
  条，被过滤掉了）。

  a2a_commits.json · 522 条 · 514 KB
  Google A2A 仓库的 commit 历史，从 2025-03-25 首个 commit 至采集时。每条含 sha、date、author（GitHub
  用户名）、author_name（显示名）、message（commit message）、url。注意：commits 没有进入 LLM 标注，因为
  raw_text 字段是 commit message，内容太短，不适合做论点分析。

  a2a_issues.json · 3104 条 · 4.0 MB
  A2A 仓库的 issues 和 issue comments。source 字段区分 issue（issue 正文）和 issue_comment（评论）。含
  title（issue 标题）、state（open/closed）、labels。这是数据量最大的来源，patch 脚本补漏的主要对象。

  a2a_prs.json · 1955 条 · 1.7 MB
  A2A 仓库的 PRs 和 PR review comments。source 字段区分 pr（PR
  正文）、pr_review_comment（行内代码审查评论）。含 merged、merged_at、labels。PR 合并率 66.2%
  的指标就从这里算出来的。

  manifest.json · 4 个键
  ERC-8004 采集元数据：采集时间、forum_posts 数量、github_comments
  数量、数据来源列表。相当于一张采集收据，记录"这批数据什么时候、从哪里抓的"。

  a2a_manifest.json · 10 个键
  A2A 采集元数据，更详细：仓库信息、各类型记录数量（commits/issues/issue_comments/prs）、补漏状态。

  filter_log.json · 6 个键
  filter_github.py 的过滤日志：总原始数、保留数、丢弃数，以及按 PR 编号的明细（哪些 PR
  被保留、哪些被丢弃、丢弃原因）。方便事后审计过滤逻辑是否合理。

  profiles_forum.json · 2 个顶层键
  enrich_profiles.py 的 Discourse 采集结果。结构是 {"forum_profiles": {handle: {...}}, "identity_map":
  [...]}。forum_profiles 存每个作者的 bio、website、user_title、groups；identity_map 存跨平台身份匹配结果（目前
   2 对：Marco-MetaMask↔MarcoMetaMask，davidecrapis.eth↔dcrapis）。

  profiles_github.json · 39 个顶层键（每个键是一个 GitHub 用户名）
  enrich_profiles.py 的 GitHub 采集结果，key 直接是用户名，value
  是档案对象（company、bio、blog、twitter_username、location、followers）。

  CHECKSUMS.json
  9 个 raw 文件的 SHA-256 hash，人工生成，用于完整性校验。目前未覆盖 R05 新增的两个 profiles
  文件（属于待更新状态）。

  ---
  data/annotated/ — 加工产物

  annotated_records.json · 4814 条 · 7.3 MB
  整个项目最核心的文件。所有原始记录 + LLM 标注结果的合并体。每条记录在原始字段基础上增加：_case（ERC-8004 或
  Google-A2A）、annotation（含 5 个标注字段的 JSON 对象）、annotation_error（失败记录的错误信息，成功则为
  null）。

  author_profiles.json · 626 条 · 341 KB
  R05 生成，每个 canonical 作者一条记录。将论坛账号和 GitHub 账号合并去重，聚合该作者的所有标注记录，包含：最终
  机构归属及其来源（institution_source）、论点类型分布、立场分布、参与过的 PR/Issue 列表。是
  annotated_records.json 的"按人汇总"视图。

  CHECKSUMS.json
  目前只有 annotated_records.json 一个文件的 hash，author_profiles.json 尚未加入（R05 后需更新）。

## why this data?

  核心问题：数据的可比性

  这里有一个根本性的不对称，需要在论文里正视：

  ERC-8004 的治理数据，是治理行为本身的直接记录。
  论坛上的争论就是决策过程。谁发帖、说什么、被回应了什么——这就是治理。

  A2A 的 GitHub 数据，是治理结果的后验记录。
  Google 内部如何决定要做 A2A、如何选择那 50 家合作伙伴、为什么在那个时间点捐赠给 Linux
  Foundation——这些关键决策完全不在公开数据里。你能看到的是 2025年4月之后的"后期精修"讨论，不是"创立"过程。

  ERC-8004:  [公开讨论] → [公开决策] → [链上部署]
                ↑ 你有这部分数据

  A2A:  [Google 内部] → [发布] → [公开讨论] → [Linux Foundation]
                            ↑ 你只有这之后的数据

  ---
  值得收集的 A2A 数据，以及为什么

  高价值（建议收集）

  1. GitHub Issues + PR 评论
  - 为什么：是最能反映技术争论和多方博弈的公开记录
  - 抓取方式：GET /repos/a2aproject/A2A/issues?state=all&per_page=100
  - 注意：重点看高评论量的（issue #1206 有 58 条，#1259 有 47 条）——这些是真正有争议的决策点

  2. TSC 投票记录
  - 为什么：gitvote 机制让 TSC 的正式表决留在 PR 评论里，是最接近"投票记录"的数据
  - 抓取方式：搜索包含 /gitvote 关键词的 PR 评论
  - https://github.com/a2aproject/A2A/pulls?q=gitvote

  3. GOVERNANCE.md 版本历史
  - 为什么：治理规则本身的演变（git blame / git log 可查），能看出权力结构如何被修改
  - git log -- GOVERNANCE.md

  4. 贡献者网络
  - 为什么：100 个贡献者里，Google 员工 vs. 其他公司员工 vs. 独立开发者的比例，是衡量"去中心化程度"的直接指标
  - 抓取方式：GET /repos/a2aproject/A2A/contributors，再对每人查 /users/{login} 里的 company 字段

  中等价值（视研究问题而定）

  5. CHANGELOG.md
  - 版本节奏（v0.1→v1.0 用了 10 个月）和 breaking change 频率，反映决策速度

  6. 唯一的 ADR（adr-001）
  - 内容是关于 ProtoJSON 序列化的决策，包含"考虑了哪些方案、为什么选这个"——是罕见的正式决策推理文档

  低价值/无法收集

  Discord：无 API，内容短暂，即使能抓也不完整

  TSC 会议录像：可能需要 Linux Foundation 账号，且视频内容难以结构化分析

  Google 发布前的内部讨论：永远不可得

  ---
  对论文框架的建议

  鉴于这个不对称性，你有两个方向可以选：

  方向 A：接受局限，明确标注
  承认 A2A 的"创立期"数据不可得，只比较"正式化之后"的治理行为。把这个局限作为 Limitation 章节如实写出。

  方向 B：把这个不对称本身作为发现
  "为什么 ERC-8004 的治理过程是完全透明的而 A2A 不是"——这本身就是两种治理模式的根本差异。DAO
  的治理在设计上就是公开可审计的；企业治理在设计上就是内部的。这不是数据缺失，这是研究发现。

  方向 B 对于 AOM/SMS 这类管理学会议更有理论贡献——你在揭示的不只是"谁赢了"，而是两种治理哲学对透明度的不同假设。

### some
两种治理模式的根本差异不在于参与者是否为机构（两者都是），而在于治理基础设施对参与者权力的约束方式不同。DAO
  治理用代码和公开性约束机构权力；企业/基金会治理用合同和成员资格约束。
