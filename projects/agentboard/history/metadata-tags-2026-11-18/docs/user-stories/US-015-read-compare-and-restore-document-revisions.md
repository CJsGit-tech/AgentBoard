> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-015 — Read, compare, and restore document revisions

- **Story:**
  - As a solo builder, I want myself and connected agents to inspect document history so that we can rework content using recent revisions.
- **Acceptance Criteria:**
  - Given a document, when I or an authenticated agent requests its history, then the current version and up to three previous versions are readable with version identifiers and update timestamps.
  - Given two retained revisions, when I compare them, then their content differences are available for review.
  - Given a retained revision selected for restore, when a builder saves it or an agent obtains client approval to restore it, then its content becomes a new current version using the same three-previous-version limit.
  - Given a version removed by the retention limit, when I or an agent requests it, then an unavailable-version response is returned without substituting another revision.
  - Given a failed or unapproved document update, when I inspect its history, then no new content version has been added.
- **Associated Features:**
  - Document management
