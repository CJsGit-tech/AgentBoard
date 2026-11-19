import { Doc } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { FileText, ArrowUpRight } from "lucide-react";
import { formatTime } from "../../api/mockAdapter";
export function DocumentList({ documents }: { documents: Doc[] }) {
  const { navigate } = useWorkspace();
  return (
    <div
      className="table-wrap"
      tabIndex={0}
      role="region"
      aria-label="Documents table scroll region"
    >
      <table>
        <caption className="sr-only">Project documents</caption>
        <thead>
          <tr>
            <th scope="col">Document</th>
            <th scope="col">Current version</th>
            <th scope="col">Updated by</th>
            <th scope="col">Updated</th>
            <th scope="col">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {documents.map((d) => (
            <tr key={d.id}>
              <th scope="row">
                <a
                  href={"#/documents/" + d.id}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate("/documents/" + d.id);
                  }}
                >
                  <FileText size={17} />
                  {d.title}
                </a>
                <small>Version {d.revisions[0].number} · Updated {formatTime(d.revisions[0].updated)}</small>
                {d.description && <small>{d.description}</small>}
                {(d.kind || d.featureTags?.length || d.concernTags?.length) && <small>{[d.kind, ...(d.featureTags || []), ...(d.concernTags || [])].filter(Boolean).join(" · ")}</small>}
                {d.sourceFilename && <small>Uploaded from {d.sourceFilename} · {formatTime(d.uploadedAt || d.revisions[0].updated)}</small>}
              </th>
              <td>Version {d.revisions[0].number}</td>
              <td>{d.revisions[0].author}</td>
              <td>{formatTime(d.revisions[0].updated)}</td>
              <td>
                <button
                  aria-label={"Open " + d.title}
                  className="iconbutton"
                  onClick={() => navigate("/documents/" + d.id)}
                >
                  <ArrowUpRight size={17} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
