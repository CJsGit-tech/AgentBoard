---
name: "US-004 — Create and prioritize tasks"
description: "As a solo builder, I want to record tasks and their priority so that I can organize what needs to happen next."
kind: "user-story"
tags: ["feature:task-coordination", "concern:data-integrity"]
---

> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

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
