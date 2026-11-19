import { Revision } from "../../api/types";
import { formatTime } from "../../api/mockAdapter";
import { getMarkdownHeadings } from "./markdown";
export function DocumentOutline({ revision }: { revision: Revision }) {
  const headings = getMarkdownHeadings(revision.content);
  return (
    <nav className="document-outline" aria-label="Document outline">
      <small>ON THIS PAGE</small>
      {headings.length ? headings.map((heading) => (
        <button
          className="text-button"
          key={heading.id}
          aria-label={`Go to ${heading.text}`}
          onClick={() =>
            document
              .getElementById(heading.id)
              ?.scrollIntoView({ behavior: "auto" })
          }
        >
          {heading.text}
        </button>
      )) : <small>No headings</small>}
      <hr />
      <small>Current revision</small>
      <strong>Version {revision.number}</strong>
      <small>{formatTime(revision.updated)}</small>
      <small>{revision.author}</small>
    </nav>
  );
}
