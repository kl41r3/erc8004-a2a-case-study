# R2 标注模型最终清单 + 清理记录（2026-06-23）

本文件回答一个问题：**第二轮（R2）标注，我们最终到底用了哪些模型、哪些失败了**；并记录 2026-06-23 的一次清理。所有数字均可从源码与产出文件追溯（不依赖任何旧报告）。

---

## 1. 最终采用的模型（3 个）

R2 结构化标注（5 字段：`stakeholder_institution` / `argument_type` / `stance` / `consensus_signal` / `key_point`），两个案例各用同一组 3 个异构模型独立标注，再多数投票取共识：

| # | 模型 ID | 厂商 | 端点 | ERC 集群（唯一 1,664） | A2A（唯一 4,059） |
|---|---|---|---|---|---|
| 1 | `deepseek-v4-flash` | DeepSeek | api.deepseek.com | 1,661 ✅（3 条解析失败，0.2%） | 4,059 ✅（原缺 214 条，2026-06-23 补完） |
| 2 | `glm-4-plus` | 智谱 Zhipu | open.bigmodel.cn | 1,664 ✅（0 错误） | 4,059 ✅ |
| 3 | `moonshot-v1-auto` | 月之暗面 Kimi | api.moonshot.cn | 1,664 ✅（0 错误） | 4,059 ✅ |

- **共识规模**：ERC 1,664 条；A2A 4,058 条（多数投票 2-of-3，较原 3,844 增 214 条）。
- **ICR κ 计算样本**：三模型共有交集，ERC N=1,664、A2A N=4,045（原 3,831）。
- **证据来源**：
  - 代码：`scripts/process/annotate_r2.py`（ERC）、`scripts/process/annotate_a2a_r2.py`（A2A）的 `BACKENDS`。
  - 成功数：各 `data/annotated/r2/{model}/manifest.json`（ERC）；A2A 无 manifest，直接统计 `annotations.json`。
  - 共识：`data/annotated/r2/consensus/consensus_stats.json`（`models_used = [deepseek, glm, kimi]`）。

> Kimi 一栏注意：原计划用推理型 **Kimi-K2.6**，实测 ~60s/条、ETA 约 25h 不可行，改用同厂的 `moonshot-v1-auto`（见 `execution-log.md` §8a）。这是同厂商内的型号下调，非跨厂替换。

---

## 2. 失败 / 弃用的模型（不进入任何最终结果）

| 模型 | 计划用途 | 失败原因 | 证据 |
|---|---|---|---|
| **MiniMax-M3** | R2 第 4 个标注模型 | API Token Plan 额度耗尽，**每次调用均 429**，只跑了 3 条测试就放弃 | `data/annotated/r2/minimax_m3/manifest.json`（曾记 `successful: 0, errors: 3, error_rate: 100%`）—— 已删除 |
| Kimi-K2.6 | R2 标注（推理型） | 吞吐过慢（~60s/条），不切实际 | `execution-log.md` §8a |

**MiniMax-M3 与 MiniMax-M2.5 不是一回事**：M2.5 是 R1 的正式标注模型（paper-acm 正文用），成功且保留；只有 R2 的 M3 失败。清理只针对 M3。

---

## 3. 评分者间信度（权威值，2026-06-23 用 `validate_multimodel.py` 重算确认）

三模型联合 Fleiss' κ：

| 字段 | ERC（N=1,664） | A2A（N=4,045） |
|---|---|---|
| **argument_type** | **0.683** Substantial | **0.619** Substantial |
| stance | 0.368 Fair | 0.484 Moderate |
| consensus_signal | 0.299 Fair | 0.465 Moderate |
| stakeholder_institution | 0.161 Slight | 0.165 Slight |

最强 pairwise 配对均为 GLM↔Kimi：ERC argument_type κ=0.730、A2A κ=0.671。

- **权威来源**：`data/annotated/r2/validation/validation_report.json`（ERC）+ `data/annotated/r2/a2a/validation/validation_report.json`（A2A）。
- **重算命令**：`uv run python scripts/analyse/validate_multimodel.py --dataset {erc,a2a}`。
- **更新记录（2026-06-23 v2）**：DeepSeek A2A 缺失的 214 条已通过 `scripts/process/complete_a2a_deepseek.py` 补完（现 4,059/4,059），N 从 3,831 升至 4,045，argument_type κ 从 0.602 升至 0.619（越过 Substantial 阈值）。paper-acm 附录 Table `tab:icr-crossmodel` 已同步更新。
- **此前错误**：`final-report.md` 曾把 A2A 列误记为 argument_type 0.706 / stance 0.497 / consensus 0.531 / institution 0.241，已于 2026-06-23 v1 更正；v2 进一步更新为完整标注后的新值。

---

## 4. 2026-06-23 清理动作

| 类别 | 动作 | 对象 |
|---|---|---|
| 代码 | 移除 `minimax_m3` 后端 | `scripts/process/annotate_r2.py`（BACKENDS 现为 deepseek/kimi/glm）；docstring 留一行指向本失败记录 |
| 代码 | 清理过时 docstring 中的 MiniMax-M3 | `scripts/process/annotate_thematic.py` |
| 数据 | 删除失败结果目录 | `data/annotated/r2/minimax_m3/`（仅含 276B 失败 manifest） |
| 论文 | **删除整篇** | `paper-extended-2/`（24 文件 / 2.4M；用户不再需要）。内容已并入 `paper-acm` 附录；paper-acm 为唯一正式论文 |
| κ | 重算并更正 | `final-report.md`、`OVERVIEW.md` 与 paper-acm 三处现已一致 |
| 文档 | 同步 tree-docs | 本文件 + `OVERVIEW.md` / `execution-log.md` / `data-processing.md §1b` / `paper-comparison.md` |

**仍存在的轻微残留（未改，需用户决定）**：若干 R2 流水线脚本的 docstring / 输出路径仍写 `paper-extended-2`（如 `build_paper_figures_r2.py`、`fill_tbd_values.py`、`run_r2_pipeline.py` 等）。这些脚本产出的 R2 数据同时为 paper-acm 附录供数，代码本体仍有用，故未改其逻辑；如需一并清掉对已删论文的指向，请告知。
