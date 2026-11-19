import { ArrowUpRight, Folder } from "lucide-react";
import { Project } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { formatTime } from "../../api/mockAdapter";
export function ProjectCard({
  project,
  onEdit,
}: {
  project: Project;
  onEdit: () => void;
}) {
  const { db, selectProject } = useWorkspace();
  return (
    <article className="project-card">
      <div className="project-card-icon">
        <Folder size={22} />
      </div>
      <button
        className="project-title"
        onClick={() => selectProject(project.id)}
      >
        {project.name}
        <ArrowUpRight size={16} />
      </button>
      <p>{project.purpose || "No purpose added yet."}</p>
      <small className="mono">{project.id}</small>
      <div className="project-card-footer">
        <span>
          {db.tickets.filter((t) => t.projectId === project.id).length} tickets
          · Updated {formatTime(project.updated)}
        </span>
        <button onClick={onEdit}>Edit</button>
      </div>
    </article>
  );
}
