import type { WorkspaceRefresh } from "./model";
import { Button, Drawer, Menu, NativeSelect, TextInput, Tree, useTree, type TreeNodeData } from "@mantine/core";
import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import { DocumentContent } from "./DocumentContent";
import { DesignCanvas } from "./DesignCanvas";
import { RecordEditor } from "./RecordEditor";
import { VisualPreview } from "./VisualPreview";
import { Empty, Icon } from "./Common";
import { TicketSummary, ticketMilestone } from "./features/tickets/TicketSummary";
import { splitReaderText } from "./features/documents/Markdown";
import "./features/documents/documents.css";
import { documentGroups, documentTypes, latestEditor, linkedDocument, nameOf, stamp, statuses, type Editor, type Row, type Workspace } from "./model";
export type DocumentGrouping = "Family" | "Type" | "Project" | "None";
const familyOf=(doc:Row)=>documentGroups.find(group=>group.types.some(type=>type.value===doc.document_type))?.label||"Unclassified";
const typeOf=(doc:Row)=>documentTypes.find(type=>type.value===doc.document_type)?.label||"Unclassified";
const newest=(rows:Row[])=>[...rows].sort((a,b)=>(b.updated_at||"").localeCompare(a.updated_at||""))[0];

function previewGroups(previews: NonNullable<Row["previews"]>) {
 const groups = new Map<string, typeof previews>();
 for (const preview of previews) {
  const filename = preview.filename.replace(/\.[^.]+$/, "");
  const screen = filename.match(/(?:^|[-_])(Today|Events|Lists|Settings|Plans|People)(?:[-_]|$)/i)?.[1];
  const label = screen ? screen[0].toUpperCase() + screen.slice(1).toLowerCase() :
   /shared[-_ ]?list|list[-_ ]?detail/i.test(filename) ? "List detail" :
   /detail/i.test(filename) ? "Item detail" :
   /form/i.test(filename) ? "Forms" : "Other captures";
  if (!groups.has(label)) groups.set(label, []);
  groups.get(label)!.push(preview);
 }
 return groups;
}

function previewState(filename: string) {
 const states: Array<[RegExp, string]> = [
  [/dark/i, "Dark"], [/light/i, "Light"], [/largest|large[-_ ]text/i, "Large text"],
  [/(?:^|[-_])zh(?:[-_.]|$)/i, "Chinese"], [/lower|[-_]end\./i, "Lower view"],
 ];
 return states.flatMap(([pattern, label]) => pattern.test(filename) ? [label] : []);
}
export function documentBuckets(db:Workspace,rows:Row[],groupBy:DocumentGrouping) {
 const groups=new Map<string,{key:string;label:string;rows:Row[]}>();
 for(const row of rows){const label=groupBy==="Family"?familyOf(row):groupBy==="Type"?typeOf(row):nameOf(db,"projects",row.project);const key=groupBy==="Project"?row.project||"":label;const group=groups.get(key)||{key,label,rows:[]};group.rows.push(row);groups.set(key,group);}
 return [...groups.values()];
}
export function DocumentLibrary({initialId,db,rows,grouping,audit,edit,refresh}:{initialId?:string;db:Workspace;rows:Row[];grouping:DocumentGrouping;audit:boolean;edit:(editor:Editor)=>void;refresh?:WorkspaceRefresh}) {
 const [selectedId,select]=useState(initialId),[browse,showBrowse]=useState(false),[linked,showLinked]=useState(false),[query,search]=useState(""),[status,setStatus]=useState("");
 const [editing,setEditing]=useState<Row|null>(null);
 const [hash,setHash]=useState(location.hash);
 useEffect(()=>{const sync=()=>setHash(location.hash);window.addEventListener("hashchange",sync);return()=>window.removeEventListener("hashchange",sync);},[]);
 const workspaceRef=useRef<HTMLDivElement>(null),actionsRef=useRef<HTMLDivElement>(null);
 useLayoutEffect(()=>{const bar=actionsRef.current,root=workspaceRef.current;if(!bar||!root)return;const measure=()=>root.style.setProperty("--reader-actions-height",bar.getBoundingClientRect().height+"px");measure();const observer=new ResizeObserver(measure);observer.observe(bar);return()=>observer.disconnect();},[]);
 const unique=useId().replace(/:/g,"");
 const selected=editing ? db.documents.find(row=>row.id===editing.id)||editing : rows.find(row=>row.id===selectedId)||newest(rows);
 const nodes=useMemo<TreeNodeData[]>(()=>documentBuckets(db,rows,"Family").map(group=>({value:"group:"+group.key,label:group.label,children:group.rows.map(row=>({value:row.id,label:row.name}))})),[db,rows]);
 const tree=useTree({initialExpandedState:Object.fromEntries(nodes.map(node=>[node.value,true]))});
 if(!selected)return <Empty>No matching documents.</Empty>;
 const links=db.tickets.filter(ticket=>linkedDocument(ticket,selected.id));
 const matching=links.filter(ticket=>(!status||ticket.status===status)&&(!query||[ticket.name,ticketMilestone(db,ticket)].join(" ").toLocaleLowerCase().includes(query.toLocaleLowerCase())));
 const groups=new Map<string,Row[]>();for(const ticket of matching){const name=ticketMilestone(db,ticket);groups.set(name,[...(groups.get(name)||[]),ticket]);}
 const text=selected.content||selected.description||"No document text yet.",prefix=unique+selected.id;
 const headings=splitReaderText(text).filter(block=>block.type==="heading");
 const [route, queryString] = hash.split("?", 2);
 const proof = route === `#documents/${encodeURIComponent(selected.id)}` ? new URLSearchParams(queryString) : new URLSearchParams();
 const previewName = proof.get("preview");
 const preview = previewName && selected.previews?.find(item=>item.filename===previewName&&item.digest===proof.get("digest"));
 const section = proof.get("section");
 const proofUnavailable = !!(previewName && !preview) || (proof.has("revision") && proof.get("revision") !== String(selected.revision)) ||
   (section !== null && !headings.some(heading => String(heading.line) === section));
 const groupsOfPreviews = previewGroups(selected.previews || []);
 function read(id:string){if(!window.dispatchEvent(new Event("agentboard:before-navigate",{cancelable:true})))return;setEditing(null);select(id);showBrowse(false);showLinked(false);search("");setStatus("");}
 const libraryTree=<Tree tree={tree} data={nodes} aria-label="Documents" levelOffset={16} onKeyDownCapture={event=>{if(!["Enter"," "].includes(event.key))return;const id=(event.target as HTMLElement).closest<HTMLElement>('[role="treeitem"]')?.dataset.value;if(!id)return;event.preventDefault();event.stopPropagation();if(id.startsWith("group:"))tree.toggleExpanded(id);else read(id);}}
    renderNode={({node,hasChildren,expanded,elementProps})=><div {...elementProps} className="library-node" data-current={selected.id===node.value||undefined} onClick={event=>{elementProps.onClick(event);if(!hasChildren)read(node.value);}}>{hasChildren&&<span className={expanded?"folder-caret open":"folder-caret"} aria-hidden="true"/>}<Icon page={hasChildren?"folder":"file"}/><span>{node.label}</span>{hasChildren&&<small>{node.children?.length}</small>}</div>}/>;
 return <div className="document-workspace" ref={workspaceRef}>
   <header className="reader-heading"><div><p className="reader-kicker">{typeOf(selected)} / {nameOf(db,"projects",selected.project)}</p><h2>{selected.name}</h2><p className="reader-byline">Revision {selected.revision} · {stamp(selected.updated_at)} · {latestEditor(selected)}</p></div></header>
   <div className="reader-actions" ref={actionsRef}>
    <Button variant="default" size="xs" className="reader-browse" onClick={()=>showBrowse(true)} leftSection={<Icon page="browse"/>}>Browse documents</Button>
    <Button variant="default" size="xs" onClick={()=>showLinked(true)}>Linked tickets ({links.length})</Button>
    <Button variant="default" size="xs" onClick={()=>edit({kind:"documents",row:selected,panel:"History"})}>History</Button>
    <Menu position="bottom-end"><Menu.Target><Button variant="default" size="xs">More</Button></Menu.Target><Menu.Dropdown><Menu.Item onClick={()=>setEditing(selected)} disabled={!!editing}>Edit document</Menu.Item><Menu.Item onClick={()=>{void navigator.clipboard?.writeText(`${location.origin}${location.pathname}#documents/${selected.id}`);}}>Copy link</Menu.Item><Menu.Item component="a" href={"#documents/"+selected.id}>Record link</Menu.Item></Menu.Dropdown></Menu>
   </div>
   {editing ? <RecordEditor key={editing.id} inline db={db} editor={{kind:"documents",row:editing}} scope={selected.project||""} close={()=>{setEditing(null);requestAnimationFrame(()=>actionsRef.current?.querySelector<HTMLButtonElement>("button")?.focus());}} open={edit} refresh={refresh||(async()=>{})}/> : proofUnavailable ?
    <section className="document-proof"><h3>Recorded proof unavailable</h3><p>The linked revision, report section, or screenshot no longer matches the saved reference.</p><a href={`#documents/${selected.id}`}>Open the current document</a></section> : preview ?
    <section className="document-proof"><h3>Recorded screenshot</h3><VisualPreview key={preview.digest+preview.filename} document={selected.id} {...preview}/><a href={`#documents/${selected.id}`}>View full screenshot gallery</a></section> : <div className="document-reader-grid">
   <aside className="document-library" aria-label="Document library">{libraryTree}</aside>
   <article className="document-prose-column" aria-label={selected.name}>
    {!!selected.source_documents?.length&&<p className="source-links"><span className="source-label">Based on</span>{selected.source_documents.map(id=><a className="source-chip" key={id} href={"#documents/"+id}>{nameOf(db,"documents",id)}</a>)}</p>}
    {!!selected.canvas_versions?.length&&<DesignCanvas key={selected.id} document={selected}/>}
    <DocumentContent db={db} project={selected.project} text={text} prefix={prefix}/>
    {section !== null && <FocusProofSection key={`${selected.id}:${selected.revision}:${section}`} target={`${prefix}-${section}`} />}
    {!!selected.tags?.length&&<p>{selected.tags.join(" · ")}</p>}
    {[...groupsOfPreviews].map(([name, assets])=><PreviewGroup key={selected.id+name} documentId={selected.id} name={name} assets={assets}/>)}
    {audit&&<dl className="reader-audit"><div><dt>Created</dt><dd>{stamp(selected.created_at)}</dd></div><div><dt>Updated</dt><dd>{stamp(selected.updated_at)}</dd></div><div><dt>Latest editor</dt><dd>{latestEditor(selected)}</dd></div></dl>}
   </article>
   <details className="document-page-index" open><summary>On this page</summary><nav aria-label="On this page">{headings.map(heading=><a key={heading.line} href={"#"+prefix+"-"+heading.line} onClick={event=>{event.preventDefault();const target=document.getElementById(prefix+"-"+heading.line);target?.scrollIntoView({block:"start"});target?.focus({preventScroll:true});}}>{heading.value}</a>)}{!headings.length&&<small>No section headings.</small>}</nav></details>
   </div>}
   <Drawer opened={browse} onClose={()=>showBrowse(false)} title="Browse documents" position="left" size="min(360px,95vw)" closeButtonProps={{"aria-label":"Close document browser"}}>
    {libraryTree}
   </Drawer>
   <Drawer opened={linked} onClose={()=>showLinked(false)} title={"Linked tickets · "+selected.name} position="right" size="min(570px,95vw)" closeButtonProps={{"aria-label":"Close linked tickets"}}>
    <TextInput type="search" label="Search linked tickets" value={query} onChange={e=>search(e.currentTarget.value)}/><NativeSelect label="Ticket status" value={status} onChange={e=>setStatus(e.currentTarget.value)} data={[{value:"",label:"All statuses"},...statuses]}/>
    {[...groups].map(([name,tickets])=><section className="linked-ticket-group" key={name}><h3>{name}</h3>{tickets.map(ticket=><div key={ticket.id} className="log"><small>{[ticket.documents?.includes(selected.id)?"Context":"",ticket.output_documents?.includes(selected.id)?"Output":""].filter(Boolean).join(" + ")}</small><TicketSummary db={db} ticket={ticket} open={row=>edit({kind:"tickets",row})} status/></div>)}</section>)}
    {!matching.length&&<Empty>{links.length?"No matching linked tickets.":"No linked tickets."}</Empty>}
   </Drawer>
 </div>;
}

function PreviewGroup({ documentId, name, assets }: { documentId: string; name: string; assets: NonNullable<Row["previews"]> }) {
 const [showPreviews, setShowPreviews] = useState(false);
 return <section className="evidence-preview-group">
  <h3>{name} <small>({assets.length})</small></h3>
  <ul>{assets.map(asset=>{
   const state=previewState(asset.filename).join(" · ");
   return <li key={asset.filename}>
    <a href={`#documents/${documentId}?${new URLSearchParams({preview:asset.filename,digest:asset.digest})}`}>{asset.filename}</a>
    {state && <small> · {state}</small>}
   </li>;
  })}</ul>
  <details onToggle={event=>setShowPreviews(event.currentTarget.open)}><summary>Show {name.toLowerCase()} previews</summary>
   {showPreviews && <div className="evidence-preview-grid">{assets.map(asset=><VisualPreview thumbnail key={`${asset.filename}:${asset.digest}`} document={documentId} {...asset}/>)}</div>}
  </details>
 </section>;
}

function FocusProofSection({ target }: { target: string }) {
 useLayoutEffect(()=>{
  const frame=requestAnimationFrame(()=>{
   const heading=document.getElementById(target);
   heading?.scrollIntoView({block:"start"});
   heading?.focus({preventScroll:true});
  });
  return ()=>cancelAnimationFrame(frame);
 },[target]);
 return null;
}
