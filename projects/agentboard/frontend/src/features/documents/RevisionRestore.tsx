import { SaveFailureControl } from "../../components/SaveFailureControl";
import { useState } from "react";
import { Doc, Revision } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export function RevisionRestore({
  document: d,
  revision: r,
  onRestored,
}: {
  document: Doc;
  revision: Revision;
  onRestored: () => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const { restoreDocument, mode } = useWorkspace();
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  return (
    <section className="restore-panel">
      <div>
        <h3>
          {r.id === d.revisions[0].id
            ? "Current version selected"
            : "Rework from this revision"}
        </h3>
        <p>
          Restore creates a new current version and keeps only three previous
          versions. The oldest may be removed.
        </p>
      </div>
      {r.id !== d.revisions[0].id &&
        (confirming ? (
          <div className="restore-confirm">
            <strong>Restore version {r.number}?</strong>
            <p>{mode === "mock" ? "This changes sample data only." : "This creates a new current revision from the selected version."}</p>
            {error && <p className="form-error" role="alert">{error}</p>}
            <SaveFailureControl />
            <div>
              <button onClick={() => setConfirming(false)}>Cancel</button>
              <button
                className="primary"
                disabled={saving}
                onClick={async () => { setSaving(true); setError(""); try { await restoreDocument(d,r); setConfirming(false); onRestored(); } catch(cause) { setError(cause instanceof Error ? cause.message : "Could not restore this revision."); } finally { setSaving(false); } }}
              >
                {saving ? "Restoring…" : "Confirm restore"}
              </button>
            </div>
          </div>
        ) : (
          <button onClick={() => setConfirming(true)}>
            Restore version {r.number}
          </button>
        ))}
    </section>
  );
}
