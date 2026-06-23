# R2 Auto-Research Integration Plan

> Reference: Ji et al. (2026), *Leveraging LLM-based agents for social science research: insights from citation network simulations*, Humanities and Social Sciences Communications. DOI: 10.1057/s41599-025-06193-w

---

## Background

The R2 pipeline currently uses three LLMs as **static annotators** — they independently label records and the labels are merged via majority vote. This is a step beyond single-model annotation but still operates in "batch inference" mode.

Auto-research frameworks (Ji et al. 2026, Lu et al. 2026, auto-research by Karpathy) propose a more dynamic paradigm: LLM agents that **plan, execute, validate, and iterate** on research tasks, much like a human researcher would.

---

## Current R2 Pipeline vs. Auto-Research Pipeline

```
R2 (current)                     R2 + Auto-Research (proposed)
─────────────                    ──────────────────────────────
1. Annotate (3 LLMs, static)     1. Planning agent: design annotation schema
2. Validate (κ statistics)       2. Annotation agent: loop until κ ≥ threshold
3. Build consensus               3. Validation agent: adversarial review
4. Compute metrics               4. Consensus agent: negotiate disagreements
5. BERTopic                      5. Topic discovery agent: iterative refinement
6. Thematic-LM                   6. Network analysis agent: causal inference
7. Network analysis              7. Synthesis agent: write results section
8. Figure generation             8. Paper-writing agent: iterative draft
```

---

## Integration Plan (3 Phases)

### Phase A: Data Expansion (already in R2)
- ✅ ERC cluster: 1→34 ERCs, 142→1,664 records
- ✅ A2A: re-annotated with 3 models (in progress)
- ❓ **Auto-research addition**: Agent autonomously searches GitHub/Ethereum Magicians for additional agent ERCs → expands corpus → validates against current taxonomy

### Phase B: Iterative Annotation Validation
- ✅ Multi-model ICR (κ statistics, majority vote)
- ❓ **Auto-research addition**: Annotation quality loop — agent runs annotation → computes κ → if κ < threshold → identifies problematic records → refines prompt/definitions → re-annotates → loop until κ ≥ target

### Phase C: Automated Analysis & Reporting
- ❓ **Auto-research addition**: 
  - BERTopic: Agent searches for optimal n_topics and min_cluster_size 
  - Thematic-LM: Agent iterates codebook with reviewer feedback until saturation
  - Network analysis: Agent formulates and tests causal hypotheses about governance form
  - Paper writing: Agent drafts results section, fills tables, generates interpretation

---

## Recommended First Step: Phase B (Iterative Annotation Validation)

**Motivation**: This is the lowest-risk, highest-ROI integration. Our current static 3-model annotation still has:
- Stance κ = 0.369 (Fair) — borderline for DNA analysis
- Institution κ = 0.161 (Slight) — unreliable as stratifier

**Proposed workflow**:

```
Input: field with κ < 0.4 (e.g., stance)
Loop:
  1. Agent reviews 50 random records where 2/3 models disagree
  2. Agent hypothesizes why (ambiguous phrasing, missing context)
  3. Agent proposes prompt refinement or definition clarification
  4. All 3 models re-annotate those 50 records
  5. Compute new κ for the sample
  6. If κ improved → apply to full dataset
  7. Stop when κ ≥ 0.4 or no improvement in 2 consecutive rounds
```

**Required**: Sufficient LLM API budget for iterative re-annotation.

---

## Decision Points (for user review)

1. **Scope**: Phase B only (annotation improvement) or Phase A+B+C (full auto-research pipeline)?
2. **Budget**: Willingness to invest additional API credits for iterative loops?
3. **Timeline**: Auto-research integration would add ~1-2 weeks to the project, potentially delaying paper submission.
4. **Paper positioning**: If Phase C is completed, the paper can claim "LLM agent-driven research pipeline" rather than "LLM-assisted annotation pipeline" — a significantly stronger methodological contribution.

---

## Current Status

- [x] Multi-model static annotation (3 LLMs, majority vote)
- [x] ICR validation framework
- [ ] Phase B: Iterative annotation validation (plan reviewed, pending implementation)
- [ ] Phase A extension: Auto corpus expansion
- [ ] Phase C: Auto analysis & reporting
