import type { WorkspaceRefresh } from "./model";
import { Button, Drawer, Menu, NativeSelect, TextInput, Tree, useTree, type TreeNodeData } from "@mantine/core";
import { useId, useLayoutEffect, useMemo, useRef, useState } from "react";
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
export function documentBuckets(db:Workspace,rows:Row[],groupBy:DocumentGrouping) {
 const groups=new Map<string,{key:string;label:string;rows:Row[]}>();
 for(const row of rows){const label=groupBy==="Family"?familyOf(row):groupBy==="Type"?typeOf(row):nameOf(db,"projects",row.project);const key=groupBy==="Project"?row.project||"":label;const group=groups.get(key)||{key,label,rows:[]};group.rows.push(row);groups.set(key,group);}
 return [...groups.values()];
}
export function DocumentLibrary({initialId,db,rows,grouping,audit,edit,refresh}:{initialId?:string;db:Workspace;rows:Row[];grouping:DocumentGrouping;audit:boolean;edit:(editor:Editor)=>void;refresh?:WorkspaceRefresh}) {
 const [selectedId,select]=useState(initialId),[browse,showBrowse]=useState(false),[linked,showLinked]=useState(false),[query,search]=useState(""),[status,setStatus]=useState("");
 const [editing,setEditing]=useState<Row|null>(null);
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
 function read(id:string){if(!window.dispatchEvent(new Event("agentboard:before-navigate",{cancelable:true})))return;setEditing(null);select(id);showBrowse(false);showLinked(false);search("");setStatus("");}
 return <div className="document-workspace" ref={workspaceRef}>
   <header className="reader-heading"><div><p className="reader-kicker">{typeOf(selected)} / {nameOf(db,"projects",selected.project)}</p><h2>{selected.name}</h2><p className="reader-byline">Revision {selected.revision} · {stamp(selected.updated_at)} · {latestEditor(selected)}</p></div></header>
   <div className="reader-actions" ref={actionsRef}>
    <Button variant="default" size="xs" onClick={()=>showBrowse(true)} leftSection={<Icon page="browse"/>}>Browse documents</Button>
    <Button variant="default" size="xs" onClick={()=>showLinked(true)}>Linked tickets ({links.length})</Button>
    <Button variant="default" size="xs" onClick={()=>edit({kind:"documents",row:selected,panel:"History"})}>History</Button>
    <Menu position="bottom-end"><Menu.Target><Button variant="default" size="xs">More actions</Button></Menu.Target><Menu.Dropdown><Menu.Item onClick={()=>setEditing(selected)} disabled={!!editing}>Edit document</Menu.Item><Menu.Item component="a" href={"#documents/"+selected.id}>Record link</Menu.Item></Menu.Dropdown></Menu>
   </div>
   {editing ? <RecordEditor key={editing.id} inline db={db} editor={{kind:"documents",row:editing}} scope={selected.project||""} close={()=>{setEditing(null);requestAnimationFrame(()=>actionsRef.current?.querySelector<HTMLButtonElement>("button")?.focus());}} open={edit} refresh={refresh||(async()=>{})}/> : <div className="document-reader-grid"><details className="document-page-index" open><summary>On this page</summary><nav aria-label="On this page">{headings.map(heading=><a key={heading.line} href={"#"+prefix+"-"+heading.line} onClick={event=>{event.preventDefault();const target=document.getElementById(prefix+"-"+heading.line);target?.scrollIntoView({block:"start"});target?.focus({preventScroll:true});}}>{heading.value}</a>)}{!headings.length&&<small>No section headings.</small>}</nav></details>
   <article className="document-prose-column" aria-label={selected.name}>
    {!!selected.source_documents?.length&&<p className="source-links"><span className="source-label">Based on</span>{selected.source_documents.map(id=><a className="source-chip" key={id} href={"#documents/"+id}>{nameOf(db,"documents",id)}</a>)}</p>}
    {!!selected.canvas_versions?.length&&<DesignCanvas key={selected.id} document={selected}/>}
    <DocumentContent db={db} project={selected.project} text={text} prefix={prefix}/>
    {!!selected.tags?.length&&<p>{selected.tags.join(" · ")}</p>}
    {selected.previews?.map(asset=><VisualPreview key={selected.id+asset.digest+asset.filename} document={selected.id} {...asset}/>)}
    {audit&&<dl className="reader-audit"><div><dt>Created</dt><dd>{stamp(selected.created_at)}</dd></div><div><dt>Updated</dt><dd>{stamp(selected.updated_at)}</dd></div><div><dt>Latest editor</dt><dd>{latestEditor(selected)}</dd></div></dl>}
   </article></div>}
   <Drawer opened={browse} onClose={()=>showBrowse(false)} title="Browse documents" position="left" size="min(360px,95vw)" closeButtonProps={{"aria-label":"Close document browser"}}>
    <Tree tree={tree} data={nodes} aria-label="Documents" levelOffset={16} onKeyDownCapture={event=>{if(!["Enter"," "].includes(event.key))return;const id=(event.target as HTMLElement).closest<HTMLElement>('[role="treeitem"]')?.dataset.value;if(!id)return;event.preventDefault();event.stopPropagation();if(id.startsWith("group:"))tree.toggleExpanded(id);else read(id);}}
    renderNode={({node,hasChildren,expanded,elementProps})=><div {...elementProps} className="library-node" data-current={selected.id===node.value||undefined} onClick={event=>{elementProps.onClick(event);if(!hasChildren)read(node.value);}}>{hasChildren&&<span className={expanded?"folder-caret open":"folder-caret"} aria-hidden="true"/>}<Icon page={hasChildren?"folder":"file"}/><span>{node.label}</span>{hasChildren&&<small>{node.children?.length}</small>}</div>}/>
   </Drawer>
   <Drawer opened={linked} onClose={()=>showLinked(false)} title={"Linked tickets · "+selected.name} position="right" size="min(570px,95vw)" closeButtonProps={{"aria-label":"Close linked tickets"}}>
    <TextInput type="search" label="Search linked tickets" value={query} onChange={e=>search(e.currentTarget.value)}/><NativeSelect label="Ticket status" value={status} onChange={e=>setStatus(e.currentTarget.value)} data={[{value:"",label:"All statuses"},...statuses]}/>
    {[...groups].map(([name,tickets])=><section className="linked-ticket-group" key={name}><h3>{name}</h3>{tickets.map(ticket=><div key={ticket.id} className="log"><small>{[ticket.documents?.includes(selected.id)?"Context":"",ticket.output_documents?.includes(selected.id)?"Output":""].filter(Boolean).join(" + ")}</small><TicketSummary db={db} ticket={ticket} open={row=>edit({kind:"tickets",row})} status/></div>)}</section>)}
    {!matching.length&&<Empty>{links.length?"No matching linked tickets.":"No linked tickets."}</Empty>}
   </Drawer>
 </div>;
}
