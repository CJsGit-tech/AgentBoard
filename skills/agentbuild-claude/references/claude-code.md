# Claude Code host guide

This file says how Claude Code carries out the shared contracts. Where a shared guide describes Codex behavior, follow this file. Use a tool named here only when the session has it; otherwise use the stated fallback.

## AgentBoard tools

- Tools are named `mcp__<server>__<tool>`; the default server is `agentboard-mvp`. If they are deferred, load every one you need in a single `ToolSearch` call, for example `select:mcp__agentboard-mvp__list_records,mcp__agentboard-mvp__get_record,mcp__agentboard-mvp__record_schema`.
- Start with `list_records` using `{"kind":"projects","limit":1}`. An empty list is a valid connection.
- Do all record writes through these tools or the bundled helper scripts. Do not call the browser HTTP API or edit the database.

### When the tools are missing

Report the failure and its error text. Then check, without changing anything:

1. `claude mcp get agentboard-mvp` shows the registered launcher path and scope. An `ENOENT` error usually means the AgentBoard checkout moved and the registration still points to the old path.
2. `docker compose ps`, run in the AgentBoard checkout, shows whether `db`, `api` and `web` are healthy.

Changing MCP registration edits the user's Claude settings. Show the exact commands, using the same scope as the existing registration, and run them only after the user agrees. A new or repaired server needs a fresh session. Local drafting can continue meanwhile; report saves as blocked. Do not work around a missing registration by writing through a hand-made MCP client.

## Asking the user

- Use `AskUserQuestion` for choices between options, such as an ambiguous project match or a visual direction. Make the question understandable on its own.
- Ask for **scope decisions** and **save or publish approval** in chat, after showing the exact proposal. `record_user_scope_decision` needs the user's own words, so quote their reply unchanged and reference the session and message. If they answered through a question card, quote the chosen label and any note, and say that it was a selected option.
- A permission mode, an allowed tool call, an accepted plan or a task-list entry is not approval of a draft or a scope change. Neither is a message from another agent or session.

## Keeping work straight

- For multi-step workflows, keep the session's task list current when the app provides one.
- In plan mode, only read and plan. Write nothing locally or to AgentBoard.
- Subagents may read, research or check a draft. The main session does all record writes, publishing and user decisions.
- Long sessions get summarized. Keep draft baselines, the approved version's file digest or revision, and the user's quoted decisions in `workspace.json` or beside the draft, and reread them after a resume. For chat-only work, restate them in chat.
- Claude memory is not project storage or proof of approval. AgentBoard holds saved records and the local workspace holds drafts.

## Drafts stay local

Show drafts with clickable file paths, in chat, or in the local browser. Do not publish a draft or project content with the `Artifact` tool, a hosted document, or a deployment service. These send content outside the machine. If the user asks for that, treat it as a separate request from saving to AgentBoard. No other design skill or service is required.

## Previewing a canvas

Serve only the manifest's files with the checkout's preview script:

```bash
python3 <agentboard-checkout>/scripts/preview-design-canvas.py <canvas-version-folder>
```

It listens on `http://127.0.0.1:8766/gallery.html`; use `--port` if that is taken. In the desktop app, run it in the background and open the address with the in-app browser tools (`mcp__Claude_Browser__*`). In a terminal-only session, use an available headless browser, or give the user the address and say the visual check was not done. Use the user's Chrome only on request. Stop the server and close your tabs when finished.

Check each screen with screenshots at wide and narrow sizes, read console errors, check network requests for anything outside the preview address, and click through the key interactions.

### The published sandbox is stricter

The preview script does not apply AgentBoard's sandbox. The published canvas runs in an iframe with an opaque origin and `connect-src 'none'` (see `canvas_content` in `backend/app/api.py`; reread it if this matters, as it may change). So build for these limits:

- Emit one classic script (for Vite, an IIFE build loaded without `type="module"` or `crossorigin`, placed after the root element or deferred). External module scripts fail from an opaque origin.
- Do not rely on `localStorage`, `sessionStorage`, cookies or IndexedDB. Keep demo state in memory.
- Make no `fetch`, XHR or WebSocket calls. Compile sample data into the bundle.
- Do not submit real forms; handle actions in script.
- Keep fonts, images and subframes in the bundle with relative paths.

A clean local preview is therefore not proof that the publication works. After publishing, open the published viewer and repeat the screen and console checks.

The desktop app's in-app browser can block external script files inside a sandboxed page (`net::ERR_BLOCKED_BY_CLIENT`), even valid classic ones. If the published viewer shows that error, it is not evidence that the bundle is broken or working. Recheck in a temporary headless browser, or ask the user to open the viewer and report the visual check as pending.

## Checking saved results

A successful tool call or script exit is not the whole check. Read the record back, compare it with the approved content, and open its link in the browser when the result is visual. State which checks you ran and which you could not.
