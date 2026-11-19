> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-005 — Assign task responsibility

- **Story:**
  - As a solo builder, I want to assign a task to an agent role or myself so that ownership is explicit.
- **Acceptance Criteria:**
  - **Given** a task and a role in the same project, **when** I assign the role, **then** the task shows that role as its owner.
  - **Given** a task, **when** I take ownership myself or reassign it, **then** the current owner is updated without discarding the task's work or documents.
  - **Given** a task with no owner, **when** I view it, **then** it is explicitly labeled Unassigned.
  - **Given** a role belonging only to another project, **when** I choose an owner, **then** it cannot be assigned to the current task.
  - **Given** a role assignment, **when** it is saved, **then** it records responsibility; Codex/Claude execute independently and can report their activity through MCP.
- **Associated Features:**
  - Agent role management
  - Task coordination
