# AgentBoard — Design index

> Owner: Product Designer | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

Clean, minimal design with useful progress visualizations and operational tables/boards. This is a draft specification; palette, dimensions, table-first layout and defaults remain proposals.

Target: desktop browser on a personal computer with local Docker Compose. Responsive review covers resized windows and zoom; phone/native layouts are outside scope.

Open the topic for your task, then its **Required context** links. Do not load every topic by default.

| Task | Read | Required companion |
| --- | --- | --- |
| Navigate screens | [navigation-layout](navigation-layout.md) | Shared states + accessibility |
| Apply visual rules | [visual-system](visual-system.md) | Tokens + accessibility |
| Keyboard, focus and contrast | [accessibility](accessibility.md) | Shared states |
| Loading, errors and drafts | [interaction-states](interaction-states.md) | None |
| Operate tickets | [tables-boards](tables-boards.md) | Shared states + accessibility |
| Track progress | [progress-visualizations](progress-visualizations.md) | Shared states + accessibility |
| Read/compare documents | [documents-history](documents-history.md) | Shared states + accessibility + approvals |
| Review activity | [activity-logs](activity-logs.md) | Shared states + accessibility |
| Understand approvals | [approval-states](approval-states.md) | Shared states + accessibility |

[Tokens](design-tokens.json) are the single source for visual values. [Architecture](../technical-architecture/README.md) governs implementation contracts. Screen/story mapping is in navigation; feature rules live in their topic.

Before implementation, validate dense Overview, Tickets, Document History and Activity screens with keyboard and zoom. Contract questions are recorded in their relevant topics.
