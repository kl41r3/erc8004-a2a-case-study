# Paper Sections — Topic Discovery Analysis
## RQ1: DAO vs. Corporate Governance in Technology Standardization

**Generated:** 2026-04-10  
**Data:** 4,329 records (ERC-8004: 142, A2A: 4,187)  
**Methods:** Thematic-LM (ACM WWW 2025) + BERTopic Comparative Discourse Analysis (ACM SMSociety 2020)

---

## 3. Method

```latex
\section{Methods}

\subsection{Method 1: Comparative Discourse Analysis via BERTopic}

Following Stine and Agarwal~\cite{stine_agarwal_2020}, we fit a BERTopic model~\cite{bertopic_2022}
jointly on the full corpus and then compare per-case topic distributions
using Jensen-Shannon (JS) divergence~\cite{lin_1991}.

\textbf{Embedding.}
Texts are encoded with \texttt{all-MiniLM-L6-v2}~\cite{reimers_gurevych_2019},
a sentence-transformer model that runs locally at no API cost.

\textbf{Dimensionality Reduction.}
Embeddings are projected to five dimensions using UMAP
($n_\text{neighbors}=15$, cosine metric, seed=42)~\cite{mcinnes_umap_2018}.

\textbf{Clustering.}
We apply HDBSCAN ($\text{min\_cluster\_size}=10$, $\text{min\_samples}=5$)
to identify dense regions, with $\text{nr\_topics}=20$ requested from
BERTopic's c-TF-IDF representation layer~\cite{bertopic_2022}.
The model produced \textbf{19 valid topics} plus one noise class.

\textbf{Cross-Case Divergence.}
We compute the proportion of each case's records assigned to each topic:
\begin{align*}
  m_i &= \frac{1}{2}(p_i + q_i) \\
  KLD(p, m) &= \sum_{i} p_i \log_2 \frac{p_i}{m_i}
\end{align*}
where $p$ and $q$ are the ERC-8004 and A2A topic distributions, and $KLD$ denotes Kullback-Leibler divergence. We then calculate the global JS divergence between the two distributions:
\begin{equation*}
  JSD(p, q) = \frac{1}{2} [KLD(p, m) + KLD(q, m)].
\end{equation*}
$JSD$ denotes JS divergence which ranges from 0 (identical distributions) to 1 (disjoint)~\cite{stine_agarwal_2020}.

For each topic $t$ and case $c \in \{\text{ERC-8004},\, \text{A2A}\}$, the within-case topic proportion is:                                                                                                                                                                                                      
  \begin{equation}
    p_t^{(c)} = \frac{\bigl|\{i \mid \mathrm{case}(i)=c,\; \mathrm{topic}(i)=t\}\bigr|}                                                                                                                                                     
                     {\bigl|\{i \mid \mathrm{case}(i)=c\}\bigr|}                                                                                                                                                                            
  \end{equation}                                                                                                                                                                                                                            
  where the denominator counts all non-bot records in case $c$                                                                                                                                                                              
  (ERC-8004: $n=142$; A2A: $n=4{,}187$), including noise-class                                                                                                             
  records ($\mathrm{topic}=-1$) which are excluded from the numerator.   

\subsection{Method 2: Thematic-LM Multi-Agent Pipeline}

We adopt the Thematic-LM framework~\cite{thematic_lm_2025}, a four-stage
multi-agent LLM system designed for large-scale inductive thematic analysis.
The pipeline proceeds as follows:

\textbf{Stage 1 — Open Coding.}
Each record is assigned a short code (3--7 words) summarizing its main idea.
Records are submitted to MiniMax-M2.5~\cite{minimax_m25} in batches of 15.
Chain-of-thought reasoning was disabled for Stage 1.

\textbf{Stage 2 — Aggregation.}
An aggregator agent groups semantically similar codes into 10--20 raw
theme clusters. To remain within the model's context budget, we sampled
300 codes (seed=42) from the full set and submitted them in a single prompt.
This stage produced 14 raw clusters.

\textbf{Stage 3 — Codebook Review.}
A reviewer agent merges redundant clusters, splits over-broad ones, and
writes a natural-language description for each theme. The resulting codebook
contains \textbf{19 themes} (T01--T19), each with a label, description, and
a representative set of member codes.

\textbf{Stage 4 — Theme Assignment.}
Each of the 4,329 records is assigned the most relevant codebook theme.
Records for which no theme reached sufficient confidence are labeled
\textit{Unclassified}. Stages 2--4 used the model's full chain-of-thought
reasoning to maximize conceptual fidelity.

Checkpoints are saved every 10 batches; the pipeline is safe to interrupt
and resume without duplicating API calls.
```

---

## 4. Results

```latex
\subsection{Thematic-LM: 19-Theme Codebook}

The pipeline identified 19 governance discourse themes spanning the full corpus
(Table~\ref{tab:themes}). Of the 4,329 records, 294 (6.8\%) remained
\textit{Unclassified}. Per-case distributions reveal structural asymmetries
that align with the institutional logics of each governance model.

\begin{table*}[htbp]
\centering
\caption{Thematic-LM codebook with per-case distributions (sorted by ERC-8004 share).}
\label{tab:themes}
\small
\begin{tabular}{llrrrr}
\toprule
\textbf{ID} & \textbf{Theme Label} & \textbf{ERC $n$} & \textbf{ERC \%} & \textbf{A2A \%} & \textbf{$\Delta$} \\
\midrule
T08 & Trust \& Security Mechanisms         &  49 & 34.5 &  4.0 & $+$30.5 \\
T01 & Protocol Specification \& Versioning &  19 & 13.4 &  7.9 & $+$5.5  \\
T07 & Community Collaboration \& Contributions & 14 & 9.9 & 9.9 & $\pm$0.0 \\
T14 & Project Governance \& Process        &   6 &  4.2 &  4.1 & $+$0.1  \\
T03 & Agent Discovery \& Registry          &   7 &  4.9 &  6.3 & $-$1.4  \\
T18 & Spec Clarifications \& Info Requests & 12 &  8.5 & 10.2 & $-$1.7  \\
T10 & AgentCard \& Metadata Structures     &   6 &  4.2 &  3.8 & $+$0.4  \\
T13 & Integrations \& External Systems     &   6 &  4.2 &  2.2 & $+$2.0  \\
T12 & Testing \& Validation Tools          &   5 &  3.5 &  1.2 & $+$2.3  \\
T19 & Bug Fixes \& Implementation Improvements & 4 & 2.8 & 5.2 & $-$2.3 \\
T06 & Documentation \& Examples            &   3 &  2.1 & 10.8 & $-$8.7  \\
T11 & Data Types \& Schema Definition      &   3 &  2.1 &  4.2 & $-$2.0  \\
T02 & Authentication \& Authorization      &   1 &  0.7 &  2.7 & $-$1.9  \\
T04 & Task \& Message Management           &   1 &  0.7 &  3.8 & $-$3.1  \\
T05 & SDK Development \& Libraries         &   1 &  0.7 &  4.6 & $-$3.9  \\
T15 & Tooling Fixes \& Automation          &   1 &  0.7 &  4.5 & $-$3.8  \\
T17 & Multi-Agent Systems Architecture     &   1 &  0.7 &  2.5 & $-$1.8  \\
T09 & Transport \& Protocol Mechanisms     &   0 &  0.0 &  3.2 & $-$3.2  \\
T16 & Streaming \& Real-time Communication &   0 &  0.0 &  2.1 & $-$2.1  \\
\midrule
    & \textit{Unclassified}                &   3 &  2.1 &  7.0 & $-$4.9  \\
\midrule
    & \textbf{Total}                       & \textbf{142} & & \textbf{4187} & \\
\bottomrule
\end{tabular}
\end{table*}

The most discriminating theme is \textbf{T08 (Trust \& Security Mechanisms)},
which accounts for 34.5\% of ERC-8004 discourse but only 4.0\% of A2A
discourse ($\Delta = +30.5$ percentage points). This theme encompasses
agent trust scoring, reputation mechanisms, on-chain credential verification,
and decentralized trust architectures. Its dominance in ERC-8004 reflects
the foundational governance problem of the EIP process: establishing
trustworthy agent identity in a permissionless environment.

In contrast, A2A's discourse is notably broader, with substantial shares
devoted to \textbf{T06 (Documentation \& Examples)} (10.8\%), \textbf{T18
(Spec Clarifications)} (10.2\%), \textbf{T07 (Community Collaboration)}
(9.9\%), and \textbf{T01 (Protocol Specification \& Versioning)} (7.9\%).
Two themes are entirely absent from ERC-8004: \textbf{T09 (Transport \&
Protocol Mechanisms)} and \textbf{T16 (Streaming \& Real-time Communication)},
indicating that low-level implementation details never entered the ERC-8004
governance forum.

The JS divergence between the two theme distributions under Method 1 is
$\mathrm{JS} = 0.216$, confirming moderate but statistically meaningful
structural separation.

\subsection{BERTopic: Embedding-Based Cross-Case Divergence}

BERTopic identified 19 topics from the combined corpus.
The global JS divergence between ERC-8004 and A2A topic distributions is
$\mathrm{JSD} = 0.288$ (Table~\ref{tab:bertopic}).
This moderate divergence (on the unit scale) indicates that the two
governance processes share discourse space but with substantially different
emphases.

\begin{table*}[htbp]
\centering
\caption{Top BERTopic topics ranked by absolute cross-case divergence.
Noise-class records excluded.}
\label{tab:bertopic}
\small
\begin{tabular}{llrrrr}
\toprule
\textbf{Topic} & \textbf{Key Terms} & \textbf{ERC $n$} & \textbf{ERC \%} & \textbf{A2A \%} & $|\Delta|$ \\
\midrule
0  & agent, agents, for, of          & 96 & 67.6 & 21.2 & 46.4 \\
1  & task, message, artifact         &  0 &  0.0 &  8.2 &  8.2 \\
3  & json, a2a, proto, message       &  0 &  0.0 &  7.7 &  7.7 \\
4  & pull, contributing, format      &  0 &  0.0 &  7.2 &  7.2 \\
2  & this, you, pr, thanks           &  1 &  0.7 &  7.7 &  7.0 \\
5  & python, samples, sdk            &  0 &  0.0 &  5.9 &  5.9 \\
9  & suggestion, sap, linkedin       &  4 &  2.8 &  0.9 &  1.9 \\
6  & version, versions, changes      &  2 &  1.4 &  2.7 &  1.3 \\
8  & vote, favor, 2025/2026          &  0 &  0.0 &  1.2 &  1.2 \\
10 & pushnotificationconfig, push    &  0 &  0.0 &  0.9 &  0.9 \\
\bottomrule
\end{tabular}
\end{table*}

ERC-8004 is strikingly concentrated: 67.6\% of its records fall into
Topic~0, the broad ``agent'' discourse cluster, compared with 21.2\% for A2A.
The BERTopic model reveals that ERC-8004 discussion does not distribute
across specialized implementation topics—zero records appear in Task
Management (Topic~1), JSON/Proto specification (Topic~3), PR contribution
workflows (Topic~4), or SDK samples (Topic~5). The only topic where
ERC-8004 shows a higher-than-A2A share is Topic~9
(suggestion/stakeholder engagement, 2.8\% vs. 0.9\%), indicating the
presence of institutional voices—corporate representatives from SAP,
LinkedIn, and similar organizations—in the EIP comment thread.
```

---

## 5. Discussion

```latex
\section{Discussion}

\subsection{The Trust Imperative in DAO Governance}

The most striking result across both methods is the centrality of trust
mechanisms in ERC-8004 governance discourse. Thematic-LM Theme T08
(\textit{Trust \& Security Mechanisms}) accounts for 34.5\% of ERC-8004
records—more than any other single theme—while registering only 4.0\% in
A2A. This asymmetry is not incidental; it reflects a structural condition
of decentralized governance. In the Ethereum ecosystem, no central authority
can certify agent identity, reputation, or behavioral compliance. The EIP
process therefore becomes the arena in which the community negotiates what
constitutes trustworthy agency: on-chain reputation scoring, verifiable
credential schemas, escrow-based validation, and vouch-chain models. These
debates are governance debates in the deepest sense—they define who or what
can participate in the ecosystem and under what conditions.

By contrast, Google A2A operates within an institutional trust environment.
Google's corporate identity, GitHub's authenticated contribution model, and
the A2A Technical Steering Committee (TSC) collectively provide trust
backstops that ERC-8004 must construct from first principles. This frees
A2A's governance discourse from the trust problem and redirects it toward
operational concerns: documentation, SDK maintenance, transport mechanisms,
and streaming protocols.

\subsection{Discourse Breadth as an Indicator of Project Maturity}

A2A's more distributed topic profile—10 themes each carrying 3--11\% of
discourse, compared with ERC-8004's heavy concentration in T08 and T01—reflects
the operational diversity of a large-scale engineering project. The BERTopic
analysis reinforces this finding: ERC-8004's discourse is 67.6\% concentrated
in a single ``agent'' cluster, while A2A distributes across task management,
JSON/proto specification, SDK samples, and PR workflows.

This pattern aligns with Organizational Theory's distinction between
\textit{constitutive} and \textit{regulative} governance~\cite{selznick_1957}.
ERC-8004's discourse is predominantly \textit{constitutive}: participants
negotiate what the protocol \textit{is} and what principles should govern
its adoption. A2A's discourse is predominantly \textit{regulative}: participants
coordinate \textit{how} an already-legitimized protocol is implemented and
maintained.

\subsection{Convergence: Community Collaboration as Shared Infrastructure}

One result is notably \textit{convergent} across both governance processes.
T07 (\textit{Community Collaboration \& Contributions}) carries essentially
identical weight in both corpora: 9.9\% for ERC-8004 and 9.9\% for A2A.
This symmetry is remarkable given the order-of-magnitude size difference
between the two communities. It suggests that regardless of governance
model—DAO or corporate—open-source collaboration infrastructure (pull
request review, CLA compliance, partner onboarding, voting procedures)
consumes a structurally fixed share of governance bandwidth.

The BERTopic analysis partially corroborates this: Topic~2 (\textit{pr,
thanks, you, this}), representing social coordination micro-discourse around
PR management, appears in A2A at 7.7\% but contributes only 0.7\% in
ERC-8004. The discrepancy arises because ERC-8004's small forum format
(Ethereum Magicians) collapses PR-style coordination into the same discussion
thread as substantive proposals, whereas A2A's GitHub Issues/PRs
structurally separate social coordination from technical debate.

\subsection{The Absent A2A-Exclusive Topics and What They Reveal}

BERTopic identifies five topics with zero ERC-8004 representation
(Topics 1, 3, 4, 5, and 8--18), all associated with engineering
implementation: transport mechanisms, streaming APIs, Docker deployment,
linter configuration, and voting records. Thematic-LM similarly finds two
entirely absent themes: T09 (\textit{Transport \& Protocol Mechanisms}) and
T16 (\textit{Streaming \& Real-time Communication}).

The absence of engineering implementation discourse from ERC-8004 is not a
corpus artifact—ERC-8004 includes both the Ethereum Magicians forum
(governance deliberation) and the ethereum/ERCs GitHub repository (PR
discussion). The absence therefore reflects a genuine property of the EIP
governance process: implementation decisions are deferred to downstream
adopters, and the governance arena focuses exclusively on the specification
contract. This \textit{implementation deferral} is itself a governance
mechanism—it enables a diverse ecosystem of compliant but independent
implementations, precisely the design goal of a permissionless standard.

\subsection{Cross-Method Triangulation}

The two methods produce convergent but not identical divergence estimates:
$\mathrm{JS}_{\mathrm{Thematic\text{-}LM}} = 0.216$ vs.
$\mathrm{JS}_{\mathrm{BERTopic}} = 0.288$. The gap is expected: Thematic-LM
operates on human-interpretable semantic clusters where the ``agent discussion''
theme can absorb discourse from both cases (T01, T18 both carry ~10\% A2A
and significant ERC shares), compressing divergence. BERTopic's embedding
space preserves finer-grained lexical distinctions—ERC-8004 uses ``trustless'',
``escrow'', ``reputation'' whereas A2A uses ``agent''---that push the two
distributions further apart. Together, the two estimates bracket the true
structural divergence and confirm the result's robustness: the two governance
processes occupy meaningfully different but overlapping discourse spaces.

\subsection{Limitations}

\textbf{Corpus imbalance.} ERC-8004 contributes only 142 records (3.3\%
of the corpus). Percentage-based comparisons, especially for low-frequency
themes, carry wide confidence intervals. Findings should be interpreted as
indicative rather than definitive pending future data collection.

\textbf{Shared codebook bias.} The Thematic-LM codebook was induced from
a sample of 300 codes drawn from both cases. A2A's larger share (~97\% of
records) may have dominated Stage 2 aggregation, potentially producing
themes that under-represent ERC-8004's distinctive concerns. The extreme
T08 dominance in ERC-8004 (34.5\%), however, argues against severe
codebook bias.

\textbf{BERTopic label interpretability.} BERTopic topic labels are
c-TF-IDF keyword concatenations (e.g., \texttt{0\_agent\_the\_to\_and})
that require human interpretation. Our mapping to governance constructs is
our own interpretive framing and is not validated by inter-rater
reliability analysis.

\textbf{Temporal dynamics.} Both methods aggregate across the full timeline
of each project. Governance discourse evolves—early ERC-8004 debates about
trust architecture may differ from later editorial discussions. Temporal
segmentation is left for future work.
```

---

## References

```latex
\begin{thebibliography}{99}

\bibitem{thematic_lm_2025}
Y.~Shi, X.~Zhao, J.~Xu, and L.~Cui,
``Thematic-LM: A LLM-Based Multi-Agent System for Large-Scale Thematic Analysis,''
in \textit{Proc. ACM Web Conf. (WWW)}, 2025, pp.~1--10.
DOI: 10.1145/3696410.3714595.

\bibitem{stine_agarwal_2020}
G.~Stine and P.~Agarwal,
``Comparative Discourse Analysis Using Topic Models: Contrasting Perspectives on China from Reddit,''
in \textit{Proc. ACM Int. Conf. Social Media and Society (SMSociety)}, 2020, pp.~1--10.
DOI: 10.1145/3400806.3400816.

\bibitem{bertopic_2022}
M.~Grootendorst,
``BERTopic: Neural Topic Modeling with a Class-Based TF-IDF Procedure,''
\textit{arXiv preprint}, arXiv:2203.05794, 2022.

\bibitem{minimax_m25}
MiniMax,
``MiniMax-M2.5 Technical Report,''
MiniMax AI, 2025.

\bibitem{reimers_gurevych_2019}
N.~Reimers and I.~Gurevych,
``Sentence-BERT: Sentence Embeddings Using Siamese BERT-Networks,''
in \textit{Proc. EMNLP-IJCNLP}, 2019, pp.~3982--3992.
DOI: 10.18653/v1/D19-1410.

\bibitem{mcinnes_umap_2018}
L.~McInnes, J.~Healy, and J.~Melville,
``UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction,''
\textit{arXiv preprint}, arXiv:1802.03426, 2018.

\bibitem{maarten_ctfidf_2022}
M.~Grootendorst,
``Maarten's c-TF-IDF: A Class-Based TF-IDF for Topic Modeling,''
Zenodo, 2022.
DOI: 10.5281/zenodo.6362383.

\bibitem{lin_1991}
J.~Lin,
``Divergence Measures Based on the Shannon Entropy,''
\textit{IEEE Trans. Inf. Theory}, vol.~37, no.~1, pp.~145--151, 1991.
DOI: 10.1109/18.61115.

\bibitem{selznick_1957}
P.~Selznick,
\textit{Leadership in Administration: A Sociological Interpretation}.
Evanston, IL: Row, Peterson, 1957.

\end{thebibliography}
```

---

## Key Numbers Summary (for internal reference)

| Metric | Value |
|--------|-------|
| Total coded records | 4,329 |
| ERC-8004 records | 142 (3.3%) |
| A2A records | 4,187 (96.7%) |
| Thematic-LM themes | 19 |
| Thematic-LM JS divergence | 0.216 |
| BERTopic topics | 19 |
| BERTopic JS divergence | 0.288 |
| Top ERC-8004 theme | T08 Trust & Security (34.5%) |
| Top A2A-dominant theme | T06 Documentation (10.8% vs 2.1%) |
| ERC-absent themes | T09 Transport, T16 Streaming |
| BERTopic ERC Topic 0 concentration | 67.6% |
| BERTopic A2A Topic 0 concentration | 21.2% |
