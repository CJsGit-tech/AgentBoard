import { Revision } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { MarkdownDocument } from "./markdown";

export function DocumentContent({ revision }: { revision: Revision }) {
  const { mode } = useWorkspace();
  return (
    <article className="document-content">
      <div className="docmeta">
        <span>PROJECT DOCUMENT</span>
        <span>Version {revision.number} · {revision.author}</span>
      </div>
      <MarkdownDocument source={revision.content} />
      {mode === "mock" && <p className="document-footnote">Preview content · not the project's actual planning documents</p>}
    </article>
  );
}
