---
name: "US-011 — Operate AgentBoard through MCP"
description: "As a solo builder, I want Codex and Claude to use AgentBoard tools so that agents can coordinate project work without manually copying information."
kind: "user-story"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "concern:compatibility", "concern:authorization", "concern:security"]
---

> Owner: Product Manager | Version: 0.1.5 | Status: draft | Last Updated: 2026-11-18

### US-011 — Operate AgentBoard through MCP

- **Story:**
  - As a solo builder, I want Codex and Claude to use AgentBoard tools so that agents can coordinate project work without manually copying information.
- **Acceptance Criteria:**
  - Given a configured Codex desktop, Codex CLI, Claude Code, or Claude Desktop client, when it connects, then it can discover typed tools for projects, roles, tasks, documents, revisions, and activity.
  - Given the builder has started AgentBoard with Docker Compose, when an AgentBuild command needs project records, then it reuses the configured MCP connection.
  - Given an AgentBuild planning command and a verified AgentBoard connection, when the agent saves its completed artifact, then it writes the canonical record directly to the matching AgentBoard project and reports the returned record ID.
  - Given the configured app is stopped or unreachable, when the requested operation needs AgentBoard, then the skill reports the connection issue and stops without redirecting writes to files.
  - Given AgentBoard is not installed and the user has not selected a target, when an AgentBuild command needs to save work, then the skill offers file-only mode or cancel and writes nothing before the choice.
  - Given an authenticated agent, when it creates or reads a project record, task, role, or document, then the operation needs no per-operation approval and enforces project boundaries and input validation.
  - Given a retried create call with the same operation key and payload, when it is processed again, then no duplicate record is created.
  - Given an agent operation, when it succeeds or fails, then the result identifies the outcome without claiming that AgentBoard launched or controlled the agent.
  - Given a client that lacks approval support, when it reads or creates records, then those operations remain available while Update/Delete remain protected.
- **Associated Features:**
  - Product project management
  - Agent role management
  - Task coordination
  - Document management
