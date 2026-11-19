---
name: "AgentBoard — Design index"
description: "Routes readers to AgentBoard's concise desktop design topics and approved mockups."
kind: "design-index"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:accessibility", "concern:reliability"]
---

# AgentBoard — Design index

> Owner: Product Designer | Version: 0.1.5 | Status: draft | Last Updated: 2026-11-18

Clean, minimal design with progress visualizations and operational tables/boards. Palette, dimensions and layout defaults remain proposals.

Target: desktop browser on a personal computer with local Docker Compose. Responsive review covers resized windows and zoom; phone/native layouts are outside scope.

Open only the topic and companion links needed for your task.

| Task | Read | Required companion |
| --- | --- | --- |
| Navigate screens | [navigation-layout](navigation-layout.md) | Shared states |
| Apply visual rules | [visual-system](visual-system.md) | Tokens |
| Keyboard and focus | [accessibility](accessibility.md) | Shared states |
| Loading, errors and drafts | [interaction-states](interaction-states.md) | None |
| Operate tickets | [tables-boards](tables-boards.md) | Shared states |
| Track progress | [progress-visualizations](progress-visualizations.md) | Shared states |
| Read/compare documents | [documents-history](documents-history.md) | History + approvals |
| Use AgentBuild records and tag filters | [artifact-operations](artifact-operations.md) | Tables/boards + document history |
| Review activity | [activity-logs](activity-logs.md) | Shared states |
| Understand approvals | [approval-states](approval-states.md) | Shared states + accessibility |

[Tokens](design-tokens.json) define visual values. [Architecture](../technical-architecture/README.md) defines implementation contracts. Screen/story mapping is in navigation.

[Approved screens](screens/README.md): mocked desktop frontend approved 2026-11-18. See [verification](screens/evidence/latest.json). Other draft specifications and production integrations remain unapproved.
