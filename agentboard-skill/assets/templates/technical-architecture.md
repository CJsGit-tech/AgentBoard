# Technical Architecture authoring entry point

For new documents, do not create a combined architecture file from this template.

1. Read references/architecture-document-profiles.md and architecture-discovery.md.
2. Select web, iOS or both and discuss optional-topic triggers.
3. Confirm the document plan and discovery brief.
4. Run scripts/architecture_documents.py scaffold using the confirmed plan.
5. Fill each generated content contract, replace the SVG skeleton, map story criteria, and review the result.
6. Run architecture_documents.py validate and validate_project.py.

The authoritative topic/heading/prompt catalog is assets/architecture-documents.json.
Legacy combined/folder projects remain supported until an authorized revision.
