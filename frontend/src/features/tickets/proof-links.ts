import type { DesignReference, ProofReference, Row, Workspace } from "../../model";
import { splitReaderText } from "../documents/Markdown";

export const designHref = (ref: DesignReference) => `#canvas/${encodeURIComponent(ref.document_id)}/${ref.version}`;

export function proofHref(proof: ProofReference) {
  const query = proof.kind === "report"
    ? new URLSearchParams({ revision: String(proof.revision), ...(proof.section_line == null ? {} : { section: String(proof.section_line) }) })
    : new URLSearchParams({ preview: proof.filename, digest: proof.digest });
  return `#documents/${encodeURIComponent(proof.document_id)}?${query}`;
}

export function resolveProof(db: Workspace, ticket: Row, proof: ProofReference) {
  const doc = db.documents.find(row => row.id === proof.document_id && row.project === ticket.project);
  if (!doc || !ticket.output_documents?.includes(doc.id)) return null;
  if (proof.kind === "screenshot") return doc.previews?.some(preview => preview.filename === proof.filename && preview.digest === proof.digest) ? doc : null;
  if (doc.revision !== proof.revision) return null;
  if (proof.section_line != null) {
    const headingAvailable = doc.report_heading_lines?.includes(proof.section_line)
      ?? splitReaderText(doc.content || "").some(block => block.type === "heading" && block.line === proof.section_line);
    if (!headingAvailable) return null;
  }
  return doc;
}
