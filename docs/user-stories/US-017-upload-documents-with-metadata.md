---
name: "US-017 — Upload documents with extracted metadata"
description: "Lets a builder upload a Markdown document and review its extracted metadata before saving it to AgentBoard."
kind: "user-story"
tags: ["feature:document-management"]
---

> Owner: Product Manager | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18

### US-017 — Upload documents with extracted metadata

- **Story:**
  - As a solo builder, I want to upload an external Markdown document and review its extracted metadata so that I can add useful project context without re-entering its details.
- **Acceptance Criteria:**
  - Given a supported Markdown file, when I upload it, then AgentBoard reads its content and recognizes valid `name`, `description`, `kind`, and `tags` frontmatter.
  - Given missing, malformed, or unknown metadata, when I preview the upload, then AgentBoard shows the issue and lets me correct fields before creating the document.
  - Given metadata extracted from an upload, when the preview is displayed, then extracted values are identified as source-provided and are not treated as instructions or as confirmation of approval, owner, or task status.
  - Given a confirmed upload, when the document is saved, then AgentBoard preserves the original content, records the upload source and time, and stores the reviewed metadata for filtering.
  - Given a file format the first release does not support, when I select it, then AgentBoard explains the supported format without creating a partial record.
- **Associated Features:**
  - Document management
