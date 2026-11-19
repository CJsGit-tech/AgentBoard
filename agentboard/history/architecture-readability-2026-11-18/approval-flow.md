# Agent Approval Flow

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

Agent CR is permitted without per-operation approval after local connection authorization. An update is still an update if expressed as restore, link replacement, or status completion. Creating a new document is allowed; overwriting an existing document cannot be disguised as Create. Existing link removal requires approval; adding a genuinely new association is Create. Human actions in the local web UI are explicit user operations and do not need a second agent approval prompt.


No agent-callable approve tool, `approved=true` flag, or arbitrary SQL/shell tool. Reads and creates execute freely under an authenticated local client credential. Agent U/D tools first persist a pending request and return/emit its identity; when verified user elicitation is available, they present the target, exact change/deletion consequence, and base revision in the client UI. Accept applies that payload atomically; decline/cancel/expiry does not execute. Unsupported elicitation returns `approval_required` plus request ID and keeps the ticket badge pending for a later capable-client retry. A disconnected call is never evidence of approval.

Approval is tied to server-controlled request identity, authenticated client connection, target, payload hash, base revision, expiration and a single-use decision. An agent's textual claim of approval is not accepted. If native client confirmation is to be used instead of elicitation, it requires a separately verified integration that conveys a trustworthy user decision; showing a generic tool prompt alone is insufficient for the server to infer permission. The trusted client is still part of the security boundary; this cannot protect against a malicious client that fabricates human responses.

Concurrent record changes invalidate outstanding approvals. Commit uses the approved base revision and rejects stale requests; retries need a new user decision. Clearing a single request removes Needs approval only when no other pending request remains. Backend never holds a database transaction open while waiting for human input. Short bounded approval interactions can resolve inline; longer or unsupported interactions return request IDs and stay queryable.
