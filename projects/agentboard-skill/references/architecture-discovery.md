# Technical architecture discovery and diagram direction

## Discovery before authoring

Technical-Documents is a conversation across rounds, followed by authoring. A product category or deployment answer alone does not establish enough context. Reuse actual prior answers, record what is confirmed, and ask focused batches of 2–4 related questions. Wait for answers before making dependent choices. Continue as many rounds as necessary; there is no one-question limit and no fixed maximum number of rounds.

### Round 1 — deployment, preferences, and external dependencies

- Where and how will the app run: local workstation, Docker Compose, LAN server, hosted platform, remote access? Which host OS/CPU and browser/client targets matter?
- Is it single-user or shared? What authentication, roles, and data isolation are required?
- Any targeted frontend, backend, database, SDK, language, or existing repository constraints?
- Which online third-party providers are required or forbidden: deployment, database, identity, AI models/agent runtimes, file storage, source control, monitoring, messaging, payments? “None” is a valid answer. Never request secrets in chat.

### Round 2 — options and functional boundaries

Use Round 1 answers to select relevant follow-ups rather than repeating a questionnaire. If stack choices are open, compare 2–3 viable options with concrete pros, cons, local/cloud fit, operational burden, and a recommendation. Verify changing capabilities in official documentation. Let the user choose or explicitly delegate the choice before committing to architecture. Do not silently promote the earlier draft stack into a decision.

Clarify agent execution versus role management; required integrations and permissions; real-time behavior; background work; task lifecycle; document input types and revision needs. Identify any changes to existing stories, and surface them for revision rather than silently changing product scope.

### Round 3 and later — data and operation details

Follow up on persistence, expected scale/concurrency, offline behavior, backup/restore, retention/deletion, privacy, secret handling, provider cost constraints, failure recovery, ports/network exposure, and maintenance. Tailor depth to the application and risk. A hosted database is not assumed for a Docker deployment; neither is a local database compulsory without discussion.

## Document Selection

Apply `architecture-document-profiles.md` and its catalog. Inspect stories for optional triggers, ask about unknowns, compare a standalone file with an inline section, and include the explicit core/platform/optional document list and rationale in the discovery brief. Confirm this list before running the skeleton script. On changed requirements, revisit the plan rather than silently adding/removing documents.

## Readiness checkpoint

Before writing architecture or the final diagram, summarize confirmed deployment, users/access, selected or explicitly delegated stack, provider choices (including none), execution/integration scope, data and reliability requirements, and unresolved tradeoffs. Ask the user to confirm/correct this concrete brief. Explain that this checkpoint prevents another premature architecture draft. Resume writing after confirmation or explicit delegation to proceed with specified assumptions. Do not re-ask facts already answered.

Existing architecture is provisional until reconciled with this discovery. Preserve it during questioning and archive it on an authorized revision. During discovery, show questions, comparisons, and the brief; do not generate the final artifacts early.

## Diagram reference and visual contract

Use `assets/references/system-architecture-modules.svg` as the user's visual reference. Its content is illustrative, not app requirements: Streamlit, MariaDB, JWT, WebSocket, version numbers, roles, ports, modules, and Chinese labels are not automatically selected for a new product.

Match the visual grammar:

- Landscape, compact technical layout; browser/users above the system boundary.
- Dashed network/deployment boundary with clearly named container or service groups inside.
- Frontend functional modules arranged in a horizontal row, aligned with corresponding backend modules where applicable.
- Backend entry points and actual shared concerns above module columns; persistence access and database/storage below.
- Pale blue frontend blocks, pale amber backend blocks, green data/storage blocks, gray external/configuration blocks; restrained typography, thin strokes, consistent spacing, rounded boxes.
- Number matching frontend/backend modules for easy tracing. Label responsibilities inside modules, rather than drawing only generic UI/API/database boxes.
- Orthogonal directional connectors with protocol/port labels; distinguish runtime calls from startup/configuration flows using solid/dashed arrows and a legend.
- Show providers outside the deployment boundary, internal-only versus published ports, configuration sources, and persistent volumes when relevant. Do not invent services simply to fill the reference layout. A combined container may contain separately labeled logical modules.
- Use the project's agreed language, accessible SVG title/description, and light/dark colors where feasible. Resize the canvas to content; avoid clipped text, overlapping arrows, tiny labels, and excessive empty space.

The diagram must reflect the agreed architecture, not copy the reference's topology or technologies. Parse and render it, inspect at readable size, and compare every boundary and connection with the written document.
