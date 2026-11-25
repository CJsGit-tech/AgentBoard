# Project tags

**Create Documents** owns the project Tag Catalog. Look up an `unclassified` document titled `Tag Catalog` in the selected project. Reuse its ID. If an older workspace has multiple matches, link the candidates and ask which one to use. On the first requested addition, prepare the catalog locally or in chat, then create it when the reviewed version is approved for saving. Use the [document question subset](planning.md#document-questions) for missing tag decisions.

Use a section per stable lowercase tag ID. Agents and the human record editor share this format.

```text
## saved-places
Label: Saved Places
Meaning: Bookmarking and searching saved items.
State: Active
```

Users can list tags, add IDs, revise labels and meanings, or change Active to Retired. Preview catalog changes locally or in chat before saving the approved version; reuse approval already given for that exact change. Keep retired IDs available for historical searches. The backend validates new assignments and rejects removal of catalog entries. Use the native `tags` array on documents and tickets. Set it only when the user specifies tags or the source records clearly establish relevant active IDs. For an explicit reassignment, send the complete intended array with the current revision.

To find related work, use `list_records(kind, project, tag)` separately for tickets and documents. Follow pagination and match stable IDs. For several tags, intersect or union matching IDs according to the requested scope. The UI offers a Tag filter and the record editor offers project-specific active tags. Legacy description assignments were imported by migration 004.
