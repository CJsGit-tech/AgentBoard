import { useState } from "react";
import { Ticket } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { FileText, X } from "lucide-react";
export function TicketDocumentLinks({ ticket }: { ticket: Ticket }) {
  const { db, linkDocument, unlinkDocument, navigate } = useWorkspace();
  const [docId, setDocId] = useState("");
  const [relation, setRelation] = useState<"Context" | "Output">("Context");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const docs = db.documents.filter((d) => d.projectId === ticket.projectId);
  const alreadyLinked = ticket.links.some(link => link.documentId === docId && link.relation === relation);
  return (
    <section className="inspector-section">
      <h3>Linked documents</h3>
      {ticket.links.map((l) => {
        const doc = docs.find((d) => d.id === l.documentId);
        return (
          <div className="document-link" key={l.documentId + l.relation}>
            <a
              href={"#/documents/" + l.documentId + "?from=" + ticket.id}
              onClick={(e) => {
                e.preventDefault();
                navigate("/documents/" + l.documentId + "?from=" + ticket.id);
              }}
            >
              <FileText size={15} />
              <span>
                {doc?.title || "Document unavailable"}
                <small>
                  {l.relation} · version {doc?.revisions[0].number}
                </small>
              </span>
            </a>
            <button
              className="iconbutton"
              aria-label={"Unlink " + (doc?.title || "unavailable document") + " " + l.relation}
              disabled={pending}
              onClick={async () => { setPending(true); setError(""); try { await unlinkDocument(ticket,l.documentId,l.relation); } catch(cause) { setError(cause instanceof Error ? cause.message : "Could not unlink document."); } finally { setPending(false); } }}
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
      {!ticket.links.length && (
        <p className="muted small">No linked documents yet.</p>
      )}
      <div className="link-controls">
        <label htmlFor="ticketdocumentlinks-1">
          Document
          <select
            id="ticketdocumentlinks-1"
            aria-label="Link document"
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
          >
            <option value="">Choose document</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor="ticketdocumentlinks-2">
          Relationship
          <select
            id="ticketdocumentlinks-2"
            aria-label="Document relationship"
            value={relation}
            onChange={(e) => setRelation(e.target.value as typeof relation)}
          >
            <option>Context</option>
            <option>Output</option>
          </select>
        </label>
        <button
          type="button"
          disabled={!docId || pending || alreadyLinked}
          onClick={async () => {
            if (
              ticket.links.some(
                (l) => l.documentId === docId && l.relation === relation,
              )
            )
              return;
            setPending(true); setError(""); try { await linkDocument(ticket,docId,relation); } catch(cause) { setError(cause instanceof Error ? cause.message : "Could not link document."); } finally { setPending(false); }
          }}
          aria-busy={pending}
        >
          {pending ? "Saving…" : alreadyLinked ? "Already linked" : "Link"}
        </button>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
    </section>
  );
}
