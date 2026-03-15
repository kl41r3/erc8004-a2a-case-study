# Git-Vote PRs: Governance Analysis

Two pull requests in the Google A2A repository that triggered formal TSC votes via `git-vote[bot]`.
Labels: `TSC Review` + `gitvote`. These are the only two PRs in the dataset with an explicit voting mechanism.

## Background: What is git-vote?

`git-vote[bot]` is a GitHub app that enables formal voting on PRs via emoji reactions on a pinned comment.
A TSC (Technical Steering Committee) member types `/vote` to initiate; binding voters are pre-registered members.
Threshold: a majority of binding voters must approve. The bot periodically posts vote-status updates.

## Why Does This Matter Theoretically?

The existence of a formal voting mechanism in an ostensibly 'open' corporate project is analytically significant:
- It reveals that Google A2A has a **defined inner circle** (TSC) with binding authority, unlike the permissionless ERC process
- Invoking `/vote` signals that **ordinary review consensus failed** — a governance escalation point
- PR #1206's trajectory (vote → TSC call → Discord → /cancel-vote → superseding PR) shows that **key decisions happen off-platform**, reducing transparency

---

## PR #831: feat(spec): Add `tasks/list` method with filtering and pagination

**URL**: https://github.com/a2aproject/A2A/pull/831
**Outcome**: PASSED (merged)

### What the PR proposes

Adds a new `tasks/list` RPC method to the A2A spec, allowing clients to query tasks with filtering (by status, contextId, lastUpdatedAfter) and pagination. Vote called because the feature was a substantive spec addition requiring TSC sign-off before merge.

### Vote mechanics

| | |
|---|---|
| `/vote` called by | amye |
| `/cancel-vote` called by | N/A |
| git-vote bot messages | 10 |
| Human participants | edenreich, holtskinner, darrelmiller, swapydapy, amye, muscariello, mikekistler, yarolegovich, ReubenBond, pstephengoogle |

### LLM annotation summary (human comments only)

**Argument types:**
- Technical: 1

**Stance distribution:**
- Neutral: 1

**Institutions involved:**
- Google: 1

### Key annotated comments

**pstephengoogle** (Google, Technical, stance=Neutral)
> > > > @edenreich The suggestion to exclude artifacts is an alternative way to address the size concerns I had. > >  > >  > > Great! > > > I am good with these changes. My concern now is if we merg
*Key point: Discussing version bump to 0.4.0, SDK 0.3.x support requirements, and backward compatibility for new endpoints*

---

## PR #1206: feat(spec): Add last update time to `Task`

**URL**: https://github.com/a2aproject/A2A/pull/1206
**Outcome**: CLOSED (superseded by #1358)

### What the PR proposes

Proposes adding a `lastUpdateTime` field to the Task data model, needed by `tasks/list` ordering. Vote called but then `/cancel-vote` issued after TSC meeting on 2026-01-06 resolved the naming dispute: the group agreed to rename the filter parameter to `status_timestamp_after` instead, removing the need for a new field. Discussion migrated to Discord and a TSC call — key decision was offline.

### Vote mechanics

| | |
|---|---|
| `/vote` called by | darrelmiller, amye, amye |
| `/cancel-vote` called by | amye |
| git-vote bot messages | 46 |
| Human participants | amye, darrelmiller, Tehsmash, lkawka, He-Pin, geneknit |

### LLM annotation summary (human comments only)

*(No annotation available)*

### Key annotated comments

---

## Comparative Governance Interpretation

| Dimension | PR #831 (tasks/list) | PR #1206 (lastUpdateTime) |
|-----------|---------------------|--------------------------|
| Outcome | Passed and merged | Closed, superseded |
| Decision venue | GitHub comments | TSC meeting + Discord |
| Transparency | High (all on-platform) | Low (key decision offline) |
| Vote trigger | Feature maturity, TSC sign-off | Data model design dispute |
| Resolution time | ~4 months | ~2 months then cancelled |

The contrast between #831 and #1206 illustrates a **dual-mode decision process** in A2A governance:
technical changes with rough consensus proceed through standard review; structurally contested changes
escalate to TSC voting — and sometimes further to off-platform coordination (Discord, synchronous calls).
This opacity gradient is absent in the ERC-8004 process, where all deliberation occurs on Ethereum Magicians forum.