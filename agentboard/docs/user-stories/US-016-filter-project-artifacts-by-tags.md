---
name: "US-016 — Filter project artifacts by tags"
description: "Lets people and agents retrieve project documents and tickets using feature and concern tags."
kind: "user-story"
tags: ["feature:document-management", "feature:task-coordination"]
---

> Owner: Product Manager | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18

### US-016 — Filter project artifacts by tags

- **Story:**
  - As a solo builder, I want to filter project documents and tickets by feature and concern tags so that I and connected agents can open only the context relevant to current work.
- **Acceptance Criteria:**
  - Given a project, when I browse documents or tickets, then I can filter by one or more feature tags and concern tags.
  - Given multiple tags in one namespace, when I apply them, then records matching any selected tag in that namespace are included.
  - Given feature and concern filters together, when I apply them, then a record must match at least one selected tag in each nonempty namespace.
  - Given an unknown or malformed tag, when the UI or MCP tool receives it, then it returns a clear validation error and does not silently return unfiltered results.
  - Given a connected Codex or Claude client, when it lists documents or tickets with tag filters, then it receives the same project-scoped results and pagination behavior as the web application.
  - Given a ticket or document created through AgentBuild, when it is saved to AgentBoard, then its valid feature and concern tags are stored and available to filters.
- **Associated Features:**
  - Document management
  - Task coordination
