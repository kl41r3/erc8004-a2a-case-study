# 可视化阅读说明书 / Visualization Reading Guide

## 总览 / Overview

本研究共生成 **6 个可视化文件**，分为 4 种图表类型，覆盖两个案例（ERC-8004 DAO 治理 vs Google A2A 企业治理）。每张图服务于不同的分析目的，建议按以下顺序阅读。

This study produces **6 visualization files** across 4 diagram types, covering two cases (ERC-8004 DAO governance vs Google A2A corporate governance). Each diagram serves a distinct analytical purpose; reading in the order below is recommended.

---

## 推荐阅读顺序 / Recommended Reading Order

```
timeline_erc8004.html       ← 先建立时间感 / Orient yourself in time first
network_erc8004.html        ← 再看关系结构 / Then examine relational structure
network_a2a.html            ← 对比案例 / Compare the other case
network_compare.html        ← 并排比较 / Side-by-side structural comparison
bipartite_erc8004.html      ← 分析论证角色 / Analyze argumentative roles
bipartite_a2a.html          ← 对比论证结构 / Compare argumentative structure
```

---

## Diagram 1 — 时间轴 / Timeline

**文件 / File:** `output/timeline_erc8004.html`

### 图表构成 / What You See

| 元素 / Element | 含义 / Meaning |
|---|---|
| X 轴 / X-axis | 时间（2025年8月 → 2026年2月）/ Date |
| Y 轴 / Y-axis | 每位参与者各占一行，按机构分组排列 / One row per participant, grouped by institution |
| 每个点 / Each dot | 一条标注记录（一篇帖子或评论）/ One annotated record |
| 点的颜色 / Dot color | 该记录的 Stance（立场）/ Stance of that record |
| 行背景色 / Row band | 所属机构（深色色调）/ Institution affiliation |
| 行标签颜色 / Label color | 机构颜色编码，与其他图一致 / Institution color, consistent across diagrams |

### 颜色编码 / Color Legend

| 颜色 / Color | 立场 / Stance | 含义 / Meaning |
|---|---|---|
| 绿色 | Support | 明确支持提案 / Explicit endorsement |
| 红色 | Oppose | 明确反对 / Explicit rejection |
| 橙色 | Modify | 支持但要求修改 / Conditional support with change requests |
| 灰色（浅）| Neutral | 提问、澄清、中性描述 / Questions, clarifications, neutral |
| 灰色（深）| Off-topic | 离题内容 / Off-topic content |

### 如何阅读 / How to Read

1. **滚动查看全部参与者**（Y 轴可滚动）。
   *Scroll vertically to see all participants.*

2. **悬停在点上**查看详细信息：日期、作者、机构、立场、论证类型、关键摘要。
   *Hover over any dot for: date, author, institution, stance, argument type, key point.*

3. **观察时间分布**：讨论是前期密集还是持续均匀？某个机构是否在特定时段集中发言？
   *Look at temporal density: was debate front-loaded or distributed? Did any institution enter late?*

4. **观察行的疏密**：记录多的行（点多）= 该参与者贡献量大。
   *Dense rows = high-volume contributors.*

### 关键解读问题 / Key Interpretive Questions

- ERC-8004 讨论是否存在明显的"讨论爆发期"？
  *Are there visible bursts of debate activity?*
- MetaMask（橙色标签）的参与分布 vs Ethereum Foundation（蓝色标签）是否不同？
  *Does MetaMask's participation pattern differ from EF's?*
- Oppose（红色点）集中在哪个时间段？这是否对应某次重大技术争议？
  *When do Oppose dots cluster? Does this correspond to a known technical dispute?*

---

## Diagram 2 — 关系网络图 / Stakeholder Network

**文件 / Files:** `output/network_erc8004.html`（ERC-8004）和 `output/network_a2a.html`（A2A）

### 图表构成 / What You See

| 元素 / Element | 含义 / Meaning |
|---|---|
| 节点（圆形）/ Round nodes | 参与者（作者）/ Participant (author) |
| 节点大小 / Node size | 贡献量（记录数）/ Contribution volume |
| 节点填充色 / Node fill color | 所属机构 / Institution affiliation |
| 节点边框粗细 / Border width | 数据置信度（见下表）/ Data confidence level |
| 菱形节点 / Diamond nodes | GitHub PR（ERC-8004 专有）/ GitHub PR node |

#### 节点边框 = 数据来源置信度 / Node Border = Data Confidence

| 边框粗细 / Border | 来源 / Source | 含义 |
|---|---|---|
| 粗（3.5px）| Confirmed | 直接证据（GitHub 公司字段、EIP 邮件）|
| 中粗（2.5px）| Strong | LinkedIn / 组织成员资格核实 |
| 中（2px）| Probable | 间接线索（句柄名称、bio 推断）|
| 细（1px）| LM_inferred | LLM 自动推断，未人工核实 |

### 边的类型 / Edge Types

| 边样式 / Edge style | 类型 / Type | 含义 / Meaning |
|---|---|---|
| 实线 + 箭头，绿色 | Reply (Support) | 作者回复目标帖，立场为支持 |
| 实线 + 箭头，红色 | Reply (Oppose) | 回复，立场为反对 |
| 实线 + 箭头，橙色 | Reply (Modify) | 回复，立场为要求修改 |
| 实线 + 箭头，灰色 | Reply (Neutral) | 回复，立场中性 |
| 紫色虚线，无箭头 | Quote reference | 在正文中引用/摘录另一帖子内容，无直接回复关系 |
| 灰色虚线，无箭头 | PR co-participation | 两人都在同一 GitHub PR 下评论（ERC-8004）|
| 灰虚线→菱形 | PR edge | 评论者连接到所在的 PR supernode |

**箭头方向 / Arrow direction:** 箭头从**发言者**指向**被回复者**。箭头方向 = 论证流向。
*Arrow points from replier → to the author being replied to. Arrow direction = direction of argumentative engagement.*

### 如何交互 / How to Interact

- **拖拽节点**：手动调整布局，将感兴趣的节点移到中心。
  *Drag nodes to rearrange — pull key actors to center.*
- **滚轮缩放**：放大局部，查看密集区域的边细节。
  *Scroll to zoom in on dense clusters.*
- **悬停**：显示该节点的详细信息（机构、置信度、记录数、论证类型分布、立场分布）。
  *Hover for full profile: institution, confidence, record count, argument breakdown, stance breakdown.*
- **物理布局自动稳定**：页面加载后约 3–5 秒完成稳定，之后可自由拖拽。
  *Layout stabilizes in ~3–5 seconds after load, then drag freely.*

### 关键解读问题 / Key Interpretive Questions

**ERC-8004：**
- 图中是否存在明显的"中心节点"？还是分散式多中心结构？
  *Is there a dominant hub, or a polycentric, distributed structure?*
- MetaMask（橙）和 EF（蓝）之间的回复边是绿色（支持）还是红色/橙色（争议）？
  *Are reply edges between MetaMask and EF green (aligned) or red/orange (contested)?*
- 菱形 PR 节点的辐射结构显示哪几个 PR 吸引了最多参与者？
  *Which PR supernodes show the most spokes? These are the most contested PRs.*
- 紫色 quote 边是否形成独立的引用链？（说明有人跨多帖整合论点）
  *Do purple quote edges form chains? This signals cross-post argument synthesis.*

**A2A：**
- Google（蓝）节点是否形成密集的内部连接核心（clique）？
  *Do Google nodes form a tightly connected core clique?*
- Microsoft（浅蓝）和 Cisco（青）是否游离在外围，还是深度嵌入？
  *Are Microsoft and Cisco peripheral or embedded?*
- 有没有 Independent 节点深入核心，而非停留在边缘？
  *Any Independent contributors embedded in the core rather than peripheral?*

---

## Diagram 3 — 并排对比图 / Side-by-Side Comparison

**文件 / File:** `output/network_compare.html`

### 图表构成 / What You See

同一页面，**左侧 ERC-8004，右侧 Google A2A**。两张网络使用**完全相同的物理布局参数**（forceAtlas2Based，springLength=130），确保结构差异是真实的，而非参数差异导致的。

One page with **ERC-8004 left, Google A2A right**. Both networks use **identical physics parameters**, so structural differences are real, not parameter artifacts.

### 如何阅读 / How to Read

这张图的核心价值在于**视觉结构对比**，不需要精读每条边：

The core value is **visual structural contrast** — you don't need to read every edge:

1. **整体形状 / Overall shape**：ERC-8004 是否更"扁平分散"？A2A 是否更"中心聚集"？
   *Is ERC-8004 more diffuse? Is A2A more hub-and-spoke?*

2. **颜色分布 / Color distribution**：左图多少种颜色？右图呢？颜色分布是否均匀或集中？
   *How many distinct colors on each side? ERC-8004 should show far more color diversity (many institutions); A2A should show blue (Google) dominance.*

3. **节点大小差异 / Node size variance**：右图是否存在明显的"超级大节点"（holtskinner）？左图最大节点（MarcoMetaMask）相比之下多大？
   *Does A2A have a dominant super-node? How does ERC-8004's largest node compare in relative size?*

4. **边的密度 / Edge density**：哪侧看起来连接更密集？（A2A 的 217 条边 vs ERC-8004 的 65 条边，但 A2A 仅截取了 50 人）
   *Which side looks denser? A2A has 217 edges among 50 people; ERC-8004 has 65 edges among 74 people.*

### 核心论点支撑 / Core Argument Support

这张图直接支持论文核心论点：

| ERC-8004（左）| Google A2A（右）|
|---|---|
| 多中心、去中心结构 / Polycentric | 单中心或寡头核心 / Hub-and-spoke |
| 颜色多样（多机构）/ Diverse colors | Google 蓝色主导 / Google-dominated |
| 边颜色多样（多种立场）/ Varied edge colors | 以中性/支持为主 / Mostly neutral/supportive |
| 社区参与者（Independent）占多数 / Independent-heavy | 机构员工主导 / Institutional-heavy |

---

## Diagram 4 — 机构 × 论证类型二部图 / Institution × Argument Type Bipartite

**文件 / Files:** `output/bipartite_erc8004.html` 和 `output/bipartite_a2a.html`

### 图表构成 / What You See

| 元素 / Element | 含义 / Meaning |
|---|---|
| 左列节点 / Left column | 各机构（Institution）|
| 右列节点 / Right column | 论证类型（Argument Type）|
| 节点大小 / Node size | 该实体的总记录数 / Total record count |
| 连线宽度 / Edge width | log(该机构做出此类论证的记录数）|
| 连线颜色 / Edge color | 论证类型颜色（与右侧节点一致）|
| 悬停 / Hover | 显示具体计数和百分比 / Shows count and percentage |

#### 论证类型颜色 / Argument Type Colors

| 颜色 / Color | 类型 / Type | 含义 / Meaning |
|---|---|---|
| 蓝色 | Technical | 协议设计、技术规范讨论 |
| 琥珀色 | Economic | 经济激励、代币机制、成本 |
| 紫色 | Governance-Principle | 治理原则、权力结构、去中心化理念 |
| 绿色 | Process | 流程、时间表、EIP 生命周期 |
| 灰色 | Off-topic | 离题内容 |

### 如何阅读 / How to Read

1. **左→右追踪一条线**：从某机构出发，看它与哪些论证类型相连，最粗的线说明该机构最常做此类论证。
   *Trace from left node: the thickest edge from an institution reveals its dominant argumentative role.*

2. **悬停边**：显示"MetaMask → Technical: 12 records (71%)"这样的精确数字。
   *Hover an edge to see exact count and share — e.g., "MetaMask → Technical: 12 records (71%)".*

3. **比较左侧节点大小**：大节点 = 高贡献量机构，观察其连线是否多样化。
   *Compare left node sizes: large = high-volume institution. Are its connections diverse or concentrated?*

4. **比较两个案例（分别打开两个文件）**：
   *Open both files and compare:*
   - ERC-8004 的 Independent 贡献者做的是什么类型的论证？
     *What argument types do ERC-8004's Independent contributors make?*
   - A2A 的 Google 员工 vs Microsoft 员工在论证类型上有何差异？
     *Do Google contributors argue differently from Microsoft contributors in A2A?*

### 关键解读问题 / Key Interpretive Questions

- **ERC-8004**：MetaMask 是否以 Technical 论证为主？EF（Ethereum Foundation）是否更多 Governance-Principle？Independent 的分布是否更分散？
  *Is MetaMask predominantly Technical? Is EF more Governance-Principle-focused? Are Independents more diffuse?*

- **A2A**：Google 的论证类型分布是否与 Microsoft 不同？（Google = 技术规范主导，Microsoft = 互操作性/Process？）
  *Does Google's argument type profile differ from Microsoft's?*

- **跨案例**：两个案例的 Governance-Principle 论证由谁主导？这与机构类型（协议财团 vs 科技企业）是否一致？
  *Who makes Governance-Principle arguments in each case? Does this align with institutional type?*

---

## 通用交互说明 / General Interaction Notes

所有 vis.js 图（network\_\*.html, bipartite\_\*.html）支持：

All vis.js-based diagrams support:

| 操作 / Action | 效果 / Effect |
|---|---|
| 拖拽节点 / Drag node | 重定位该节点 |
| 滚轮 / Scroll | 缩放 |
| 悬停 / Hover | 工具提示（详细信息）|
| 单击节点 / Click node | 高亮直接邻居 |
| 双击空白 / Double-click canvas | 重置缩放 |

timeline_erc8004.html（D3.js）支持：

| 操作 / Action | 效果 / Effect |
|---|---|
| 悬停点 / Hover dot | 详细信息浮窗 |
| 纵向滚动 / Vertical scroll | 查看更多作者行 |

---

## 数据质量说明 / Data Quality Notes

所有图中节点均标注了数据置信度，以便读者判断哪些机构归属是可信的，哪些是推断的：

All network diagrams encode data confidence so readers can judge which attributions are solid:

- **粗边框节点**：机构已由 R07 人工核查（GitHub 公司字段、EIP 邮件、LinkedIn）
  *Thick-bordered nodes: institution verified by manual R07 investigation*
- **细边框节点**：机构由 LLM 推断，尚未人工核实
  *Thin-bordered nodes: institution LLM-inferred, not manually verified*
- **统计数字**：LLM 推断的 517 位作者中，经人工核查样本的准确率可在 `analysis/` 目录下的 kappa 计算结果中查阅
  *Accuracy of LLM inference can be verified against manual R07 sample via kappa scores in `analysis/`*
