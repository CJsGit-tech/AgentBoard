import { useEffect, useState } from "react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { DocumentContent } from "./DocumentContent";
import { DocumentOutline } from "./DocumentOutline";
import { DocumentEditor } from "./DocumentEditor";
import { formatTime } from "../../api/mockAdapter";
export function DocumentDetailScreen({ route }: { route: string }) {
  const { db, projectId, navigate, dirty, setDirty } = useWorkspace();
  const id = route.split("?")[0].split("/")[2];
  const from = new URLSearchParams(route.split("?")[1]).get("from");
  const [editing, setEditing] = useState(false);
  useEffect(() => setEditing(false), [id]);
  const doc = db.documents.find(
    (d) => d.id === id && d.projectId === projectId,
  );
  if (!doc)
    return (
      <section className="state-panel">
        <h2>Document unavailable</h2>
        <p>This document is missing or belongs to another project.</p>
        <button onClick={() => navigate("/documents")}>
          Back to documents
        </button>
      </section>
    );
  return (
    <>
      <button
        className="backlink text-button"
        onClick={() => navigate(from ? "/tickets/" + from : "/documents")}
      >
        ← {from ? "Back to ticket" : "All documents"}
      </button>
      <PageHeader
        title={doc.title}
        description={"Current version " + doc.revisions[0].number + " · Updated " + formatTime(doc.revisions[0].updated)}
        actions={
          <>
            <button
              onClick={() =>
                navigate(
                  "/documents/" +
                    id +
                    "/history" +
                    (from ? "?from=" + from : ""),
                )
              }
            >
              Revision history
            </button>
            <button
              className={editing ? "" : "primary"}
              onClick={() => {
                if (
                  editing &&
                  dirty &&
                  !confirm("Discard unsaved document changes?")
                )
                  return;
                setDirty(false);
                setEditing(!editing);
              }}
            >
              {editing ? "Cancel editing" : "Edit document"}
            </button>
          </>
        }
      />
      {(doc.description || doc.kind || doc.featureTags?.length || doc.concernTags?.length || doc.sourceFilename) && <dl className="document-record-metadata">
        {doc.description && <><dt>Description</dt><dd>{doc.description}</dd></>}
        {doc.kind && <><dt>Kind</dt><dd>{doc.kind}</dd></>}
        {(doc.featureTags?.length || doc.concernTags?.length) && <><dt>Tags</dt><dd>{[...(doc.featureTags || []), ...(doc.concernTags || [])].join(", ")}</dd></>}
        {doc.sourceFilename && <><dt>Uploaded from</dt><dd>{doc.sourceFilename}</dd><dt>Uploaded</dt><dd>{formatTime(doc.uploadedAt || doc.revisions[0].updated)}</dd></>}
      </dl>}
      <StatePanel>
        {editing ? (
          <section className="panel document-edit-panel">
            <DocumentEditor
              key={doc.id}
              document={doc}
              onSaved={() => setEditing(false)}
            />
          </section>
        ) : (
          <div className="document-reading">
            <DocumentOutline revision={doc.revisions[0]} />
            <DocumentContent revision={doc.revisions[0]} />
          </div>
        )}
      </StatePanel>
    </>
  );
}
