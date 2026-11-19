> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

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
