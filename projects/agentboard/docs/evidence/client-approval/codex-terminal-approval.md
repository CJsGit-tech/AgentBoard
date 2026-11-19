# Codex terminal approval verification

Run on November 19, 2026 (Taipei) with installed `codex-cli 0.169.0-alpha.11.1`.

The installed CLI ran in a pseudo-terminal with a temporary `CODEX_HOME`. It connected over authenticated Streamable HTTP to a disposable AgentBoard API and Postgres database. A deterministic Responses API mock on loopback requested one `update_project` tool call. It used a dummy model key. The test driver supplied keypresses to the actual terminal menus.

| Terminal case | Server and persisted result |
| --- | --- |
| Pause on AgentBoard’s approval form | The form showed the target, base revision, request ID and proposed purpose. An independent read still returned the original purpose at revision 1. |
| Select True | AgentBoard returned `success` and `applied: true`. A fresh read returned the new purpose at revision 2. |
| Select False | AgentBoard returned `rejected` and `applied: false`. A fresh read returned the original purpose at revision 1. |
| Select True after an intervening edit | AgentBoard returned `stale_revision` and `applied: false`. A fresh read returned the intervening edit at revision 2. |
| Run `codex exec` with `approval_policy = "never"` | Codex refused the tool invocation because its own permission prompt required input. A fresh read returned the original record at revision 1. |

To repeat, start a disposable AgentBoard instance with an empty migrated database and one temporary credential flagged for interactive approval. Create a fixture project, start `codex` with an isolated config pointing to the test MCP server and loopback model mock, and have the mock request `update_project` at revision 1. Select **Allow** at Codex’s tool permission prompt. The AgentBoard form appears separately. For the stale test, commit a second change to the fixture before selecting **True**. Verify each result with a fresh project read.

An independent reviewer read the terminal captures and MCP results. This run used a local mock provider and covered one update operation in the installed terminal UI. Graphical desktop verification remains open. [Recorded results](codex-terminal-results.json)
