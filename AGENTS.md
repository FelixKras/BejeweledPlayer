# Agent Instructions

## Memory Plane

Use the project Memory Plane for all substantial work. Follow `.agents/skills/memory-plane/SKILL.md`.

Before making substantial changes:

```bash
memory-plane status
memory-plane retrieve "<current task and relevant entities>" --scope project --scope team
```

Review relevant approved memories before implementation. Treat proposals as unapproved claims and cite memory IDs and source references when memory materially affects a decision.

After major changes or decisions, propose the smallest reusable durable record covering decisions, constraints, corrected assumptions, procedures, blockers, and next actions. Do not store transcripts, secrets, credentials, raw personal data, or transient reasoning.

```bash
memory-plane propose \
  --kind <decision|procedure|claim|episode|task|constraint> \
  --title "<concise title>" \
  --body "<durable outcome and rationale>" \
  --scope project \
  --author "<agent identity>" \
  --confidence <0-1> \
  --source "<canonical file, command output, issue, URL, or memory ID>" \
  --tag "<relevant entity>"
```

Agents create proposals, not approved facts. A reviewer must approve shared durable memory with `memory-plane approve`.
