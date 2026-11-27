import { useMemo, useState } from "react";
import { Button, TextInput } from "@mantine/core";
import "./features/library/cards.css";
import { Icon } from "./Common";
import { InfoHelp } from "./features/help/InfoHelp";
import {
  type Row,
  type Workspace,
  type ProjectSummary,
} from "./model";

type Props = {
  db: Workspace;
  openProject: (id: string) => void;
  editProject: (row?: Row) => void;
};

const meterStatuses = ["Done", "In progress", "Blocked", "Planned"] as const;

export function Projects({ db, openProject, editProject }: Props) {
  const [query, setQuery] = useState("");
  const matches = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    return db.projects.filter((project) =>
      !term || `${project.name}\n${project.description || ""}`.toLocaleLowerCase().includes(term),
    );
  }, [db.projects, query]);
  const completed = matches.reduce((n, project) => n + (project.summary?.statuses.Done || 0), 0);
  const total = matches.reduce((n, project) => n + totalTickets(project.summary), 0);
  const blockerProjects = matches.filter(project => project.summary?.statuses.Blocked).length;

  return (
    <>
      <header className="heading">
        <div>
          <div className="with-info"><h1>Projects</h1><InfoHelp label="projects">Choose a project to open its workspace.</InfoHelp></div>
        </div>
        <Button className="mast-action" leftSection={<Icon page="plus" />} onClick={() => editProject()}>
          New project
        </Button>
      </header>

      <div className="folder-tools">
        <TextInput
          type="search"
          aria-label="Search projects"
          placeholder="Search projects…"
          leftSection={<Icon page="search" />}
          value={query}
          onChange={(event) => setQuery(event.currentTarget.value)}
        />
        <p className="folder-summary" aria-live="polite">
          <b>{matches.length}</b> {matches.length === 1 ? "project" : "projects"}
          <span aria-hidden="true">·</span>
          <b>{completed}</b> of {total} tickets done
          <span aria-hidden="true">·</span>
          <b className="warn">{blockerProjects}</b> with blockers
        </p>
      </div>

      {matches.length ? (
        <div className="folders" aria-label="Projects">
          {matches.map((project) => (
            <ProjectFolder
              key={project.id}
              project={project}
              open={() => openProject(project.id)}
              edit={() => editProject(project)}
            />
          ))}
        </div>
      ) : (
        <div className="folder-empty">
          <h2>{db.projects.length ? "No matching projects" : "No projects yet"}</h2>
          {db.projects.length ? (
            <button className="link" onClick={() => setQuery("")}>Clear search</button>
          ) : (
            <p>Create a project to begin.</p>
          )}
        </div>
      )}
    </>
  );
}

function totalTickets(summary?: ProjectSummary) {
  return Object.values(summary?.statuses || {}).reduce((n, count) => n + count, 0);
}

function ProjectFolder({ project, open, edit }: {
  project: Row;
  open: () => void;
  edit: () => void;
}) {
  const counts = project.summary?.statuses || {};
  const total = totalTickets(project.summary);
  const blocked = counts.Blocked || 0;
  const completed = counts.Done || 0;
  const health = !total ? "pending" : blocked ? "blocked" : "clear";
  const accessibleBreakdown = meterStatuses.map(status => `${status}: ${counts[status] || 0}`).join(", ");
  const meterSegments = meterStatuses.flatMap(status => {
    const count = counts[status] || 0;
    if (total > 40) return count ? [{ status, key: status, weight: count }] : [];
    return Array.from({ length: count }, (_, i) => ({ status, key: status + i, weight: 1 }));
  });
  return (
    <article className="folder" data-health={health}>
      <div className="folder-tab" data-status={health}>
        <i aria-hidden="true" />
        {health === "pending" ? "Awaiting work" : blocked ? `${blocked} blocked` : "No blockers"}
      </div>
      <div className="folder-body">
        <div className="folder-head">
          <h2>
            <button className="folder-title" title={project.name} onClick={open}>
              {project.name}
            </button>
          </h2>
          <button
            type="button"
            className="folder-settings"
            title="Project settings"
            aria-label={`${project.name} project settings`}
            onClick={edit}
          >
            <Icon page="edit" />
          </button>
        </div>
        <p className="folder-description">{project.description || "No description"}</p>
        <div className="folder-metric">
          <b>{total ? `${Math.round(100 * completed / total)}%` : "—"}</b>
          <span>{total ? `${completed} of ${total} tickets complete` : "Progress pending"}</span>
        </div>
        <div
          className={`folder-meter${total ? "" : " is-empty"}`}
          role="img"
          aria-label={total ? `Ticket status. ${accessibleBreakdown}` : "Progress pending. No tickets yet."}
        >
          {total ? meterSegments.map((segment) => (
            <span
              key={segment.key}
              data-status={segment.status}
              style={segment.weight ? { flex: `${segment.weight} 1 0` } : undefined}
            />
          )) : <span />}
        </div>
        <dl className="folder-facts">
          <div>
            <dt>Milestones</dt>
            <dd>{project.summary?.milestones ? `${project.summary.completed_milestones}/${project.summary.milestones} done` : "—"}</dd>
          </div>
          <div><dt>Documents</dt><dd>{project.summary?.documents || 0}</dd></div>
        </dl>
      </div>
    </article>
  );
}
