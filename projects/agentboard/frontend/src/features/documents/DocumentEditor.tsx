import { SaveFailureControl } from "../../components/SaveFailureControl";
import { useState } from "react";
import { Doc } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { documentKinds } from "../../api/restClient";
export function DocumentEditor({
  document,
  onSaved,
}: {
  document?: Doc;
  onSaved: (id: string) => void;
}) {
  const { projectId, saveDocument, setDirty, db, preview, mode } = useWorkspace();
  const [saving, setSaving] = useState(false);
  const [title, setTitle] = useState(document?.title || "");
  const [content, setContent] = useState(document?.revisions[0].content || "");
  const [description, setDescription] = useState(document?.description || "");
  const [kind, setKind] = useState(document?.kind || "document");
  const [featureTags, setFeatureTags] = useState(document?.featureTags?.join(", ") || "");
  const [concernTags, setConcernTags] = useState(document?.concernTags?.join(", ") || "");
  const [error, setError] = useState("");
  return (
    <form
      noValidate
      aria-label="document editor"
      className="document-editor"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!title.trim() || !content.trim()) {
          setError("Title and content are required.");
          e.currentTarget
            .querySelector<HTMLElement>(!title.trim() ? "input" : "textarea")
            ?.focus();
          return;
        }
        setSaving(true);
        const value = {title:title.trim(),content,description:description.trim(),kind,featureTags:splitTags(featureTags),concernTags:splitTags(concernTags)};
        try { onSaved(await saveDocument(value, document)); }
        catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save document. Your draft is retained."); }
        finally { setSaving(false); }
      }}
    >
      <label htmlFor="documenteditor-1">
        Document title <span aria-hidden="true">*</span>
        <input
          id="documenteditor-1"
          aria-label="Document title"

          required
          aria-invalid={!!error && !title.trim()}
          aria-describedby={error ? "documenteditor-error" : undefined}
          value={title}
          onChange={(e) => {
            setError("");
            setTitle(e.target.value);
            setDirty(true);
          }}
        />
      </label>
      <label htmlFor="documenteditor-2">
        Content <span aria-hidden="true">*</span>
        <textarea
          id="documenteditor-2"
          aria-label="Document content"
          rows={15}
          required
          aria-invalid={!!error && !content.trim()}
          aria-describedby={error ? "documenteditor-error" : undefined}
          value={content}
          onChange={(e) => {
            setError("");
            setContent(e.target.value);
            setDirty(true);
          }}
        />
      </label>
      <label htmlFor="documenteditor-description">Short description
        <input id="documenteditor-description" value={description} maxLength={240} onChange={e => { setDescription(e.target.value); setDirty(true); }} />
      </label>
      <label htmlFor="documenteditor-kind">Kind
        <select id="documenteditor-kind" value={kind} onChange={e => { setKind(e.target.value); setDirty(true); }}>
          {documentKinds.map(value => <option key={value}>{value}</option>)}
        </select>
      </label>
      <label htmlFor="documenteditor-feature-tags">Feature tags
        <input id="documenteditor-feature-tags" placeholder="feature:document-management, ..." value={featureTags} onChange={e => { setFeatureTags(e.target.value); setDirty(true); }} />
      </label>
      <label htmlFor="documenteditor-concern-tags">Concern tags
        <input id="documenteditor-concern-tags" placeholder="concern:reliability, ..." value={concernTags} onChange={e => { setConcernTags(e.target.value); setDirty(true); }} />
      </label>
      {preview === "Conflict" && (
        <div className="conflict-panel">
          <strong>Current saved content</strong>
          <pre>
            {db.documents.find((d) => d.id === document?.id)?.revisions[0]
              .content || "No saved document"}
          </pre>
          <p>
            Your draft remains in the editor. Resolve the preview conflict
            before retrying.
          </p>
        </div>
      )}
      {error && (
        <p id="documenteditor-error" role="alert" className="form-error">
          {error}
        </p>
      )}
      <SaveFailureControl />
      <div className="form-footer">
        <small>{mode === "mock" ? "Creates a new revision; retains current + three previous versions" : "Saves a new server revision"}</small>
        <button className="primary" disabled={saving}>Save document</button>
      </div>
    </form>
  );
}

function splitTags(input: string) {
  return [...new Set(input.split(",").map(tag => tag.trim()).filter(Boolean))];
}
