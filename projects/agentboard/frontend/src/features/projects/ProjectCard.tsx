import { useState } from "react";
import { ArrowUpRight, Folder, Pencil, Trash2 } from "lucide-react";
import { Project } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { formatTime } from "../../api/mockAdapter";

export function ProjectCard({ project, onEdit }: { project: Project; onEdit: () => void }) {
  const { db, projectId, selectProject, mode, deleteProject } = useWorkspace();
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const tickets = db.tickets.filter((ticket) => ticket.projectId === project.id).length;
  const records = mode === "connected" && project.id !== projectId
    ? "Select project to view its records"
    : `${tickets} ${tickets === 1 ? "ticket" : "tickets"}`;

  return (
    <article className="projects-row" aria-label={`${project.name} project`}>
      <span className="projects-row-icon" aria-hidden="true"><Folder size={18} /></span>
      <div className="projects-row-main">
        <div className="projects-row-heading">
          <button className="projects-row-title" onClick={() => selectProject(project.id)}>
            {project.name}<ArrowUpRight size={14} aria-hidden="true" />
          </button>
          {project.id === projectId && <span className="projects-active-label">Current project</span>}
        </div>
        <p>{project.purpose || "No purpose added yet."}</p>
        {error && <p className="projects-row-error" role="alert">{error}</p>}
      </div>
      <div className="projects-row-meta">
        <span>{records}</span>
        <time dateTime={project.updated}>Updated {formatTime(project.updated)}</time>
      </div>
      <div className="projects-row-actions">
        <button aria-label={`Edit ${project.name}`} onClick={onEdit}><Pencil size={14} /> Edit</button>
        <button
          className="projects-delete"
          aria-label={`Delete ${project.name}`}
          disabled={deleting}
          onClick={async () => {
            const accepted = confirm(`Delete “${project.name}”? This permanently deletes the project and all associated records, including roles, tickets, documents, activity, and approvals. This cannot be undone.`);
            if (!accepted) return;
            setDeleting(true);
            setError("");
            try { await deleteProject(project); }
            catch (cause) { setError(cause instanceof Error ? cause.message : "Could not delete project. The project and its records are unchanged."); }
            finally { setDeleting(false); }
          }}
        ><Trash2 size={14} /> {deleting ? "Deleting…" : "Delete"}</button>
      </div>
    </article>
  );
}
