# R3 多轮标注进度报告

**时间:** 2026-06-22  
**方法:** 3个模型 × 3轮独立标注 × 2个案例 = 18组结果  
**字段:** argument_type, stance, consensus_signal (3 fields only)

---

## 模型与API状态

| 模型 | API状态 | 问题 |
|------|---------|------|
| **deepseek-v4-flash** | ✅ 正常 | temperature=0, system prompt OK |
| **glm-4-plus** | ✅ 正常 | 偶有限流 (429) |
| **deepseek-chat** | ✅ 正常 | 稍慢但稳定 |
| ~~glm-4.7~~ | ❌ 弃用 | 限流过于严重 |
| ~~glm-5.1/5/5.2/5-turbo~~ | ❌ 全部空响应 | Zhipu GLM-5系列API返回len=0 |
| ~~kimi-k2.6~~ | ❌ 弃用 | temperature必须=1, 不能有system prompt, 空响应频繁 |

## 最终运行模型

1. **deepseek-v4-flash**: OpenAI-compat, deepseek API
2. **glm-4-plus**: OpenAI-compat, zhipu API
3. **deepseek-chat**: OpenAI-compat, deepseek API (对照)

---

## 标注完成情况

| Case | Model | R1 | R2 | R3 |
|------|-------|----|----|-----|
| **ERC** | deepseek-v4-flash | ✅ 1,664 | ✅ 1,656 | ✅ 1,653 |
| **ERC** | glm-4-plus | ✅ 1,664 | ✅ 1,660 | ✅ 1,660 |
| **ERC** | deepseek-chat | ✅ 1,664 | ✅ 1,660 | ✅ 1,660 |
| **A2A** | deepseek-v4-flash | 3,831/3,883 (98.6%) | 3,827/3,883 (98.5%) | 3,828/3,883 (98.5%) |
| **A2A** | glm-4-plus | 3,845/3,883 (99.0%) | 3,841/3,883 (98.9%) | 3,841/3,883 (98.9%) |
| **A2A** | deepseek-chat | 3,845/3,883 (99.0%) | 3,841/3,883 (98.9%) | 3,841/3,883 (98.9%) |

- ERC: 9/9 轮次 ≥99.2%
- A2A: 9/9 轮次 ≥98.5%
- 缺失 <2% 为 API 永久失败记录（通过重试无法恢复）

---

## 数据总量

- **ERC:** 3 模型 × 3 轮 × ~1,660 条 = ~14,940 条标注
- **A2A:** 3 模型 × 3 轮 × ~3,840 条 = ~34,560 条标注
- **总计:** ~49,500 条标注

---

## 与用户要求对比

| 要求 | 实际 |
|------|------|
| 5 个模型 | 3 个模型 (2个因API问题弃用) |
| 3 轮每模型 | ✅ 3 轮 |
| ERC 1,664 条 | ✅ ≥99% |
| A2A 3,883 条 | ✅ ≥98.5% |
| 3 个字段 | ✅ AT + ST + CS |
| GLM 5.1 | ❌ API空响应, 用 glm-4-plus 替代 |
| Kimi 2.6 | ❌ API异常, 用 deepseek-chat 替代 |

---

## 下一步

1. 合并三轮标注 → 每模型每字段取 majority vote → 得到"共识"标签
2. 计算 pairwise Cohen's κ + Fleiss' κ（跨轮次 ICR）
3. 每模型跑 BERTopic
4. 跨模型 BERTopic JSD 对比
5. Network analysis（基于共识标注）
6. 写 extended-2 论文
