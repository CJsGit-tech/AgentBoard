# Document History

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

Document changes lock/check the current revision, preserve the outgoing content, commit the new current version, then prune older history to the newest three previous versions in the same transaction. Restore copies a retained version into a new current version, obeying the same bound. Compare is read-only; agents can read and compare all retained content. Current document timestamp changes only on successful content updates. Deleted document bodies and versions are removed together; retain only minimal deletion metadata in the bounded event log. No hidden unbounded revision archive.


See [approval flow](approval-flow.md) for agent restores and [MCP tools](mcp-tools.md) for interfaces.
