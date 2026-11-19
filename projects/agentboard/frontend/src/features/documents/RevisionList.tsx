import { Doc } from "../../api/types";
import { formatTime } from "../../api/mockAdapter";
export function RevisionList({
  document: d,
  selected,
  onSelect,
  onExpired,
}: {
  document: Doc;
  selected: string;
  onSelect: (id: string) => void;
  onExpired: () => void;
}) {
  return (
    <aside className="revision-list">
      <small>RETAINED VERSIONS</small>
      <ol>
        {d.revisions.map((r, i) => (
          <li key={r.id}>
            <button
              className={r.id === selected ? "chosen" : ""}
              onClick={() => onSelect(r.id)}
            >
              <strong>
                Version {r.number}
                {i === 0 && <span>Current</span>}
              </strong>
              <small>{formatTime(r.updated)}</small>
              <small>{r.author}</small>
            </button>
          </li>
        ))}
      </ol>
      <p>
        Current + up to three previous versions. Older versions are unavailable.
      </p>
      <button onClick={onExpired}>Inspect expired version</button>
    </aside>
  );
}
