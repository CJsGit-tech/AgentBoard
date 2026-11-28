import { useMemo, useState } from "react";
import { Button, SegmentedControl, TextInput } from "@mantine/core";
import "./features/library/cards.css";
import { Icon } from "./Common";
import { InfoHelp } from "./features/help/InfoHelp";
import { ago, perDay, SparkColumns, StatusBar, StatusLegend } from "./features/charts/primitives";
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

type Sort = "Recent" | "Name" | "Progress";
const progress = (project: Row) => {
  const total = totalTickets(project.summary);
  return total ? (project.summary?.statuses.Done || 0) / total : -1;
};

export function Projects({ db, openProject, editProject }: Props) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<Sort>("Recent");
  const matches = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    const found = db.projects.filter((project) =>
      !term || `${project.name}\n${project.description || ""}`.toLocaleLowerCase().includes(term),
    );
    return [...found].sort((a, b) => sort === "Name" ? a.name.localeCompare(b.name)
      : sort === "Progress" ? progress(b) - progress(a)
      : (Date.parse(b.summary?.last_activity || "") || 0) - (Date.parse(a.summary?.last_activity || "") || 0));
  }, [db.projects, query, sort]);
  const completed = matches.reduce((n, project) => n + (project.summary?.statuses.Done || 0), 0);
  const total = matches.reduce((n, project) => n + totalTickets(project.summary), 0);
  const blockerProjects = matches.filter(project => project.summary?.statuses.Blocked).length;
  const idle = matches.find(project => totalTickets(project.summary) && !project.summary?.statuses.Done && !project.summary?.statuses["In progress"]);

  return (
    <>
      <header className="heading">
        <div>
          <div className="with-info"><h1>Projects</h1><InfoHelp label="projects">Choose a project to open its workspace.</InfoHelp></div>
          <p aria-live="polite">
            <b>{completed}</b> of {total} tickets done across {matches.length} {matches.length === 1 ? "project" : "projects"}
            {blockerProjects ? <> · <b className="warn">{blockerProjects}</b> with blockers</> : null}
            {idle ? <> · <b>{idle.name}</b> has {totalTickets(idle.summary)} planned tickets and none started</> : null}
          </p>
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
        <SegmentedControl className="folder-sort" size="xs" radius="xl" value={sort} onChange={(value) => setSort(value as Sort)}
          data={["Recent", "Name", "Progress"]} aria-label="Sort projects" />
      </div>

      {matches.length ? (
        <>
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
          <div className="folder-legend"><StatusLegend /></div>
        </>
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
  const days = perDay(project.summary?.recent_done || []);
  const week = days.reduce((a, b) => a + b, 0);
  const milestones = project.summary?.milestones || 0;
  return (
    <article className="folder v5-project" data-health={!total ? "pending" : blocked ? "blocked" : "clear"}>
      <div className="folder-body">
        <div className="v5-project__top">
          <span className="overline"><Icon page="milestones" /> {milestones} {milestones === 1 ? "milestone" : "milestones"}</span>
          {blocked ? <span className="v5-chip" data-tone="amber"><span aria-hidden="true">◆</span> {blocked} blocked</span> : null}
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
        <h2>
          <button className="folder-title" title={project.name} onClick={open}>
            {project.name}
          </button>
        </h2>
        {project.description
          ? <p className="folder-description">{project.description}</p>
          : <button type="button" className="link v5-project__add" onClick={edit}>Add description</button>}
        <div className="v5-project__progress">
          <div className="v5-project__figure">
            <b>{total ? `${Math.round(100 * completed / total)}%` : "—"}</b>
            <span>{total ? `${completed} of ${total} done · ${counts.Planned || 0} planned` : "Progress pending"}</span>
          </div>
          <StatusBar counts={counts} label={`${project.name} ticket status`} />
        </div>
        <footer className="v5-project__foot">
          <span className="v5-project__spark">
            <SparkColumns values={days} label={`${project.name} tickets done per day, last 7 days`} />
            <span><b>{week}</b> done this week</span>
          </span>
          <span>{ago(project.summary?.last_activity)}</span>
        </footer>
      </div>
    </article>
  );
}
