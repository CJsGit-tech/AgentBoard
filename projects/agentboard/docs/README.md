---
name: "AgentBoard Documents"
description: "Indexes AgentBoard's vision, stories, architecture, designs, and tickets."
kind: "document-index"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking"]
---

# AgentBoard Documents

- [Run the AgentBoard app](../README.md) — Docker Compose, browser pairing, and MCP clients
- [Product Vision](product-vision.md)
- [Designs](designs/README.md) — profile and tokens
- [User Stories: titles and features](user-stories/README.md)
- [Technical Architecture: overview and topics](technical-architecture/README.md)
- [Module diagram](technical-architecture/system-architecture.svg)
- [Engineering tickets](tickets/README.md) — work by role, type, and dependency
- [Verification report](review-report.md) — observed behavior and open release checks

Docker Compose is the first install/run path. Once AgentBoard is available and connected, AgentBuild writes directly to canonical app records; automatic AgentBuild launch/readiness probing is undefined and deferred. Markdown files are a separate opt-in file-only mode for users who choose not to install/use the app. In file-only mode, start with an index and open only relevant files. Metadata and the [tag guide](tag-vocabulary.md) use the [shared machine-readable vocabulary](tag-vocabulary.json). Tags find candidates; links preserve traceability. Previous combined documents are archived in history/plain-folder-refactor-2026-11-17.
