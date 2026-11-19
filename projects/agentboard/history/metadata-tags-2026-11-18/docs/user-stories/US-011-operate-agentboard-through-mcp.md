> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-011 — Operate AgentBoard through MCP

- **Story:**
  - As a solo builder, I want Codex and Claude to use AgentBoard tools so that agents can coordinate project work without manually copying information.
- **Acceptance Criteria:**
  - Given a configured Codex desktop, Codex CLI, Claude Code, or Claude Desktop client, when it connects, then it can discover typed tools for projects, roles, tasks, documents, revisions, and activity.
  - Given an authenticated agent, when it creates or reads a project record, task, role, or document, then the operation needs no per-operation approval and enforces project boundaries and input validation.
  - Given a retried create call with the same operation key and payload, when it is processed again, then no duplicate record is created.
  - Given an agent operation, when it succeeds or fails, then the result identifies the outcome without claiming that AgentBoard launched or controlled the agent.
  - Given a client that lacks approval support, when it reads or creates records, then those operations remain available while Update/Delete remain protected.
- **Associated Features:**
  - Product project management
  - Agent role management
  - Task coordination
  - Document management
