import { useMemo, useState } from "react";
import { Button, TextInput } from "@mantine/core";
import "./features/library/cards.css";
import { Icon } from "./Common";
import { InfoHelp } from "./features/help/InfoHelp";
import {
  type Row,
  type Workspace,
  done,
  percent,
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
  const allTickets = db.tickets.filter((ticket) => matches.some((project) => project.id === ticket.project));
  const blockerProjects = matches.filter((project) =>
    db.tickets.some((ticket) => ticket.project === project.id && ticket.status === "Blocked"),
  ).length;

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
          <b>{done(allTickets)}</b> of {allTickets.length} tickets done
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
              tickets={db.tickets.filter((ticket) => ticket.project === project.id)}
              documents={db.documents.filter(doc => doc.project === project.id).length}
              milestones={db.milestones.filter((milestone) => milestone.project === project.id)}
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

function ProjectFolder({ project, tickets, milestones, documents, open, edit }: {
  project: Row;
  tickets: Row[];
  milestones: Row[];
  documents: number;
  open: () => void;
  edit: () => void;
}) {
  const blocked = tickets.filter((ticket) => ticket.status === "Blocked").length;
  const inProgress = tickets.filter((ticket) => ticket.status === "In progress").length;
  const completedMilestones = milestones.filter((milestone) => {
    const work = tickets.filter((ticket) => ticket.milestone === milestone.id);
    return work.length > 0 && done(work) === work.length;
  }).length;
  const health = !tickets.length ? "pending" : blocked ? "blocked" : "clear";
  const statusCounts = new Map(meterStatuses.map((status) => [
    status,
    tickets.filter((ticket) => ticket.status === status).length,
  ]));
  const accessibleBreakdown = meterStatuses
    .map((status) => `${status}: ${statusCounts.get(status) || 0}`)
    .join(", ");
  const meterSegments = tickets.length <= 40
    ? meterStatuses.flatMap((status) =>
        tickets.filter((ticket) => ticket.status === status).map((ticket) => ({ status, key: ticket.id, weight: undefined })),
      )
    : meterStatuses.flatMap((status) => {
        const count = statusCounts.get(status) || 0;
        return count ? [{ status, key: status, weight: count }] : [];
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
          <b>{tickets.length ? `${percent(tickets)}%` : "—"}</b>
          <span>{tickets.length ? `${done(tickets)} of ${tickets.length} tickets complete` : "Progress pending"}</span>
        </div>
        <div
          className={`folder-meter${tickets.length ? "" : " is-empty"}`}
          role="img"
          aria-label={tickets.length ? `Ticket status. ${accessibleBreakdown}` : "Progress pending. No tickets yet."}
        >
          {tickets.length ? meterSegments.map((segment) => (
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
            <dd>{milestones.length ? `${completedMilestones}/${milestones.length} done` : "—"}</dd>
          </div>
          <div><dt>Documents</dt><dd>{documents}</dd></div>
        </dl>
      </div>
    </article>
  );
}
