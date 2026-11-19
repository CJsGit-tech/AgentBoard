# User Stories — AgentBoard

> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17
> Based on: Product Vision v0.1.2 (`docs/product-vision.md`, draft)

### US-001 — Create a product project

- **Story:**
  - As a solo builder, I want to create a project with its purpose so that its work and documents share a clear context.
- **Acceptance Criteria:**
  - **Given** a project name and optional purpose, **when** I save a new project, **then** it appears in my project list and opens with the saved details.
  - **Given** a blank or whitespace-only name, **when** I save, **then** creation is prevented with a clear explanation and my other input is retained.
  - **Given** an existing project, **when** I change its name or purpose and save, **then** its existing tasks, roles, and documents remain associated with it.
  - **Given** a save failure, **when** creation or editing fails, **then** the app does not report success and preserves my input for retry.
- **Associated Features:**
  - Product project management


### US-002 — Find and switch projects

- **Story:**
  - As a solo builder, I want to find and reopen my projects so that I can resume the right work without mixing contexts.
- **Acceptance Criteria:**
  - **Given** multiple projects, **when** I open the project list and select one, **then** its identity is visible and its tasks, roles, and documents are shown.
  - **Given** an active project, **when** I switch to another, **then** the displayed records belong to the selected project rather than the previous one.
  - **Given** no projects, **when** I open the list, **then** an empty state offers project creation.
  - **Given** projects with the same name, **when** I inspect the list, **then** another visible identifying detail lets me distinguish them.
- **Associated Features:**
  - Product project management


### US-003 — Define project agent roles

- **Story:**
  - As a solo builder, I want to define agent roles and responsibilities so that I can make clear assignments.
- **Acceptance Criteria:**
  - **Given** a project, **when** I save a role with a name and responsibilities, **then** it appears in that project's role list and is available for assignment.
  - **Given** missing required role information, **when** I save, **then** the app identifies the missing information and retains my input.
  - **Given** an assigned role, **when** I edit its responsibilities, **then** the role details update without losing existing task assignments.
  - **Given** a role definition, **when** I view it, **then** its existence does not imply an agent has been launched or is running.
- **Associated Features:**
  - Agent role management


### US-004 — Create and prioritize tasks

- **Story:**
  - As a solo builder, I want to record tasks and their priority so that I can organize what needs to happen next.
- **Acceptance Criteria:**
  - **Given** a selected project, **when** I save a task with a title, optional description, and priority, **then** it appears in that project with its saved details and initial status.
  - **Given** a blank title, **when** I save, **then** the app rejects the task with an explanation and retains my input.
  - **Given** an existing task, **when** I edit its title, description, or priority, **then** its assignment, status, and linked documents are preserved.
  - **Given** tasks with different priorities, **when** I order the task list by priority, **then** the highest-priority tasks appear first.
- **Associated Features:**
  - Task coordination


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


### US-006 — Track task progress and blockers

- **Story:**
  - As a solo builder, I want to update task status and record blockers so that I can coordinate work and identify what needs intervention.
- **Acceptance Criteria:**
  - **Given** a task, **when** I select Planned, In Progress, Blocked, or Done and save, **then** the task displays that status and its last update time.
  - **Given** a task being marked Blocked, **when** I save without a blocker explanation, **then** the app requests an explanation before applying the change.
  - **Given** a blocked task, **when** I resolve the blocker and change its status, **then** it no longer appears as currently blocked.
  - **Given** a completed task requiring more work, **when** I return it to In Progress, **then** it reappears among active work.
  - **Given** a failed status save, **when** the update fails, **then** the app retains the last saved status and clearly shows the failure with a retry option.
- **Associated Features:**
  - Task coordination
  - Progress tracking


### US-007 — Maintain project documents

- **Story:**
  - As a solo builder, I want to create, read, and revise product documents within a project so that I can retain its decisions and context.
- **Acceptance Criteria:**
  - **Given** a project, **when** I save a document with a title and content, **then** it is listed in that project and can be reopened with the saved content.
  - **Given** a saved document, **when** I revise it, **then** the current content and update timestamp change, and the previous content becomes a historical revision.
  - **Given** three previous document versions already exist, **when** another revision is saved, **then** only the current version and the three most recent previous versions remain available.
  - **Given** a missing title or empty content, **when** I save, **then** the app identifies the problem and retains my input.
  - **Given** a failed save, **when** I attempt to leave the editor, **then** the app indicates that changes are unsaved and lets me stay to recover them.
  - **Given** a project with no documents, **when** I open its documents, **then** an empty state offers creation.
- **Associated Features:**
  - Document management


### US-008 — Connect documents and task outputs

- **Story:**
  - As a solo builder, I want to link documents to relevant tasks so that I can find the supporting context and resulting work together.
- **Acceptance Criteria:**
  - **Given** a task and a document in the same project, **when** I link the document as supporting context or an output, **then** the task shows the document and its relationship.
  - **Given** a linked document, **when** I open it from a task, **then** the correct document opens and I can return to the task.
  - **Given** a document already linked with the same relationship, **when** I try linking it again, **then** no duplicate association is created.
  - **Given** a document belonging only to another project, **when** I choose documents to link, **then** it is not offered as a link target.
  - **Given** an existing association, **when** I remove the link, **then** the document itself remains available in the project.
- **Associated Features:**
  - Document management
  - Task coordination


### US-009 — Review project progress

- **Story:**
  - As a solo builder, I want an overview of project progress and blockers so that I can choose what needs attention next.
- **Acceptance Criteria:**
  - **Given** tasks in multiple states, **when** I view project progress, **then** counts for Planned, In Progress, Blocked, and Done match the saved tasks in that project.
  - **Given** a status count, **when** I select it, **then** I can inspect the tasks contributing to it.
  - **Given** blocked tasks, **when** I inspect project blockers, **then** each shows its explanation and owner, including Unassigned where applicable.
  - **Given** a task status change saved successfully, **when** I return to the overview, **then** the totals reflect the saved change.
  - **Given** no tasks, **when** I open progress, **then** the app shows an empty state rather than implying the project is complete.
  - **Given** unavailable project data, **when** the overview cannot load, **then** it shows an error and retry action rather than reporting zero work as fact.
- **Associated Features:**
  - Progress tracking


### US-010 — Review a task's changes

- **Story:**
  - As a solo builder, I want to inspect task ownership and status changes so that I can reconstruct how work progressed.
- **Acceptance Criteria:**
  - **Given** a saved ownership or status change, **when** I inspect task activity, **then** I see the previous value, new value, and time of the change.
  - **Given** several changes, **when** I inspect activity, **then** their order is clear and reopening the task preserves the recorded entries.
  - **Given** an update that failed to save, **when** I inspect activity, **then** no successful change is recorded for that failed attempt.
  - **Given** a task with no retained changes, **when** I inspect activity, **then** an empty state explains that no activity is available within the 30-day retention window.
- **Associated Features:**
  - Progress tracking
  - Task coordination

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


### US-012 — Approve agent updates and deletions in the client

- **Story:**
  - As a solo builder, I want to review agent Update/Delete requests in Codex or Claude so that agents cannot change existing work without my approval.
- **Acceptance Criteria:**
  - Given an agent Update/Delete request, when it arrives, then the existing record remains unchanged until I approve the specific target and proposed change through the client interface.
  - Given a pending request associated with a ticket, when I view the board, then its ticket shows a Needs approval badge separately from Planned, In Progress, Blocked, or Done status.
  - Given approval for a change, when it commits, then the approved change and its audit record are saved together and the badge clears only if no other pending requests remain.
  - Given rejection, timeout, cancellation, or unsupported client approval, when processing finishes, then no business change executes; unsupported approval leaves a pending request and Needs approval badge for later retry.
  - Given a record changed after approval was requested, when an old approval is submitted, then the change is rejected as stale and fresh approval is required.
  - Given an agent assertion that approval was granted, when no verified client approval response exists, then the assertion does not authorize the change.
- **Associated Features:**
  - Task coordination
  - Progress tracking
  - Document management
  - Agent role management
  - Product project management


### US-013 — Report and review agent activity

- **Story:**
  - As a solo builder, I want a logging page showing agent work on tickets so that I can review dispatches, tool calls, and changes in one place.
- **Acceptance Criteria:**
  - Given an agent dispatch, tool call, or external work event, when the agent reports it through MCP, then the log shows agent, ticket when applicable, action, timestamp, outcome, and filterable labels.
  - Given an operation handled by AgentBoard itself, when it completes or fails, then AgentBoard records it automatically and distinguishes server-observed events from agent-reported events.
  - Given activity logs, when I filter by project, ticket, agent, event type, label, or time, then the view shows matching retained events only.
  - Given new committed activity, when I keep the logging page open, then entries appear automatically without manual refresh.
  - Given duplicate event delivery with the same event key, when the event is retried, then only one log entry is retained.
  - Given an unreported external action, when I review the log, then the app does not claim that its external capture is exhaustive.
- **Associated Features:**
  - Progress tracking
  - Task coordination
  - Agent role management


### US-014 — Expire activity after 30 days

- **Story:**
  - As a solo builder, I want activity to expire automatically so that the local log retains no more than 30 days by default.
- **Acceptance Criteria:**
  - Given an event at least 30 days old, when I query activity or task history, then it is excluded even if cleanup has not yet run.
  - Given expired activity, when automatic cleanup runs, then its event records are deleted without deleting current tickets, documents, or their retained revisions.
  - Given the application was stopped past a retention deadline, when it restarts, then expired events are hidden immediately and cleanup resumes.
  - Given the logging page loses its live connection, when reconnection succeeds, then it resumes from retained events and indicates any unavailable interval.
- **Associated Features:**
  - Progress tracking


### US-015 — Read, compare, and restore document revisions

- **Story:**
  - As a solo builder, I want myself and connected agents to inspect document history so that we can rework content using recent revisions.
- **Acceptance Criteria:**
  - Given a document, when I or an authenticated agent requests its history, then the current version and up to three previous versions are readable with version identifiers and update timestamps.
  - Given two retained revisions, when I compare them, then their content differences are available for review.
  - Given a retained revision selected for restore, when a builder saves it or an agent obtains client approval to restore it, then its content becomes a new current version using the same three-previous-version limit.
  - Given a version removed by the retention limit, when I or an agent requests it, then an unavailable-version response is returned without substituting another revision.
  - Given a failed or unapproved document update, when I inspect its history, then no new content version has been added.
- **Associated Features:**
  - Document management

