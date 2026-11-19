> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

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
