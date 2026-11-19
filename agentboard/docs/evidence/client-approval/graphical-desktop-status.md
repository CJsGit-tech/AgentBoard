# Graphical desktop verification status

November 19, 2026 (Taipei). The installed app bundles were inspected for isolated profile options. This check kept the live AgentBoard credentials and ordinary application profiles out of the test.

| App | Observed result |
| --- | --- |
| Claude Desktop 6.6395.0 | The bundle places `claude_desktop_config.json` under `CLAUDE_USER_DATA_DIR` when that variable is set. A bounded direct launch used a new profile and a process restriction that allowed only local Unix socket binds while denying TCP. The internal Electron sandbox failed to initialize. No MCP probe messages appeared. The test process and temporary files were removed, and existing Claude process IDs were unchanged. |
| Codex graphical host (`ChatGPT.app`, `com.openai.codex`) | The host created an isolated profile using `CODEX_ELECTRON_USER_DATA_PATH` and a separate `CODEX_HOME`. It reached the app-server handshake with bundled CLI `0.169.0-alpha.11.1`. Under the offline process sandbox, the renderer failed to initialize its nested Electron sandbox and the host exited before the stdio probe received any MCP messages. |

The disposable test helper was run in both interactive-approval and pending-only modes. Codex recognized the generated configuration in its terminal settings reader. Direct checks discovered all 31 tools through the generated HTTP and stdio connections. An unanswered approval and a pending-only request each preserved the fixture's original revision. Enter and Ctrl-C removed the respective stacks, database volumes, networks, and private fixture directories. The live stack retained its four original containers. [Graphical test guide](graphical-test-guide.md)

Graphical approval verification is deferred to the project owner by request. Both graphical approval flows remain unverified. The terminal runs and the desktop stdio bridge have their own evidence. [Graphical test guide](graphical-test-guide.md) · [Client verification matrix](../../review-report.md#client-and-release-gate-matrix)
