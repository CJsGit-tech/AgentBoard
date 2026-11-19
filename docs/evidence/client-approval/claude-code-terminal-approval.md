# Claude Code terminal approval verification

Run on November 19, 2026 (Taipei) with installed Claude Code 2.1.327. The CLI ran in an interactive pseudo-terminal with an isolated config and `--permission-mode manual`. It connected to a disposable AgentBoard API and Postgres database through Streamable HTTP. A deterministic localhost Messages mock selected the MCP tools. The test driver supplied the terminal input.

Claude Code’s `/mcp` view showed the server connected with 31 tools. After `update_project`, its terminal displayed **MCP server “agentboard” requests your input**, the proposed change, an `approved` checkbox and **Accept** and **Decline** controls.

| Terminal case | Persisted result |
| --- | --- |
| Check `approved` and select Accept | The project purpose changed and its revision advanced from 1 to 2. |
| Leave `approved` unchecked and select Decline | The original project purpose and revision 1 were preserved. |
| Check `approved` and select Accept after an intervening edit | The tool returned `stale_revision`. Postgres retained the intervening purpose at revision 2 and recorded the original approval request as stale. |

Repeat with a fresh fixture project for each case. Start Claude Code without a positional prompt, wait for AgentBoard to connect, then send the synthetic update prompt through its terminal. After choosing an action, read the fixture independently to verify its purpose and revision.

These results cover the installed terminal client and a single project update operation. The graphical Claude Desktop client is a separate verification target. [Recorded results](claude-code-terminal-results.json)
