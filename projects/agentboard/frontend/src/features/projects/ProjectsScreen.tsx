import { useState } from "react";
import { Plus } from "lucide-react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { Project } from "../../api/types";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { Modal } from "../../components/Modal";
import { ProjectForm } from "./ProjectForm";
import { ProjectCard } from "./ProjectCard";
import "./projects.css";
export function ProjectsScreen() {
  const { db, selectProject, dirty, setDirty } = useWorkspace();
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Project | null | undefined>();
  const close = () => {
    if (dirty && !confirm("Discard unsaved project changes?")) return;
    setDirty(false);
    setEditing(undefined);
  };
  const projects = db.projects.filter((p) =>
    (p.name + " " + p.purpose)
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        title="Projects"
        description="Your products, work and decisions in one place."
        actions={
          <button
            className="primary"
            onClick={() => {
              setEditing(null);
            }}
          >
            <Plus size={16} />
            New project
          </button>
        }
      />
      <div className="toolbar">
        <label htmlFor="projectsscreen-1">
          Find project
          <input
            id="projectsscreen-1"
            placeholder="Name or purpose"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <span>{projects.length} projects</span>
      </div>
      <StatePanel
        empty={!projects.length}
        title="No projects found"
        action={
          <button
            onClick={() => {
              setEditing(null);
            }}
          >
            Create project
          </button>
        }
      >
        <div className="projects-list" role="list" aria-label="Projects">
          {projects.map((p) => (
            <div role="listitem" key={p.id}>
            <ProjectCard
              project={p}
              onEdit={() => {
                setEditing(p);
              }}
            />
            </div>
          ))}
        </div>
      </StatePanel>
      <Modal
        open={editing !== undefined}
        title={editing ? "Edit project" : "Create project"}
        onClose={close}
      >
        {editing !== undefined && (
          <ProjectForm
            project={editing || undefined}
            onSaved={(id) => {
              setEditing(undefined);
              selectProject(id);
            }}
          />
        )}
      </Modal>
    </>
  );
}
