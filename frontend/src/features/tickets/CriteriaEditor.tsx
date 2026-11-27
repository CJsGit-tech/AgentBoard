import { Button, Checkbox, NativeSelect, Stack, Textarea } from "@mantine/core";
import type { DesignReference, ProofReference, Row, TicketCriterion } from "../../model";
import { splitReaderText } from "../documents/Markdown";
import "./ticket-reader.css";

export function CriteriaEditor({ documents, outputIds, value, onChange }: {
  documents: Row[]; outputIds: string[]; value: TicketCriterion[]; onChange: (value: TicketCriterion[]) => void;
}) {
  const designs = new Map<string, { reference: DesignReference; label: string }>();
  const proofs = new Map<string, { reference: ProofReference; label: string }>();
  for (const doc of documents) {
    for (const version of doc.canvas_versions || []) {
      designs.set(`${doc.id}:${version.version}`, { reference: { document_id: doc.id, version: version.version }, label: `${doc.name} · Canvas v${version.version}` });
    }
    if (!outputIds.includes(doc.id)) continue;
    proofs.set(doc.id, { reference: { kind: "report", document_id: doc.id, revision: doc.revision, status: "unverified" }, label: `${doc.name} · whole document` });
    for (const block of splitReaderText(doc.content || "")) if (block.type === "heading") {
      proofs.set(`${doc.id}:section:${block.line}`, { reference: { kind: "report", document_id: doc.id, revision: doc.revision, section_line: block.line, status: "unverified" }, label: `${doc.name} · ${block.value}` });
    }
    for (const preview of doc.previews || []) {
      proofs.set(`${doc.id}:preview:${preview.filename}`, { reference: { kind: "screenshot", document_id: doc.id, filename: preview.filename, digest: preview.digest, status: "unverified" }, label: `${doc.name} · ${preview.filename}` });
    }
  }
  const update = (id: string, changes: Partial<TicketCriterion>) => onChange(value.map(criterion => criterion.id === id ? { ...criterion, ...changes } : criterion));

  return <details className="criteria-editor">
    <summary>Acceptance criteria and evidence ({value.length})</summary>
    <p>Link an approved design and exact proof. Choose Output documents above before adding evidence.</p>
    {value.map((criterion, index) => {
      const evidence = criterion.evidence || [];
      const designKey = criterion.design ? `${criterion.design.document_id}:${criterion.design.version}` : "";
      return <fieldset key={criterion.id}>
        <legend>Criterion {index + 1}</legend>
        <Stack gap="xs">
          <Textarea label="Criterion" required value={criterion.text} onChange={event => update(criterion.id, { text: event.currentTarget.value })} />
          <Checkbox label="Require verified evidence to complete" checked={criterion.evidence_required} onChange={event => update(criterion.id, { evidence_required: event.currentTarget.checked })} />
          <NativeSelect label="Approved Canvas version" value={designKey} onChange={event => update(criterion.id, { design: designs.get(event.currentTarget.value)?.reference ?? null })}
            data={[{ value: "", label: "No reference" }, ...Array.from(designs, ([key, design]) => ({ value: key, label: design.label })), ...(designKey && !designs.has(designKey) ? [{ value: designKey, label: "Recorded version unavailable" }] : [])]} />
          {evidence.map((proof, proofIndex) => <div key={`${proof.document_id}:${proofIndex}`}>
            <small>{proof.kind === "screenshot" ? proof.filename : `${documents.find(doc => doc.id === proof.document_id)?.name || "Recorded report"} · revision ${proof.revision}${proof.section_line == null ? "" : ` · section line ${proof.section_line + 1}`}`}</small>
            <NativeSelect label="Proof status" value={proof.status} data={[
              { value: "unverified", label: "Unverified" }, { value: "verified", label: "Verified" }, { value: "superseded", label: "Superseded" },
            ]} onChange={event => {
              const status = event.currentTarget.value as ProofReference["status"];
              update(criterion.id, { evidence: evidence.map((item, i) => i === proofIndex ? { ...item, status } : item) });
            }} />
          </div>)}
          {proofs.size > 0 && <NativeSelect label="Add evidence from Outputs" value="" data={[
            { value: "", label: "Choose a report section or capture" }, ...Array.from(proofs, ([key, proof]) => ({ value: key, label: proof.label })),
          ]} onChange={event => {
            const added = proofs.get(event.currentTarget.value)?.reference;
            if (added && !evidence.some(item => {
              const { status: _status, ...target } = item;
              const { status: _addedStatus, ...addedTarget } = added;
              return JSON.stringify(target) === JSON.stringify(addedTarget);
            })) update(criterion.id, { evidence: [...evidence, added] });
          }} />}
          <Button type="button" variant="subtle" onClick={() => onChange(value.filter(item => item.id !== criterion.id))}>Remove criterion</Button>
        </Stack>
      </fieldset>;
    })}
    <Button type="button" variant="default" onClick={() => onChange([...value, { id: crypto.randomUUID(), text: "", evidence_required: false }])}>Add criterion</Button>
  </details>;
}
