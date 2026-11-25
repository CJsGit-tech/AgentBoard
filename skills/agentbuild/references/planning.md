# Plan in AgentBoard

## Project structure

**Setup** reuses a uniquely matched project or creates it when the supplied name has no match. The Setup command authorizes project creation and initialization of missing default roles. Ask for the project name if no project was identified or the supplied ID cannot be found. If a name matches multiple projects, link the candidates and use a checkout path or other distinguishing detail to help the user choose. If the user provides a local checkout, verify it and save it on the project as `checkout_path`. Reuse an existing mapping. Initialize the six default roles where missing and preserve customized role instructions. Check the [core documents](#core-documents) and link the matches or mark them Missing or Needs selection. Read back newly saved project and role records. Document creation and revision belong to Create Documents.

Resolve and prepare the [local planning workspace](local-workspace.md). Reuse the verified checkout or local project folder supplied by the user. Create missing draft, visual, and evidence directories and report their absolute paths. Setup authorizes these local steps without an extra confirmation. If no local folder can be identified, ask for one while continuing independent project checks. Do not infer the folder from the AgentBoard server checkout, create placeholder documents, or require a Docker mount for host-side planning.

| Default role | Starting instructions |
| --- | --- |
| Product Manager | Clarify the product, users and outcomes. Write concise vision and stories. Turn accepted scope into testable tickets. |
| Solution Architect | Inspect the code and constraints. Record architecture, interfaces, data and tradeoffs, with evidence and open decisions. |
| Product Designer | Use the approved user journeys and target devices. Specify screen states, interactions and accessibility requirements. |
| Frontend Programmer | Implement the authorized UI in the confirmed checkout and stack. Verify the full affected interface and user flows. |
| Backend Programmer | Implement the authorized API, data or service changes. Preserve compatibility and verify errors and data integrity. |
| Code Reviewer | Review the supplied artifact or change against its requirements. Report findings with evidence, severity and suggested fixes. |

## Core documents

Use these titles and AgentBoard types for the four core documents in each project.

| Title | Type | Inputs |
| --- | --- | --- |
| Product Brief | `product-vision` | Product concept, target users, pain points, and intended value. |
| Technical Stack | `architecture-topic` | Confirmed platforms, languages, frameworks, data stores, local setup and deployment. Cite relevant manifests, config, or README paths from the verified checkout. |
| User Experiences | `user-story` | User journeys, expected behavior, key decisions, and the states the experience must handle. |
| Design Profile | `design-topic` | Concrete screen designs, shared visual choices, narrative, local React/Mantine drafts, and the approved canvas publication. |

Use the same lookup in Setup and Create Documents. Match the type and title in the selected project, ignoring case. Accept Product Vision and Tech Stack as established titles for the same two documents. If multiple records match, link the candidates with distinguishing details and ask which one to use before writing. Reuse the chosen ID and title. Use a leading `State: Draft` line in new core records. Mark unknown decisions **Open** and add evidence for existing stack claims. Those decisions block only work that depends on them.

## Planning documents

**Create Documents** checks the project for the [core documents](#core-documents). Show which exist, which are missing, and which need the user to select a match. If the user gives only the project, guide them through the missing documents. Use any requested document names to limit the scope. “All” selects the four core documents. Revise existing content when the user requests a change. If all four exist and there are no requested changes, report their links.

For a feature, screen, or requirements change, follow [Change reviews](reviews.md) within this workflow. Read the request and impacted documents, then keep findings with the local/chat draft. Use `source_documents` for verified document dependencies when saving and managed tags for related features. Flag affected documents outside the selected writing scope; do not silently edit them. Submit formal findings once the approved storage writes are authorized. Scope agreement and approval to store a reviewed draft are separate decisions; reuse either when already given for the current version.

Work through the selected documents one at a time in this order. Use the [content formats](formats.md).

1. **Product Brief** — Use project evidence to propose the audience, problem, and intended value. Ask about the most important open decision first.
2. **Technical Stack** — Inspect the confirmed checkout. Use the README, manifests, and configuration to fill in the current stack. Discuss open platform or deployment decisions with the user.
3. **User Experiences** — Start with the Product Brief and existing requirements. Walk through one key journey at a time. Confirm what the user wants to do, how the journey starts, what the user and system do, and what happens when the journey succeeds or runs into a problem. Reuse decisions the user has already made in this workflow or recorded on the project.
4. **Design Profile** — Turn User Experiences and any UserScreens Feel/Flow/Show guidance into concrete screen designs and local visual drafts. If source records are missing, use confirmed journeys and local/chat drafts without creating placeholder records. Use the [direction review](#choose-a-visual-direction) when selecting or revisiting the visual direction. Prepare the [Design Profile content](formats.md#design-profile), then use the [local Visuals procedure](visuals.md#build-the-local-draft) for the narrative and React/Mantine screen drafts within this selected document. Flag unresolved product behavior as a User Experiences decision and show which screen or state depends on it.

When the user requests [UserScreens](formats.md#userscreens), prepare its Feel/Flow/Show screen descriptions before building the dependent Design Profile drafts. Use confirmed journeys from User Experiences and current conversation context. Design Profile implements those screen descriptions; do not require a saved Design Profile before preparing UserScreens. An optional, user-requested [design export](formats.md#design-export) follows the reviewed Design Profile.

For each document, share the starting point and use its own [question subset](#document-questions). Start with unresolved high-level context and decisions, then deepen the discussion with follow-ups based on the user's answers, examples, corrections, and earlier chat. Ask one focused question at a time and explain why it matters. The subsets are starting points, not a fixed questionnaire or a limit on useful follow-ups. Reuse known answers and inspect implementation facts directly; when the needed context is available, draft without an extra question.

Use the answers in the draft before presenting it for review. Prepare selected documents in the [local workspace](local-workspace.md) and show them in chat with file links, or work entirely in chat/IDE when requested. This preparation comes before application storage writes, including edits to existing documents and Design Profile attachments. Mark deferred decisions **Open**. Present the concrete document or design package, apply feedback locally, then save/upload the version the user approves. Reuse existing approval for that exact version without another confirmation; a workflow command alone does not publish unfinished documents or designs. Explain changes to agreed scope through the scope-confirmation flow. Verify saved records and complete their impact reviews. If the user skips a document, move on. Show proposed replacements of human-approved decisions before applying them.

For a preview that may be saved, persist the target ID and revision, or that the target is missing, in the local draft metadata described in [Local workspace](local-workspace.md#location-map-and-draft-baselines). Include any source record revisions the draft depends on. Before saving that preview, compare its baseline with the current records. If a revision changed or a previously missing target now exists, read the changes and refresh the draft and impact review. Ask only if the refreshed proposal changes the agreed scope or needs a missing decision. Use the verified baseline revision for the save and handle conflicts the same way. Update the intended record in place and report its link and verified revision.

User Experiences uses a standard User Story record. Repeat its exact-title lookup immediately before creating it so an existing record can be reused. Use source IDs and revisions when they matter to the document. Read project constraints before choosing devices, a stack, or a deployment target. If the user selects Tag Catalog, follow the [catalog and assignment rules](tags.md).

## Document questions

Use the relevant subset for every selected document. Adapt the wording to the project's context, skip answered questions, and extend the discussion when a reply reveals missing decisions, conflicting goals, exceptions, or new constraints. Carry answers into the draft as the conversation develops.

| Document | Starting question subset |
| --- | --- |
| Product Brief | Who is it for? What problem matters most? What outcome would help? What belongs in the first scope? How will success be recognized? |
| Technical Stack | Which platforms must it support? What existing systems or integrations constrain it? What data/security needs matter? Where will it run? What scale, cost, or maintenance tradeoffs need a decision? Verify existing technology from the checkout. |
| User Experiences | What goal starts each journey? Where does it begin? What should the user and system do? What counts as success? What happens with empty data, waiting, failures, recovery, or different permissions? |
| UserScreens | Feel: what should attract attention first, and how should contrast/grouping guide the eye? Flow: what is the next action, and which information or actions appear later? Show: what information is essential now, and how much detail can be deferred? Which devices and states must these choices support? |
| Design Profile | Which screens and states should be drafted first? Which visual direction fits the UserScreens intent? How should widgets, controls, charts, and shared styles look? How should layouts adapt? Which interactions must the local prototype demonstrate before approval? |
| Screen Inventory | Which screens, states, and devices need coverage? Which visuals already exist? What is missing? Which source journey or design does each visual represent? Is an HTML canvas or an explicitly requested still image needed? |
| Tag Catalog | What does each tag mean? Which records should it find? Do proposed tags overlap? Which stable IDs, labels, assignments, or retirement decisions need agreement? |
| Review Report | What artifact and version are being reviewed? Against which requirements or criteria? Which findings affect the user's decision? What remains unresolved? |
| Review Evidence | Which claim must be demonstrated? Which artifact or interaction proves it? What environment and version were checked? What does the evidence cover, and what remains unverified? |
| Other requested documents | Establish the document's purpose, reader, source material, decisions, and expected output, then form a subset specific to that purpose. For legacy design-canvas content, clarify ownership and intended use before applying the current Design Profile flow. |

## Choose a visual direction

1. Read the project description, Product Brief, User Experiences, and any existing Design Profile or UserScreens needed for the request. Identify the screens, audience, and task that the references should serve.
2. If the direction is unresolved, present two or three distinct, relevant options using the existing interface, user-provided examples, or accessible references. Inspect any referenced screenshots or previews and explain the specific layout, visual hierarchy, or styling decision each option would inform. No particular gallery or service is required.
3. Ask the user which direction to use and wait for their choice before applying it to the design documents or drafts. A recommendation helps the user compare the options. A direction the user has already chosen for the same scope can be reused unless they ask to revisit it.
4. Record the selected direction and the traits the user wants to adopt in the Design Profile. Use that direction when drafting UserScreens, creating visual drafts, or preparing a requested design export.
