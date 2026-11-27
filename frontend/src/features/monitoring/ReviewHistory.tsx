import { useEffect, useState } from "react";
import { errorText, request, stamp, type ChangeReview, type ReviewDocument } from "../../model";
import { Markdown } from "../documents/Markdown";

function useReviewRead<T>(path: string) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{path: string; data?: T; error?: string}>();
  useEffect(() => {
    let current = true;
    if (path) {
      setResult(undefined);
      request<T>(path).then(data => {
        if (current) setResult({path, data});
      }).catch(e => {
        if (current) setResult({path, error: errorText(e)});
      });
    }
    return () => { current = false; };
  }, [path, attempt]);
  return { result: result?.path === path ? result : undefined, retry: () => setAttempt(v => v + 1) };
}

function SnapshotRecord({record}: {record: ReviewDocument}) {
  const content = record.fields?.content ?? record.fields?.description;
  return <details><summary>{record.name} · Revision {record.revision}</summary>
    {typeof content === "string" && <Markdown text={content} />}
    <details><summary>All recorded fields</summary><pre style={{whiteSpace:"pre-wrap", overflowWrap:"anywhere"}}>{JSON.stringify(record.fields, null, 2)}</pre></details>
  </details>;
}

export function ReviewSnapshot({ project, id, label }: { project: string; id: string; label: string }) {
  const [open, setOpen] = useState(false);
  const {result, retry} = useReviewRead<ChangeReview>(open ? 'projects/' + encodeURIComponent(project) + '/reviews/' + encodeURIComponent(id) : '');
  const review = result?.data;
  return <details onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>{label}</summary>
    {open && (!result ? <p role="status">Loading review…</p> : result.error ? <p role="alert">{result.error} <button onClick={retry}>Retry</button></p> : review && <>
      <p>{review.request}</p>
      {review.rationale && <p>{review.rationale}</p>}
      {review.confirmation_note && <p>{review.confirmation_note}</p>}
      <SnapshotRecord record={review.snapshot.subject} />
      {review.snapshot.documents.map(doc => <div key={doc.id}>
        <a className="link" href={'#documents/' + encodeURIComponent(doc.id)}>Open current {doc.name}</a>
        <SnapshotRecord record={doc} />
        {review.findings.filter(f => f.document_id === doc.id).map(f => <p key={f.document_id}>{f.outcome} · {f.reason}</p>)}
      </div>)}
    </>)}
  </details>;
}

type ReviewList = {items: Pick<ChangeReview,"id"|"revision"|"status"|"created_at"|"superseded">[]; next_offset: number | null};
export function ReviewHistory({project, subject}: {project: string; subject: string}) {
  const [open, setOpen] = useState(false);
  const [offset, setOffset] = useState(0);
  const {result, retry} = useReviewRead<ReviewList>(open ? 'projects/' + encodeURIComponent(project) + '/reviews?subject=' + encodeURIComponent(subject) + '&limit=20&offset=' + offset : '');
  const page = result?.data;
  return <details onToggle={e => setOpen(e.currentTarget.open)}>
    <summary>Scope and document reviews</summary>
    {open && (!result ? <p role="status">Loading reviews…</p> : result.error ? <p role="alert">{result.error} <button onClick={retry}>Retry</button></p> : page && <>
      {!page.items.length && <p>No reviews recorded.</p>}
      {page.items.map(r => <ReviewSnapshot key={r.id + ':' + r.revision} project={project} id={r.id}
        label={stamp(r.created_at) + ' · ' + r.status + (r.superseded ? ' · Superseded' : ' · Current')} />)}
      {offset > 0 && <button onClick={() => setOffset(Math.max(0,offset - 20))}>Newer reviews</button>}
      {page.next_offset !== null && <button onClick={() => setOffset(page.next_offset!)}>Older reviews</button>}
    </>)}
  </details>;
}
