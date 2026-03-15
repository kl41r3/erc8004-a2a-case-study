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
