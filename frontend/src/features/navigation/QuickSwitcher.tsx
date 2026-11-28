// ⌘K quick switcher (Design Profile V5, decision A). Navigation only: it reads records and never writes.
import { useEffect, useMemo, useRef, useState } from "react";
import { Modal } from "@mantine/core";
import { Icon } from "../../Common";
import { request, workspacePath, type Row, type Workspace } from "../../model";
import "./quick-switcher.css";

type Kind = "projects" | "documents" | "tickets";
type Item = { kind: Kind; id: string; name: string; project: string; projectName: string; meta?: string };
const label: Record<Kind, string> = { projects: "Projects", documents: "Documents", tickets: "Tickets" };
const icon = { projects: "projects", documents: "documents", tickets: "tickets" } as const;
const LIMIT = 6;

export function useQuickSwitcherShortcut(open: () => void) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey && event.key.toLowerCase() === "k") {
        event.preventDefault();
        open();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
}

export const shortcutLabel = () => (/Mac|iPhone|iPad/.test(navigator.platform) ? "⌘K" : "Ctrl+K");

export function QuickSwitcher({ opened, onClose, db, scope, openProject }: {
  opened: boolean; onClose: () => void; db: Workspace | null; scope: string; openProject: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [projects, setProjects] = useState<Row[] | null>(null);
  const list = useRef<HTMLUListElement>(null);

  // The directory read is a plain GET; current-project documents and tickets come from the loaded workspace.
  useEffect(() => {
    if (!opened) return;
    setQuery(""); setActive(0);
    let live = true;
    request<Workspace>(workspacePath("")).then(data => { if (live) setProjects(data.projects); }).catch(() => { if (live) setProjects(db?.projects || []); });
    return () => { live = false; };
  }, [opened]); // eslint-disable-line react-hooks/exhaustive-deps

  const items = useMemo(() => {
    const projectRows = projects || db?.projects || [];
    const projectName = (id: string) => projectRows.find(p => p.id === id)?.name || db?.projects.find(p => p.id === id)?.name || "";
    const term = query.trim().toLocaleLowerCase();
    const match = (row: Row) => !term || row.name.toLocaleLowerCase().includes(term) || row.id.toLocaleLowerCase() === term;
    const group = (kind: Kind, rows: Row[], meta?: (row: Row) => string) => rows.filter(match).slice(0, term ? LIMIT : 4)
      .map(row => ({ kind, id: row.id, name: row.name, project: kind === "projects" ? row.id : row.project || scope, projectName: kind === "projects" ? "" : projectName(row.project || scope), meta: meta?.(row) }));
    const inProject = <T extends Row>(rows: T[] = []) => scope ? rows.filter(row => row.project === scope) : [];
    return [
      ...group("projects", projectRows),
      ...group("documents", inProject(db?.documents)),
      ...group("tickets", inProject(db?.tickets), row => row.status || ""),
    ];
  }, [query, projects, db, scope]);

  useEffect(() => { setActive(0); }, [query]);
  useEffect(() => { list.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: "nearest" }); }, [active]);

  const choose = (item: Item | undefined) => {
    if (!item) return;
    onClose();
    if (item.kind === "projects") openProject(item.id);
    else location.hash = `#project/${encodeURIComponent(item.project)}/${item.kind}/${encodeURIComponent(item.id)}`;
  };

  let index = -1;
  const kinds = (Object.keys(label) as Kind[]).filter(kind => items.some(item => item.kind === kind));
  return (
    <Modal opened={opened} onClose={onClose} withCloseButton={false} centered={false} yOffset="12vh" size={560} radius="lg"
      padding={0} classNames={{ content: "qs" }} aria-label="Quick switcher" returnFocus>
      <div className="qs-search">
        <Icon page="search" />
        <input
          data-autofocus
          type="text" role="combobox" aria-expanded="true" aria-controls="qs-results" aria-autocomplete="list"
          aria-activedescendant={items[active] ? `qs-item-${active}` : undefined}
          aria-label={scope ? "Jump to a project, document or ticket" : "Jump to a project"}
          placeholder={scope ? "Jump to a project, document or ticket…" : "Jump to a project…"}
          value={query}
          onChange={event => setQuery(event.currentTarget.value)}
          onKeyDown={event => {
            if (event.key === "ArrowDown") { event.preventDefault(); setActive(i => Math.min(items.length - 1, i + 1)); }
            else if (event.key === "ArrowUp") { event.preventDefault(); setActive(i => Math.max(0, i - 1)); }
            else if (event.key === "Home" && event.ctrlKey) { event.preventDefault(); setActive(0); }
            else if (event.key === "Enter") { event.preventDefault(); choose(items[active]); }
          }}
        />
        <kbd>Esc</kbd>
      </div>
      <ul id="qs-results" ref={list} role="listbox" aria-label="Results" className="qs-results">
        {kinds.map(kind => (
          <li key={kind} role="presentation">
            <div className="overline qs-group" role="presentation">{label[kind]}</div>
            <ul role="group" aria-label={label[kind]}>
              {items.filter(item => item.kind === kind).map(item => {
                index++;
                const i = index;
                return (
                  <li key={item.kind + item.id} id={`qs-item-${i}`} data-index={i} role="option" aria-selected={i === active}
                    className="qs-item" onMouseMove={() => setActive(i)} onClick={() => choose(item)}>
                    <span className="qs-item__icon"><Icon page={icon[item.kind]} /></span>
                    <span className="qs-item__name">{item.name}</span>
                    <span className="qs-item__meta">{[item.meta, item.projectName].filter(Boolean).join(" · ")}</span>
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ul>
      {!items.length && <p className="qs-empty" role="status">No matches for “{query.trim()}”. Try a shorter name.</p>}
      <footer className="qs-foot"><span><kbd>↑</kbd><kbd>↓</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span>{!scope && <span className="qs-note">Open a project to search its documents and tickets.</span>}</footer>
    </Modal>
  );
}
