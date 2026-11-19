# Verify approvals in the graphical clients

From the folder containing AgentBoard's `compose.yaml`, run the disposable fixture with Docker running and the backend image built.

```sh
python3 infra/desktop-verification.py
```

Keep that terminal open. The helper prints the localhost endpoint and paths to temporary MCP settings. Use those settings in a signed-in test profile of each graphical client. Use the existing [client setup guide](../../../README.md#agentbuild) to find the configuration. Keep the generated Codex token in the test profile.

| Check | Observe and record |
| --- | --- |
| Connect and create | Discover AgentBoard's 31 tools. Create a synthetic project, document and ticket. Repeat a Create call with the same operation key and payload and confirm that it returns the same ID. |
| Read, log and reconnect | Read the document and a document revision. Append and list a synthetic activity event. Restart the graphical client, reconnect and read the same records. |
| Accept | Request a ticket edit. Verify the target and proposed change in the AgentBoard form, then accept. Read the ticket and confirm the proposed change and one revision increase. |
| Decline | Request a different edit. Decline it, then read the ticket and confirm its last saved revision and values. |
| Stale approval | Leave an edit approval open on a known revision. Use another connected, verified client to apply a different edit to the same ticket. Accept the older approval and confirm the tool returns `stale_revision`. Read the ticket and check that the newer values are preserved. |

Repeat in both Codex desktop and Claude Desktop. Record each client version, each result, and any case the client could not perform. Use synthetic text throughout and omit credentials from screenshots or transcripts.

Keep the fixture terminal open through the checks. When finished, remove its MCP settings from the test profiles and press Enter in the fixture terminal. This stops the instance and deletes its disposable database and credentials.

For the pending-only case, repeat setup with `python3 infra/desktop-verification.py --pending-only`. Load the newly generated settings and request an update in each client. Observe `approval_required` with a request ID and confirm that the target keeps its original revision and values. Stop and remove this fixture in the same way.
