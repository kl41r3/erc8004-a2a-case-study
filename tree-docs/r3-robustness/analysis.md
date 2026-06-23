# R3 Analysis Phase

## Status: ✅ Complete

### Data Collection
- 3 models: deepseek-v4-flash, glm-4-plus, deepseek-chat
- 3 rounds per model per case
- ERC: 1,664 records × 3 models × 3 rounds = 14,976 annotations
- A2A: 3,845 records × 3 models × 3 rounds = 34,605 annotations
- Total: ~49,500 annotations
- Coverage: 18/18 rounds at 100%

### Discontinued models (API issues)
- glm-5.1 / glm-5 / glm-5.2 / glm-5-turbo: all return empty response (len=0) from Zhipu API
- glm-4.7: rate limited (429 errors)
- kimi-k2.6: requires temperature=1, no system prompt, frequent empty responses

### Annotation Results
- 3 fields only: argument_type, stance, consensus_signal
- Per-model consensus: majority vote across 3 rounds

### Cross-Round ICR
- glm-4-plus: Fleiss κ 0.86-0.93 (Almost Perfect)
- deepseek-chat: Fleiss κ 0.69-0.92 (Substantial to Almost Perfect)
- deepseek-v4-flash: Fleiss κ 0.51-0.63 (Moderate to Substantial)

### Cross-Model Agreement
- 3/3 agreement: ~55-63% across all fields
- 2/3+ agreement: ~96-99%

### BERTopic
- 6 runs (3 models × 2 cases)
- Cross-model JSD: 0.000-0.014 (near-identical topic distributions)

### Key Finding
Model choice has minimal impact on BERTopic discourse composition (JSD < 0.02).
Annotator reliability varies by model: glm-4-plus and deepseek-chat are highly stable;
deepseek-v4-flash (reasoning model) has higher variance.
