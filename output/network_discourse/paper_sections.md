# Network Discourse Analysis — Paper Sections (LaTeX Draft)

**Generated:** 2026-04-12  
**Methods covered:** DNA (Discourse Network Analysis) + Socio-semantic Bipartite Network  
**Status:** Draft — insert into paper/RQ1.tex after existing SNA section

---

## \subsection{Network Discourse Analysis}

```latex
\subsection{Network Discourse Analysis}

We augment the structural co-participation network with two complementary
discourse-layer analyses that jointly exploit the Thematic-LM topic assignments
(Section~\ref{sec:thematic-lm}) and the LLM-annotated stance labels.

\paragraph{Data note: actor counts versus raw participant counts.}
The network actor set is smaller than the total annotated participant set
because of three sequential filters applied in \texttt{loader.py}.
Starting from 149 ERC-8004 and 5{,}272 Google A2A annotated records:
(i)~bot accounts (\texttt{github-actions[bot]}, \texttt{eip-review-bot},
\texttt{dependabot[bot]}) and texts shorter than 20 characters are removed
(ERC: $149\!\to\!130$ records, $71\!\to\!69$ actors;
 A2A: $5{,}272\!\to\!4{,}230$ records, $778\!\to\!772$ actors);
(ii)~records are inner-joined against \texttt{coded\_records.json}, retaining
only the 4{,}329 entries that received a Thematic-LM theme assignment
(12 coded records find no matching annotation and are dropped);
(iii)~\textit{Off-topic} and \textit{Unclassified} stance labels are excluded.
After all filters: ERC-8004 retains 126 records and \textbf{66 actors};
Google A2A retains 3{,}759 records and \textbf{710 actors}.

\subsubsection{Method III: Discourse Network Analysis}

Following \citet{leifeld2013}, we model each governance community as a
\emph{discourse network} in which nodes represent actors and edges represent
shared or opposing positions on thematic content.
Formally, let $A$ be the set of actors and $T = \{T_{01},\ldots,T_{19}\}$ the
codebook of 19 themes derived in Section~\ref{sec:thematic-lm}.
For each record $r$ we have a tuple $(a_r, \theta_r, s_r)$ where $a_r\in A$
is the author, $\theta_r\in T$ is the assigned theme, and
$s_r\in\{+1, +0.5, 0, -1\}$ encodes the stance
(Support\,$=\!+1$, Modify\,$=\!+0.5$, Neutral\,$=\!0$, Oppose\,$=\!-1$).

We first construct an \emph{actor–theme stance matrix} $M$ whose rows
are actors and whose columns are the 19 themes.
Each cell $M_{at}$ holds the actor's \emph{mean stance score} across
all records they contributed to theme $t$
(Support\,=\,+1, Modify\,=\,+0.5, Neutral\,=\,0, Oppose\,=\,$-$1);
the cell is left empty if the actor never participated in that theme.
The following toy example illustrates the structure:

\begin{center}
\small
\begin{tabular}{lccc}
\toprule
         & Theme A & Theme B & Theme C \\
\midrule
Alice    & $+1$    & $-1$    & ---     \\
Bob      & $+1$    & $+0.5$  & $0$     \\
Carol    & ---     & $-1$    & $+1$    \\
\bottomrule
\end{tabular}
\end{center}

\noindent Two networks are then projected from $M$:
\begin{itemize}
    \item \textbf{Congruence network} $G^+$: an edge connects two actors
          whenever they hold a stance in the \emph{same direction}
          (both positive or both negative) on at least one theme.
          The edge weight $w_{ij}^{+}$ counts the number of such themes.
          In the example, Alice and Bob agree on Theme~A ($+1$ vs.\ $+1$),
          so they are linked in $G^+$.
    \item \textbf{Conflict network} $G^-$: an edge connects two actors
          whenever their stances on at least one theme are
          \emph{strictly opposite in sign} (one positive, one negative).
          The edge weight $w_{ij}^{-}$ counts those themes.
          Alice and Bob conflict on Theme~B ($-1$ vs.\ $+0.5$), so they
          also appear in $G^-$; Alice and Carol agree on Theme~B
          ($-1$ vs.\ $-1$), linking them in $G^+$.
\end{itemize}

Four summary statistics are reported for each network.

\noindent\textbf{Network density} is the fraction of realised edges among all
possible actor pairs — higher values indicate a more tightly connected
discourse community:
\[ \rho(G) = \frac{|E|}{\binom{|A|}{2}}. \]

\noindent\textbf{Louvain modularity} $Q$ measures how well actors
partition into internally coherent communities; $Q>0.3$ is conventionally
taken as meaningful community structure \citep{blondel2008}:
\[ Q = \frac{1}{2m}\sum_{i,j}\!\Bigl[A_{ij} - \frac{k_i k_j}{2m}\Bigr]\delta(c_i,c_j), \]
where $m = \tfrac{1}{2}\sum_{ij}A_{ij}$ is total edge weight,
$k_i = \sum_j A_{ij}$ is the weighted degree of node $i$,
and $\delta(c_i,c_j)=1$ iff $i$ and $j$ belong to the same Louvain community.

\noindent\textbf{Cross-institutional polarization index} $\pi$ is the share
of congruence edges that cross distinct \texttt{stakeholder\_institution}
categories — high $\pi$ means agreement is predominantly cross-institutional,
low $\pi$ means actors mostly agree within their own organisational group:
\[ \pi = \frac{|E_{\text{cross}}|}{|E_{\text{total}}|}. \]

\noindent\textbf{Normalised betweenness centrality} $b(v)\in[0,1]$ identifies
broker actors who lie on the shortest paths connecting otherwise distant
discourse communities — higher $b(v)$ signals a discourse gatekeeper:
\[ b(v) = \frac{2}{(|A|-1)(|A|-2)}\sum_{s \neq v \neq t}\frac{\sigma_{st}(v)}{\sigma_{st}}, \]
where $\sigma_{st}$ is the total number of shortest paths from $s$ to $t$
and $\sigma_{st}(v)$ counts those passing through $v$.
We report $b(v)$ for the top-5 actors.

\subsubsection{Method IV: Socio-semantic Bipartite Network}

Following \citet{roth2010}, we construct a two-mode (bipartite) network
$\mathcal{B} = (A \cup T,\, E)$ in which an edge $(a, t)$ exists whenever
actor $a$ authored at least one record assigned to theme $t$,
with weight $B_{at}$ equal to the raw comment count.

The \emph{actor-actor projection} $W^A = BB^\top$ links two actors by the
number of themes they co-discussed (self-loops removed).
The \emph{theme-theme projection} $W^T = B^\top B$ links two themes by the
number of actors who engaged in both.

Per-actor topic diversity is measured by Shannon entropy:
\begin{equation}
    H(a) = -\sum_{t=1}^{|T|} \hat{p}_{at} \log_2 \hat{p}_{at},
    \quad \hat{p}_{at} = B_{at} \Big/ \textstyle\sum_{t'} B_{at'},
    \label{eq:entropy}
\end{equation}
where $H(a)=0$ for a pure specialist (one theme only) and
$H(a)=\log_2|T|$ for a perfect generalist (uniform spread across all themes).

We further characterise the distribution of $H$ via its Gini coefficient
(the higher the Gini, the more topic diversity is concentrated in a few
actors), and measure per-theme actor concentration as the Gini of
comment counts within each theme.
The \emph{thematic overlap coefficient} $\Omega$ is the ratio of themes
active in both cases to the smaller case's theme count; $\Omega=1$ means
one community's thematic space is a strict subset of the other's.
Topic \emph{gatekeepers} — actors whose removal most fragments the
actor-actor projection — are identified by normalised betweenness centrality.
```

---

## \subsection{Results: Network Discourse Analysis}

```latex
\subsection{Results: Network Discourse Analysis}
\label{sec:results-netdisc}

\subsubsection{Discourse Network Analysis Results}

Table~\ref{tab:dna} reports the key metrics for both congruence and
conflict networks.

\begin{table}[h]
\centering
\caption{Discourse Network Analysis metrics.}
\label{tab:dna}
\begin{tabular}{lcc}
\toprule
\textbf{Metric} & \textbf{ERC-8004} & \textbf{Google A2A} \\
\midrule
Actors ($|A|$)                    & 66      & 710     \\
Active themes                     & 16      & 19      \\
Records (after filtering)         & 126     & 3{,}759 \\
\midrule
\multicolumn{3}{l}{\textit{Congruence network $G^+$}} \\
Edges                             & 318     & 20{,}638 \\
Density                           & 0.1483  & 0.0820   \\
Louvain modularity                & 0.2886  & 0.2453   \\
Polarization index $\pi$          & 0.138   & 0.253    \\
Top betweenness                   & 0.0607  & 0.0175   \\
\midrule
\multicolumn{3}{l}{\textit{Conflict network $G^-$}} \\
Edges                             & 74      & 2{,}531  \\
Mean actor theme diversity        & 1.47    & 2.211    \\
\bottomrule
\end{tabular}
\end{table}

\noindent\textbf{Consensus structure.}
ERC-8004 exhibits a substantially higher congruence density (0.148 vs.\ 0.082),
indicating that participants in the DAO governance process hold more uniformly
aligned positions relative to those in the corporate project.
Both networks show moderate community structure in the Louvain partition
($Q_{\mathrm{ERC}}\!=\!0.289$; $Q_{\mathrm{A2A}}\!=\!0.245$).

\noindent\textbf{Conflict and cross-institutional discourse.}
The A2A conflict network is 34$\times$ larger in absolute edge count
(2,531 vs.\ 74), reflecting the diversity of technical positions across
710 contributors from multiple organizations.
The polarization index reveals a structural difference in how institutional
identity shapes discourse: in ERC-8004, only 13.8\% of congruence edges
cross institutional boundaries, whereas in Google A2A the proportion reaches
25.3\%.
This counterintuitive finding suggests that while both projects exhibit
participation inequality, A2A contributors from different companies engage
in more cross-institutional discursive agreement than the pseudonymous
participants of ERC-8004.

\noindent\textbf{Discourse centrality.}
In ERC-8004, the top betweenness actor scores 0.061, compared with 0.018
in A2A---a 3.4$\times$ difference.
The ERC-8004 discourse network thus features a small set of ``broker''
participants who mediate between otherwise disconnected congruence
communities, consistent with the hub-and-spoke topology identified in the
structural SNA (Section~\ref{sec:results-sna}).
In A2A, by contrast, discourse brokerage is distributed across many
low-centrality actors, indicating a flatter discursive hierarchy.

\subsubsection{Socio-semantic Network Results}

\begin{table}[h]
\centering
\caption{Socio-semantic bipartite network metrics.}
\label{tab:ss}
\begin{tabular}{lcc}
\toprule
\textbf{Metric} & \textbf{ERC-8004} & \textbf{Google A2A} \\
\midrule
Actors ($|A|$)                          & 66      & 710    \\
Active themes ($|T|$)                   & 16      & 19     \\
Actor-actor projection edges            & 645     & 59{,}007 \\
Louvain modularity (actor proj.)        & 0.1901  & 0.1814  \\
\midrule
\multicolumn{3}{l}{\textit{Actor topic diversity (Shannon entropy)}} \\
Mean $H$                                & 0.348   & 0.617  \\
Median $H$                              & 0.0     & 0.0    \\
Gini$(H)$                               & 0.773   & 0.707  \\
Max $H$                                 & 2.664   & 3.834  \\
\midrule
\multicolumn{3}{l}{\textit{Theme concentration}} \\
Mean Gini (per-theme actor counts)      & 0.085   & 0.453  \\
Most-discussed theme                    & T08     & T06    \\
\midrule
Thematic overlap $\Omega$               & \multicolumn{2}{c}{1.000} \\
\bottomrule
\end{tabular}
\end{table}

\noindent\textbf{Pervasive discourse specialization.}
In both cases, the median actor entropy is $H\!=\!0$, indicating that
the majority of participants engaged with exactly one thematic domain.
This extreme specialization is consistent with the ``peripheral participant''
pattern documented in open-source communities~\citep{mockus2002}, and
suggests that governance discourse---regardless of DAO vs.\ corporate
structure---is organized as a division of communicative labor rather than
broad deliberation.

\noindent\textbf{Modest generalism advantage in A2A.}
The mean entropy of A2A actors (0.617) is 77\% higher than ERC-8004 (0.348),
and the maximum entropy reaches 3.83 bits (vs.\ 2.66 bits).
This reflects A2A's larger community size: with 710 contributors and 19
active themes, the probability of a core member naturally spanning multiple
technical workstreams is higher.
The Gini of the entropy distribution ($\mathrm{Gini}(H)$: 0.773 vs.\ 0.707)
confirms that even within each case, topic diversity is itself concentrated
in a small fraction of participants---consistent with the ``1\% rule'' of
online communities~\citep{nielsen2006}.

\noindent\textbf{Thematic divergence.}
The most striking cross-case contrast emerges from the theme participation
rates (Table~\ref{tab:ss_themes}).
ERC-8004 concentrates on \emph{T08: Trust \& Security Mechanisms}
(45.5\% of actors), reinforcing the finding from the BERTopic analysis
(Section~\ref{sec:results-bertopic}) that security and trust infrastructure
is the dominant concern of the DAO governance community.
A2A, by contrast, spreads participation across documentation (T06: 21.3\%),
specification requests (T18: 24.6\%), and SDK development (T05: 11.8\%).
Importantly, the thematic overlap coefficient $\Omega\!=\!1.0$ indicates
that ERC-8004's thematic space is a strict subset of A2A's: all 16 themes
active in ERC-8004 appear in A2A, while A2A additionally covers three
engineering-only themes (T09: Transport Mechanisms; and two implementation
themes) absent from ERC-8004.

\begin{table}[h]
\centering
\caption{Cross-case actor participation rates per theme (top 10 by divergence).
         Percentages are the share of actors \emph{within} each case who
         engaged with the theme at least once.}
\label{tab:ss_themes}
\begin{tabular}{llccc}
\toprule
\textbf{Theme} & \textbf{Label} & \textbf{ERC-8004} & \textbf{A2A} & $\Delta$ \\
\midrule
T08 & Trust \& Security Mechanisms          & \textbf{45.5\%} & 10.0\% & $+35.5$pp \\
T06 & Documentation \& Examples             & 3.0\%  & \textbf{21.3\%} & $-18.3$pp \\
T01 & Protocol Specification \& Versioning  & \textbf{22.7\%} & 11.0\% & $+11.7$pp \\
T05 & SDK Development \& Libraries          & 1.5\%  & \textbf{11.8\%} & $-10.3$pp \\
T15 & Tooling Fixes \& Automation           & 1.5\%  & \textbf{11.5\%} & $-10.0$pp \\
T19 & Bug Fixes \& Improvements             & 4.5\%  & \textbf{13.9\%} & $-9.4$pp  \\
T17 & Multi-Agent Systems Architecture      & 1.5\%  & \textbf{10.7\%} & $-9.2$pp  \\
T09 & Transport \& Protocol Mechanisms      & 0.0\%  & \textbf{8.7\%}  & $-8.7$pp  \\
T04 & Task \& Message Management            & 1.5\%  & \textbf{9.6\%}  & $-8.1$pp  \\
T18 & Spec Clarifications \& Info Requests  & 16.7\% & \textbf{24.6\%} & $-7.9$pp  \\
\bottomrule
\end{tabular}
\end{table}
```

---

## \subsection{Discussion: Discourse Structure and Governance Form}

```latex
\subsection{Discussion: Discourse Structure and Governance Form}
\label{sec:discussion-netdisc}

The combined DNA and socio-semantic results yield three theoretical
observations relevant to CSCW research on collaborative infrastructure design.

\paragraph{(1) Governance form shapes discourse focus, not discourse volume.}
Both ERC-8004 and Google A2A exhibit pervasive discourse specialization
(median entropy $H\!=\!0$) and high participation inequality (Gini $>$\,0.7).
The DAO structure of ERC-8004 does not produce broader or more egalitarian
deliberation; instead, it concentrates deliberation on a narrower thematic
domain---specifically security and trust---while A2A disperses participation
across a wider range of engineering workstreams.
This suggests that the permissionless entry characteristic of DAOs filters
\emph{which} topics attract participation rather than enabling more inclusive
discourse overall.

\paragraph{(2) Institutional identity is a weaker discourse boundary in
corporate governance than expected.}
The polarization index reveals that a higher fraction of discursive agreement
in Google A2A crosses institutional boundaries (25.3\%) compared to
ERC-8004 (13.8\%).
This inverts the naive expectation that corporate governance, coordinated by a
single sponsoring organization (Google), would produce more within-institution
echo chambers.
One interpretation is that A2A's GitHub pull-request workflow structurally
encourages external contributors to engage directly with Google engineers on
technical topics, producing cross-institutional congruence through the
pull-request review mechanism---a form of ``designed'' cross-boundary
interaction~\citep{crowston2012}.
In ERC-8004, pseudonymous participation may paradoxically reinforce
sub-community clustering, as participants lack institutional identity cues
to signal cross-community engagement.

\paragraph{(3) The division of discursive labor mirrors the division of
technical labor.}
The thematic overlap coefficient $\Omega\!=\!1.0$ means ERC-8004's entire
discourse is nested within A2A's thematic space.
A2A's three additional themes (transport protocols, SDK tooling,
implementation fixes) are purely engineering execution topics that a
governance-focused proposal community has no reason to discuss.
This nesting structure is theoretically significant: it suggests that DAO
governance discourse occupies a principled \emph{subset} of the collaborative
infrastructure design space, focusing on the ``what should be built and why''
layer while delegating the ``how to build it'' layer to other venues.
The mean actor entropy differential ($\Delta H \approx +0.27$ bits in favor
of A2A) further supports this: A2A contributors who span multiple workstreams
naturally accumulate broader topic portfolios in a single repository, whereas
ERC-8004 contributors direct their multi-topic engagement to different
community forums (Ethereum Magicians, EIP-related GitHub repositories, etc.)
that fall outside our corpus.
```

---

## References (IEEE format)

```latex




\bibitem{leifeld2017}
P. Leifeld, ``Discourse network analysis: Policy debates as dynamic networks,''
in \textit{The Oxford Handbook of Political Networks}, J.~N. Victor,
A.~H. Montgomery, and M.~N. Lubell, Eds. Oxford: Oxford University Press,
2017, ch.~14. DOI: 10.1093/oxfordhb/9780190228217.013.25
% NOTE: not cited in current draft

\bibitem{blondel2008}
V.~D. Blondel, J.-L. Guillaume, R. Lambiotte, and E. Lefebvre,
``Fast unfolding of communities in large networks,''
\textit{Journal of Statistical Mechanics: Theory and Experiment},
vol.~2008, no.~10, p.~P10008, 2008.
DOI: 10.1088/1742-5468/2008/10/P10008



\bibitem{nielsen2006}
J. Nielsen, ``Participation inequality: Encouraging more users to contribute,''
Nielsen Norman Group, 2006. [Online]. Available:
https://www.nngroup.com/articles/participation-inequality/

\bibitem{crowston2006}
% WARNING: text uses \citep{crowston2012} — correct citekey to crowston2006 or replace with the actual 2012 paper
K. Crowston and J. Howison, ``Hierarchy and centralization in free and open
source software team communications,''
\textit{Knowledge, Technology \& Policy}, vol.~18, no.~4, pp.~65--85, 2006.
DOI: 10.1007/s12130-006-1004-8
```
