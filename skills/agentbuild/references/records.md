# AgentBoard records

Use the live schema to validate every outgoing field. The names below match the current AgentBoard MVP. Send writable fields only. IDs and revisions returned by the server identify saved records. The examples use fictional IDs.

## Tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `record_schema` | `kind` | JSON Schema for writable fields |
| `list_records` | `kind`, optional `project`, `tag`, `deleted`, `limit`, `offset`, `document_type`, `work_type` | One page. Use the type filters only with their matching kind. |
| `get_record` | `kind`, `id`, optional `deleted` | Record and current revision |
| `create_record` | `kind`, `fields`, optional `editor_role_id` | Saved record with allocated ID |
| `update_record` | `kind`, `id`, `revision`, `changes`, optional `editor_role_id` | Saved record |

Use `publish_canvas(document_id, revision, files, change_note, sources)` on the project's Design Profile (`design-topic`). The destination uses its current record revision. `files` maps relative paths to base64, and each source is `{"document_id":"<verified-id>","revision":3}`. Read back `canvas_versions` to verify the saved version, digest, change note, source names and revisions, publisher, and publication time. Canvas publication numbers and Design Profile record revisions are separate values.

The Design Profile owns the canvas attachment. Canvas in the sidebar lists published profiles and opens each full canvas in a new tab. Use `/#canvas/<profile-id>/<version>` for a verified publication link on the same app origin. Legacy `design-canvas` records may exist in older workspaces. Resolve their ownership before publishing to avoid creating a second history.

Use `attach_visual` to store and version PNGs on a screen inventory. Document readbacks include a `previews` array with filenames and SHA-256 digests.

Record lists default to 50, accept up to 200 and use an offset. Page until a short page for complete lookup or counts. If records change while paging and it matters, refresh and confirm before acting.

## Review tools

- `list_change_reviews(project?, subject?, limit?, offset?)` returns current and superseded reviews with their immutable input snapshots. Page all results and use `superseded: false` for the current check.
- `start_change_review(kind, id, revision, request, operation="Edit")` records a request against a document or ticket. Use `operation: "Delete"` for document removal. Identical current requests return the same review.
- `assess_change_review(id, revision, assessment)` records the conclusion, rationale, and one finding for every snapshot document. Its schema defines the allowed values. Only the user can decide a scope change.

- `record_user_scope_decision(id, revision, accept, user_quote, conversation_reference)` records the user's explicit reply on the exact scope proposal. Never infer consent or make the decision.

Checks have their own revisions. Content fingerprints determine freshness; metadata-only changes do not reopen checks. `source_documents` is a unique same-project dependency list on documents; cycles are rejected. Run `mode` is `Edit` (requires a reviewed linked ticket) or `Read only`. See [Change reviews](reviews.md) for gates and user confirmation, and `/#activity` for the existing activity log. There is no separate Reviews workspace. A saved draft is not proof of user approval.

## Record types and links

| Kind / ID prefix | Main data | Relationships |
| --- | --- | --- |
| `projects` / `P-` | `name`, optional `description`, `checkout_path` | Parent workspace record |
| `milestones` / `M-` | `name`, optional `description` | Required `project` ID |
| `roles` / `R-` | `name`, optional `description`, `instructions` | Required `project` ID |
| `documents` / `D-` | `name`, `content`, optional `document_type` and `description` | Required `project` ID |
| `tickets` / `AB-` | `name`, optional `description`, `status`, `due`, `work_type`, `execution_role` | Required `project` and `milestone`. Optional `role` ID and `documents` (Context). |

A project's children link only within that project. A record's owning project is fixed after creation. Ticket Context uses unique live document IDs. Use `role` for assignment. Use `editor_role_id` as a tool argument on ticket/document edits to attribute the current edit to a verified role when applicable. Use `execution_role` (`FE`, `BE`, or empty) for work routing.

Ticket statuses are `Planned`, `In progress`, `Blocked`, `Done`. Work types are `BUILD`, `BUG`, `UNCLASSIFIED`. `due` is a calendar date (`YYYY-MM-DD`) or empty. Derive relative dates from the user's local calendar.

The app writes audit events automatically. Use revision checks when editing. Updates with no field change can return the existing revision. On a stale revision, compare the latest fields against the approved change. After a timeout, read back before retrying. The server assigns a fresh ID on each create and checks recognized core document and Tag Catalog titles within a project. Other creates require a lookup before retrying. Each write is a separate transaction.

## Document types and browser navigation

The Documents library groups the Product Brief and User Experiences under Product, Technical Stack under Architecture, and Design Profile and Screen Inventory under Design. The Design Profile holds canvas publications, also listed in the Canvas sidebar. The Tag Catalog uses the Unclassified type.

Use the verified app base URL for navigation, for example `http://127.0.0.1:8080/#documents`, `/#tickets`, `/#milestones`, or `/#roles` on the same base. Include the project and record title beside section links. For every saved output, link the record title using its `record_url` from the local launcher or resolve `record_path` against the verified app base, for example http://127.0.0.1:8080/#documents/D-123456789abc. In document content, use plain references such as `Design Profile — D-123456789abc (rev 2)` when a source matters. The native Context relationship is visible from the ticket and document.

Use [Formats](formats.md) for record contents and repository paths. Use the [Tag Catalog](tags.md) and the native tags array for managed tags. Use the live schema to determine which other metadata fields can be written. If the user explicitly wants an estimate or decision recorded, label it in the relevant description or content and report how it was stored.
