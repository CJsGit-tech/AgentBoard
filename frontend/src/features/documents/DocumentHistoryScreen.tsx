import { useEffect, useState } from "react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { RevisionList } from "./RevisionList";
import { RevisionComparison } from "./RevisionComparison";
import { RevisionRestore } from "./RevisionRestore";
import { UnavailableRevision } from "./UnavailableRevision";
export function DocumentHistoryScreen({ route }: { route: string }) {
  const { db, projectId, navigate } = useWorkspace();
  const id = route.split("?")[0].split("/")[2];
  const from = new URLSearchParams(route.split("?")[1]).get("from");
  const doc = db.documents.find(
    (d) => d.id === id && d.projectId === projectId,
  );
  const [selected, setSelected] = useState(
    doc?.revisions[1]?.id || doc?.revisions[0]?.id || "",
  );
  const [compare, setCompare] = useState(doc?.revisions[0]?.id || "");
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    setSelected(doc?.revisions[1]?.id || doc?.revisions[0]?.id || "");
    setCompare(doc?.revisions[0]?.id || "");
    setExpired(false);
  }, [id]);
  if (!doc)
    return (
      <StatePanel
        empty
        title="Document unavailable"
        action={
          <button onClick={() => navigate("/documents")}>
            Back to documents
          </button>
        }
      >
        {null}
      </StatePanel>
    );
  const before = doc.revisions.find((r) => r.id === selected);
  const after = doc.revisions.find((r) => r.id === compare) || doc.revisions[0];
  return (
    <>
      <button
        className="backlink text-button"
        onClick={() =>
          navigate("/documents/" + id + (from ? "?from=" + from : ""))
        }
      >
        ← Read document
      </button>
      <PageHeader
        title="Revision history"
        description={doc.title + " · current + three previous versions"}
        actions={
          <button
            onClick={() => navigate(from ? "/tickets/" + from : "/documents")}
          >
            {from ? "Back to ticket" : "All documents"}
          </button>
        }
      />
      <StatePanel>
        <div className="history-layout">
          <RevisionList
            document={doc}
            selected={selected}
            onSelect={(id) => {
              setSelected(id);
              setExpired(false);
            }}
            onExpired={() => setExpired(true)}
          />
          <section>
            {expired || !before ? (
              <UnavailableRevision
                onBack={() => {
                  setExpired(false);
                  setSelected(doc.revisions[0].id);
                }}
              />
            ) : (
              <>
                <div className="comparison-toolbar">
                  <label htmlFor="documenthistoryscreen-1">
                    Compare version
                    <select
                      id="documenthistoryscreen-1"
                      aria-label="Selected revision"
                      value={selected}
                      onChange={(e) => setSelected(e.target.value)}
                    >
                      {doc.revisions.map((r) => (
                        <option key={r.id} value={r.id}>
                          Version {r.number}
                        </option>
                      ))}
                    </select>
                  </label>
                  <span>with</span>
                  <label htmlFor="documenthistoryscreen-2">
                    Revision
                    <select
                      id="documenthistoryscreen-2"
                      aria-label="Compare revision"
                      value={compare}
                      onChange={(e) => setCompare(e.target.value)}
                    >
                      {doc.revisions.map((r) => (
                        <option key={r.id} value={r.id}>
                          Version {r.number}
                          {r.id === doc.revisions[0].id ? " · current" : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <RevisionComparison before={before} after={after} />
                <RevisionRestore
                  key={selected}
                  document={doc}
                  revision={before}
                  onRestored={() => {
                    setSelected(doc.revisions[0].id);
                    setCompare("");
                  }}
                />
              </>
            )}
          </section>
        </div>
      </StatePanel>
    </>
  );
}
