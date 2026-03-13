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
- Technical: 26
- Process: 11
- Governance-Principle: 2

**Stance distribution:**
- Modify: 14
- Support: 13
- Neutral: 12

**Institutions involved:**
- Independent: 29
- Google: 6
- Microsoft: 4

### Key annotated comments

**edenreich** (Independent, Technical, stance=Neutral)
> # Description  Thank you for opening a Pull Request! Before submitting your PR, there are a few things you can do to make sure it goes smoothly:  - [x] Follow the [`CONTRIBUTING` Guide](https://g
*Key point: Add tasks/list method with filtering and pagination to specification*

**edenreich** (Independent, Technical, stance=Neutral)
> Not sure about this linting error of 404.html file, I didn't even touched this file. I guess it will be fixed on the main upstream.
*Key point: Linting error in 404.html file not caused by author, expected to be fixed upstream*

**holtskinner** (Google, Process, stance=Support)
> I did a rebase to pull in the updates from main so the lint errors don't mess with your PR.  @kthota-g and @pstephengoogle Can you please review/approve this change to the spec?
*Key point: Requesting review and approval from kthota-g and pstephengoogle for spec changes after main rebase*

**ReubenBond** (Independent, Technical, stance=Modify)
> If I send a `tasks/list` command to a public-facing compliant A2A server without specifying a `contextId`, will I receive everyone's tasks? I believe the answer should be no, but the spec appears to n
*Key point: Spec should clarify implicit scope when contextId omitted in tasks/list - implementation-defined or explicit parameter*

**edenreich** (Independent, Technical, stance=Support)
> > If I send a `tasks/list` command to a public-facing compliant A2A server without specifying a `contextId`, will I receive everyone's tasks? I believe the answer should be no, but the spec appears to
*Key point: Asks whether tasks/list without contextId exposes all users' tasks; suggests implementation-defined implicit scoping.*

**edenreich** (Independent, Process, stance=Neutral)
> I had to cleanup some changes that are not related to this Pull Request scope - it seems like some of the changes were removed from main upstream on the latest version - not sure exactly what went wro
*Key point: Describes cleanup of unrelated changes due to rebase issues with upstream main branch.*

**darrelmiller** (Microsoft, Process, stance=Neutral)
> @a2aproject/a2a-tsc I'm assuming that including this feature would require a minor version bump.  Features like this are a good reason for why we need to implement a proposal system because if we don'
*Key point: Features require minor version bumps; need proposal system to prevent merge conflicts during version changes.*

**darrelmiller** (Microsoft, Technical, stance=Modify)
> @edenreich   I would expect the two most common filter criteria would be: - all in-progress tasks - recently completed tasks  The current set of filter criteria make those scenarios a bit tricky
*Key point: Suggests adding status array filter, lastUpdateDateTime filter, and taskReference result option for efficiency.*

**edenreich** (Independent, Technical, stance=Support)
>  > @edenreich >  > I would expect the two most common filter criteria would be: >  > * all in-progress tasks > * recently completed tasks >  > The current set of filter criteria make those sce
*Key point: Supports adding status array filter and lastUpdateDateTime for better task filtering and observability.*

**swapydapy** (Independent, Technical, stance=Support)
> +1 to filters for lastUpdatedtime, list of task statuses.  Also should we consider a param to include artifacts or not, to make the Task result payload smaller.
*Key point: Supports adding lastUpdatedTime and task status filters; suggests param to optionally include artifacts to reduce payload size.*

**edenreich** (Independent, Technical, stance=Support)
> > +1 to filters for lastUpdatedtime, list of task statuses. >  > Also should we consider a param to include artifacts or not, to make the Task result payload smaller.  @swapydapy Yea makes sense, 
*Key point: Supports adding filters for lastUpdatedTime, task statuses, and artifact inclusion parameter to reduce payload size.*

**edenreich** (Independent, Technical, stance=Neutral)
> @darrelmiller @swapydapy I've added both filters to make it more flexible can you have a look?
*Key point: Requesting review of added filters for flexibility*

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

**Argument types:**
- Technical: 4
- Process: 4
- Off-topic: 1

**Stance distribution:**
- Modify: 3
- Support: 2
- Oppose: 2
- Neutral: 2

**Institutions involved:**
- Independent: 5
- Cisco: 2
- Microsoft: 2

### Key annotated comments

**lkawka** (Independent, Technical, stance=Support)
> The new `task/list` method's [specification](https://github.com/a2aproject/A2A/blob/main/docs/specification.md#74-taskslist) dictates that tasks must be ordered by the last update time. However, the c
*Key point: Add last update time field to Task message for stable task ordering by update time*

**amye** (Independent, Technical, stance=Oppose)
> Sigh, it really does need duration. Reverting!
*Key point: Contributor reverts their change, confirming duration field is required*

**He-Pin** (Independent, Off-topic, stance=Neutral)
> I think is is great, mcp just added this too.
*Key point: Brief positive comment without substantive engagement with proposal*

**geneknit** (Independent, Technical, stance=Modify)
> Discussion moving to Discord and the main issue. Concern about having two that serve the same value. cc: @darrelmiller
*Key point: Concern about having two features serve the same value in the protocol*

**Tehsmash** (Cisco, Technical, stance=Modify)
> After discussion in the TSC meeting on 2026/01/6, we agreed to leave the fields in Task as they are and change the filter for ListTasks to `status_timestamp_after` to indicate that its based on the ta
*Key point: Change ListTasks filter to status_timestamp_after to reflect task status only*

**darrelmiller** (Microsoft, Process, stance=Modify)
> @Tehsmash I think that means we could close this PR and combine the proposed naming change with this PR to change the datatype https://github.com/a2aproject/A2A/pull/1288 
*Key point: Close this PR and combine the proposed naming change with PR #1288*

**Tehsmash** (Cisco, Process, stance=Support)
> > @Tehsmash I think that means we could close this PR and combine the proposed naming change with this PR to change the datatype #1288  👍  happy for it to be combined (whatever makes it turn around 
*Key point: Supports combining this PR with #1288 to expedite the naming change.*

**darrelmiller** (Microsoft, Process, stance=Oppose)
> Closing this PR in favour of #1358 
*Key point: Closing this PR, redirecting to alternative PR #1358*

**amye** (Independent, Process, stance=Neutral)
> /cancel-vote   #1358 has the correct one + gitvote has added Stephen already, so yay! We'll restart this. 
*Key point: Cancelling current vote; will restart as #1358 has correct version and Stephen added to gitvote.*

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