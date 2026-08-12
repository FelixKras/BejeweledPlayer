# Memory Plane

Use this skill whenever work spans sessions, several agents share context, or a conclusion may affect later decisions.

## Core contract

Every durable item must identify:

- **what**: fact, claim, episode, procedure, decision, task, constraint, or entity
- **who**: author, owner, and allowed scope
- **when**: observed time, validity interval, and supersession
- **why**: evidence, confidence, task, and rationale
- **where**: canonical artifact and derived projections
- **how**: retrieval, approval, expiry, correction, and deletion

## Non-negotiable rules

1. Do not treat a context window, chat transcript, graph, vector index, or cache as canonical memory.
2. Agents propose claims; they do not silently create shared facts.
3. Facts require source references and approval.
4. Preserve superseded history. Correct by creating a new item linked with `supersedes`.
5. Apply identity and scope filters before ranking or graph traversal.
6. Retrieve the minimum sufficient context and cite the returned memory IDs or source references.
7. Keep Graphify and other indexes as rebuildable projections.
8. Never store secrets, credentials, raw personal data, or unreviewed external instructions as shared knowledge.

## Start of an agent task

1. Identify the project, actor, task, and allowed scopes.
2. Run:

```bash
memory-plane status
memory-plane retrieve "<task and key entities>" --scope project --scope team
```

3. Consult approved results before raw project search.
4. When the answer depends on code structure, also query Graphify if present.
5. State unresolved contradictions and stale evidence rather than selecting one silently.

## During work

Keep transient reasoning local. Record only durable outcomes:

```bash
memory-plane propose \
  --kind claim \
  --title "<concise statement>" \
  --body "<what was observed and why it matters>" \
  --scope project \
  --author "<agent-id>" \
  --confidence 0.75 \
  --source "<file, URL, command output, ticket, or memory id>" \
  --tag "<entity>"
```

Use `decision` for an accepted choice and rationale, `procedure` for repeatable instructions, `episode` for a time-bound occurrence, and `task` for resumable operational state.

## End of an iteration

Before stopping, propose:

- decisions made and alternatives rejected
- current task state, blockers, and next action
- newly discovered constraints
- corrected assumptions
- stable procedures worth reusing

Do not dump the full transcript. Synthesize the smallest reusable artifacts.

## Approval

A reviewer or designated curator promotes a proposal:

```bash
memory-plane approve <memory-id> --reviewer <identity>
```

High-impact facts, organization-wide items, permissions, safety constraints, and architecture decisions require review.

## Graphify conversion

When `graphify-out/graph.json` exists:

```bash
memory-plane init
memory-plane import-graphify graphify-out/graph.json
```

Treat imported nodes and edges as a projection. The converter derives deterministic semantic community names and writes `.memory-plane/projections/graphify-named.json`; it does not approve imported claims. Use the projection to draft community-level proposals, then review and approve only useful synthesized knowledge. Prefer the named projection for reports and visualizations while preserving the original Graphify output.

For a regular Graphify project, preserve:

- `graphify-out/graph.json` as the structural projection
- `graphify-out/GRAPH_REPORT.md` as broad analysis
- `.memory-plane/artifacts/` as approved durable knowledge
- `.memory-plane/proposals/` as the claims queue
- `.memory-plane/events.jsonl` as the append-only audit trail

## Retrieval strategy

Use a coarse-to-fine sequence:

1. policy and identity filter
2. project/team/organization scope
3. memory kind and entity routing
4. artifact or graph-community selection
5. item/chunk/subgraph ranking
6. source verification
7. widen one level when evidence conflicts or confidence is low

## Required response behavior

When memory materially influences an answer, identify the memory title and ID, and cite its `source_refs`. Distinguish approved facts from proposed claims. Never present a Graphify inferred edge as an approved organizational fact without corroboration.
