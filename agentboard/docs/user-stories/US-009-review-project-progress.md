---
name: "US-009 — Review project progress"
description: "As a solo builder, I want an overview of project progress and blockers so that I can choose what needs attention next."
kind: "user-story"
tags: ["feature:progress-tracking", "concern:accessibility", "concern:reliability"]
---

> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

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
