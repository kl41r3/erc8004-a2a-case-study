These tasks are seperated, so do them one-by-one. Understand these tasks and set a plan for yourself, don't use my boxes directly. After you finish your plan, go back and check these boxes that I set for you. Check them only with confidence. 

You are allowd to edit this file --- but only ckeck the boxes.
(ps: you can leave comments below, as stingers ：-) 


### 20260313
- [x] 把两个含有gitvote的pr数据扒下来并处理分析(除了基本的标注之外，关注一下内容说了什么，为什么要投票表决)：https://github.com/a2aproject/A2A/pull/1206；https://github.com/a2aproject/A2A/pull/831。
- [x] 把https://github.com/a2aproject/A2A/discussions/ 里的数据也扒下来（放到`a2a_discussion.json`, 你需要新建这个文件），同时做好数据标注。更新`a2a_manifest.json`
- [x] `scripts/scrape_erc8004.py` 里面只保留scrape 论坛数据的代码，同时改名为`scrape_erc8004_forum.py`
- [x] `github_comments` and `github_comments_filtered`只保留一个，目前这两个文件里的内容都是9个关键pr的内容。
- [x] html Google的颜色换成绿色(现在颜色太相近看不清)，同时加上实线和虚线分别什么意思的标注（全英文）。
- [x] 把data和script里每个文件是什么，做什么，整理到`README.md`，并在`README.md`里给出项目结构图。全英文。言简意赅即可。这个文件是给别人看的。

当数据全部处理完毕之后：
- [x] 重新整理一份全英文的文件，说明获取了哪些数据，怎么处理的，在哪些文件中查看。然后给出最终得到了什么指标（包括你处理过的数据，以及你在本地报告中提到的所有数据指标），具体到用什么方法计算的，用的脚本还是llm判断等细节，如果是代码，准确到`文件名-第几行到第几行`，方便我核验。这个文件是给我看的。
- [x] 刷新SHA-256 目前的SHA-256没有包括修改过的数据。

论文的前期准备：
- [x] 综合考虑，给出理论的reference list。可以自己去找文章引用，记得引用的都要顶刊，比如IEEE和AMO。如果不是顶刊或者经典，必须要特殊的理由。
- [x] 对于数据进行综合的解读。从每个结论进行推理。注意，我们的一个重要落脚点是创新机制。
- [x] 写一份markdown文件，给我一些我论文的每个部分能用的词汇和短语。尤其是一些专业领域内的”行话”，这套”叙事”。我在自己写论文的时候重点参考这份文件。
- [x] 自己新建一个文件夹，然后在建一个`dft.tex`文件，在里面用IEEE格式给出一篇完整的论文。我希望你分步、仔细考虑这个问题。这不是让你代替我完成，而是你作为claude code会如何尽全力地给这个项目做出一份汇报。我希望你给我帮助，这最终目的是促进我自己的思考。请尽力完成这个事情，体现你的深度和专业性。


### 20260314

现在我们要做一点git版本管理和数据整理的工作。`verification` and `human-notes`这两个文件夹直接无视。

重新计算`annotated`的数据的SHA。**直接在对话中先完成institution的数据处理，生成图表，然后再做后面的处理。**

更新`output/preparation/DATA_AND_METRICS.md` 和 `output/preparation/data_interpretation.md`. `output/preparation`这个文件夹里面的内容是给我自己看的。

我希望你把`script`里的脚本按照功能都整理一下。比如scrape功能的文件都放在`script/scrape`这个文件夹下。别让我看见零散的东西。这可能涉及到路径的修改。接下来，修改`README.md`. 现在我希望你在`analysis`, `data`, `output`, `scripts` 这几个文件夹下分别建立md文档，记录这个文件夹中每个文件的作用。原来的`README.md`把文件说明相关的信息都删掉。

重写`output/finding_summary.md`. 言简意赅，这个是给读论文的大家看的。

根据我们最新的讨论结果，更新`paper/draft/dft.tex`.

这是我们最后一次动data了，可以打一个小的v更新。






好，现在我对现有可视化有了准确了解。深度讨论如下：

  ---
  现有可视化的核心问题

  当前 HTML 的实质：一个 vis-network 力导向图，节点 = 人（大小 = 记录数，颜色 = 机构），边有两类——实线（直接
  reply）、虚线（co-participation，即同一 PR 下出现过）。技术上能跑，但对论文而言信息密度太低，关键治理信号几乎不可读。

  具体问题逐条拆解：

  1. 边没有方向

  edges: { arrows: { to: false } }
  A reply B 和 B reply A 在图里是同一条线。但在治理分析里，方向决定了谁在回应谁，哪个人是"被回应者"（议题的核心）vs.
  哪个人是"回应者"（反应者）。dcrapis → spengrah 和 spengrah → dcrapis 的治理含义完全不同。

  2. 边没有编码 stance

  所有实线边都是同一种灰色。但每条 reply 背后都有 LLM 标注的 stance（Support/Oppose/Modify）。如果把边的颜色设为绿色=Support
  、红色=Oppose、橙色=Modify，治理过程中的争议节点会立刻从视觉上浮现出来——这是最能支撑论文论点的单一改动。

  3. Independent 灰色海洋

  70+ 个节点全是 #888888。这在视觉上把机构信号完全淹没了。但"Independent"并不是同质的——有人是 Technical 型，有人是
  Governance-Principle 型。按 argument_type 给 Independent 节点再细分颜色，比按机构分更有区分度。

  4. co-participation 边的信息量为零

  虚线表示两个人在同一个 PR 里评论过。但 lightclient ←→ dcrapis ←→ abcoathup ←→ joao1963 都出现在 PR #1170，这个 clique
  只是因为都参与了同一个 PR，并不代表他们之间有直接对话。这种边制造了假关系密度，应该换成 PR
  节点作为二部图中间层（见下面建议）。

  5. 两个账号问题未解决

  MarcoMetaMask（GitHub）和 Marco-MetaMask（论坛）在图里是同一个节点，说明 build_network.py
  合并了——这是对的。但其他跨平台账号是否合并？需要确认。

  6. A2A 图在这个框架下根本做不了

  A2A 有 610 个贡献者。力导向图在 100+ 节点时已经是毛球，610 节点是不可读的。目前的 network_a2a.html
  很可能是一个巨大的节点团，对比 ERC-8004 的意义基本为零。

  ---
  应该做什么：按研究目的分层

  你的论文核心论点是 DAO 治理 vs. 公司层级治理在标准制定过程中的差异。不同的论点需要不同的图：

  图一：时序参与图（Timeline）

  解决的问题：治理过程是线性还是迭代的？参与者什么时候进入讨论？

  X 轴 = 时间（2025-08 到 2026-01），Y 轴 = 参与者（按机构分组）。每个点 = 一条记录，颜色 = stance。能直接看出：
  - ERC-8004：大量独立参与者早期涌入，MetaMask 的 MarcoMetaMask 持续活跃全程
  - 可以对比 A2A：参与者是何时进场的，是否集中在少数 Google 员工

  这个图对管理学读者最直观，不需要懂网络分析，最适合放进论文正文。

  图二：改进后的 reply 网络（主要修改）

  保留现有力导向结构，做三个改动：
  1. 加箭头（方向）
  2. 边颜色 = stance（绿/红/橙，深灰=Neutral/Off-topic）
  3. 把 GitHub co-participation 边替换成PR 超节点：一个菱形节点代表 PR #1170，连到所有参与该 PR 的人，边方向朝外

  这样就能清楚看出：MarcoMetaMask 在哪些互动中是 Modify 者，lightclient 在 PR #1170 里的角色，spengrah 的 Oppose
  立场是否被后续讨论采纳。

  图三：两案例并排对比（论文的核心图）

  同一个 HTML，左边 ERC-8004，右边 A2A（只取 top 30 贡献者）。同样的视觉编码，同样的力学参数。

  这能直接展示两个治理形态的结构差异：
  - ERC-8004：多中心、边界模糊、Independent 节点比例高
  - A2A：高度集中、Google 节点在中心、其他贡献者是外围

  这是整篇论文最有力的单张图。

  图四（可选）：双模网络——参与者 × 论点类型

  左列 = 机构（MetaMask / EF / Independent / Google...），右列 = argument_type（Technical / Governance-Principle / Process /
   Economic）。边粗细 = 该机构对该论点类型的使用次数。

  这个图回答一个很具体的治理问题：不同机构在讨论中扮演什么角色？ MetaMask 主要做 Technical 论证还是 Governance-Principle
  论证？Google 内部贡献者的 argument distribution 是否比外部贡献者更集中？

  ---
  技术路径

  现有 vis-network 框架可以承载上面所有改动，不需要换库。边颜色和箭头是参数修改，PR 超节点是数据结构改动，时序图可以用
  D3.js（或 vis-timeline）。

  两个 HTML 的问题不在于技术框架，而在于数据编码层：颜色只用了机构（information too sparse），边只用了
  reply/co-participation（丢失了 stance、direction、weight）。

  我建议的优先顺序：
  1. 先做并排对比图（高价值，论文主图）
  2. 在 ERC-8004 图里加边的方向 + stance 颜色
  3. 把 co-participation 虚线换成 PR 超节点
  4. 时序图最后做（需要额外数据整理）

  ---
  在开始动手之前，你需要决定一件事：A2A 的网络图用什么节点范围？ 是全量 610 人、只取 top 20
  人类贡献者、还是只取那些同时参与过 ERC-8004 的人（目前是 voidcenter）？这决定了并排图的对称性和可读性。