import { useEffect, useId, useLayoutEffect, useRef, useState, type ClipboardEvent, type ReactNode } from "react";
import "./RichTextEditor.css";
import { InfoHelp } from "../help/InfoHelp";

type Props = {
  disabled?: boolean;
  value: string;
  onChange: (markdown: string) => void;
  render: (markdown: string) => ReactNode;
  invalid?: boolean;
  errorId?: string;
};
type Mode = "Rich text" | "Markdown";
type Original = { html: string; source: string; separator: string };
type Originals = { leading: string; blocks: WeakMap<Node, Original> };
type MarkState = { bold:boolean; italic:boolean; bullets:boolean; numbers:boolean; block:string; structured:boolean };
const baseState:MarkState = {bold:false,italic:false,bullets:false,numbers:false,block:"p",structured:false};
const inlineTags = new Set(["b","strong","i","em","code","a","br","span"]);
const blocks = new Set(["p","div","blockquote","pre","ul","ol","table","h1","h2","h3","h4","h5","h6"]);
const allowed = new Set([...inlineTags,...blocks,"li","thead","tbody","tr","th","td"]);
const blockChoice = ["p","h1","h2","h3","h4","h5","h6","blockquote"];

// The reader creates the nodes. Copy only the semantic elements required for editing.
function cleanNode(node:Node):Node {
  if(node.nodeType===Node.TEXT_NODE) return document.createTextNode(node.textContent||"");
  if(!(node instanceof HTMLElement)) return document.createTextNode("");
  const tag=node.tagName.toLowerCase();
  if(!allowed.has(tag)) return document.createTextNode(node.textContent||"");
  const copy=document.createElement(tag);
  if(tag==="a") {
    const href=node.getAttribute("href")||"";
    if(/^https?:\/\//i.test(href)) copy.setAttribute("href",href);
  }
  if(tag==="th" && node.hasAttribute("scope")) copy.setAttribute("scope",node.getAttribute("scope")!);
  for(const child of node.childNodes) copy.append(cleanNode(child));
  return copy;
}
function editorBlock(node:HTMLElement, raw:string):HTMLElement {
  const table=node.tagName==="DIV" && node.querySelector(":scope > table, :scope > ul, :scope > ol");
  const clean=cleanNode(table||node) as HTMLElement;
  const level=Number(node.dataset.mdLevel);
  if(level>=1 && level<=6) {
    const heading=document.createElement("h"+level);
    heading.append(...Array.from(clean.childNodes));
    return heading;
  }
  if(clean.tagName==="PRE") clean.dataset.info=node.dataset.mdInfo||"";
  if(clean.tagName==="OL") {
    const start=/^\s*(\d+)[.)]/.exec(raw)?.[1];
    if(start && start!=="1") clean.setAttribute("start",start);
  }
  if(clean.tagName==="TABLE") {
    const rows=raw.trim().split(/\r?\n/);
    const columnCount=(line:string)=>line.trim().replace(/^\||\|$/g,"").split(/(?<!\\)\|/).length;
    if(rows.some(row=>columnCount(row)!==columnCount(rows[0]))) {
      throw new Error("This table has rows of different widths. Edit it in Markdown to keep every cell.");
    }
    clean.dataset.divider=rows[1].trim();
  }
  return clean;
}
function getProjection(stage:HTMLElement,source:string) {
  const root=stage.firstElementChild;
  const offsets=[0];
  for(const m of source.matchAll(/\n/g)) offsets.push(m.index!+1);
  const nodes=Array.from(root?.children||[]).filter((n):n is HTMLElement=>n instanceof HTMLElement);
  if((source.trim()&&!nodes.length)||nodes.some(n=>n.dataset.mdLine===undefined)) throw new Error("The reader could not identify editable document blocks. Use Markdown to edit this document.");
  const original:Originals={leading:source.slice(0,offsets[Number(nodes[0]?.dataset.mdLine)||0]),blocks:new WeakMap()};
  const fragment=document.createDocumentFragment();
  nodes.forEach((n,i)=>{
    const begin=offsets[Number(n.dataset.mdLine)];
    const end=nodes[i+1]?offsets[Number(nodes[i+1].dataset.mdLine)]:source.length;
    const raw=source.slice(begin,end);
    const separator=raw.match(/(?:\r?\n[ \t]*)+$/)?.[0]||"";
    const element=editorBlock(n,raw);
    original.blocks.set(element,{html:element.outerHTML,source:raw.slice(0,raw.length-separator.length),separator});
    fragment.append(element);
  });
  return {fragment,original};
}
function inlineMarkdown(node:Node):string {
  if(node.nodeType===Node.TEXT_NODE) return (node.textContent||"").replace(/\u00a0/g," ");
  if(!(node instanceof HTMLElement)) return "";
  const contents=Array.from(node.childNodes,inlineMarkdown).join("");
  switch(node.tagName) {
    case "STRONG": case "B": return contents ? "**"+contents+"**" : "";
    case "EM": case "I": return contents ? "_"+contents+"_" : "";
    case "A": return node.getAttribute("href") ? "["+contents+"]("+node.getAttribute("href")+")" : contents;
    case "CODE": return "`"+(node.textContent||"")+"`";
    case "BR": return "\n";
    default: return contents;
  }
}
function markdownBlock(node:Node):string {
  if(!(node instanceof HTMLElement)) return inlineMarkdown(node);
  const tag=node.tagName.toLowerCase(), contents=inlineMarkdown(node);
  if((tag==="div"||tag==="p"||/^h[1-6]$/.test(tag)) && Array.from(node.children).some(n=>blocks.has(n.tagName.toLowerCase()))) {
    return Array.from(node.childNodes,markdownBlock).join("\n");
  }
  if(/^h[1-6]$/.test(tag)) return "#".repeat(Number(tag[1]))+" "+contents;
  if(tag==="pre") return "```"+(node.dataset.info||"")+"\n"+(node.textContent||"")+"\n```";
  if(tag==="blockquote") {
    const hasBlocks=Array.from(node.children).some(child=>blocks.has(child.tagName.toLowerCase()));
    const quoted=hasBlocks?Array.from(node.childNodes,markdownBlock).join("\n\n"):contents;
    return quoted.replace(/^/gm,"> ");
  }
  if(tag==="ul"||tag==="ol") {
    const start=Number(node.getAttribute("start")||"1");
    return Array.from(node.children).map((li,index)=>{
      const children=Array.from(li.childNodes);
      const first=children.filter(x=>!(x instanceof HTMLElement && /^(UL|OL)$/.test(x.tagName))).map(inlineMarkdown).join("");
      const nested=children.filter(x=>x instanceof HTMLElement && /^(UL|OL)$/.test(x.tagName)).map(x=>markdownBlock(x).replace(/^/gm,"  "));
      const marker=tag==="ol"?(start+index)+". ":"- ";
      return [marker+first,...nested].join("\n");
    }).join("\n");
  }
  if(tag==="table") {
    const rows=Array.from((node as HTMLTableElement).rows);
    const encode=(row:HTMLTableRowElement)=>"| "+Array.from(row.cells,c=>inlineMarkdown(c).replace(/\|/g,"\\|").replace(/\n+/g," ")).join(" | ")+" |";
    if(!rows.length) return "";
    const divider=node.dataset.divider || "| "+Array.from(rows[0].cells,()=>"---").join(" | ")+" |";
    return [encode(rows[0]),divider,...rows.slice(1).map(encode)].join("\n");
  }
  return contents==="\n"?"":contents;
}
function serialize(editor:HTMLElement,original:Originals):string {
  if(!editor.textContent && !editor.querySelector("table,pre")) return "";
  const nodes=Array.from(editor.childNodes);
  let result=original.leading;
  nodes.forEach((n,i)=>{
    const saved=original.blocks.get(n);
    result+=saved && n instanceof HTMLElement && n.outerHTML===saved.html ? saved.source : markdownBlock(n);
    if(i===nodes.length-1) result+=saved?.separator||"";
    else {
      const next=nodes[i+1];
      const isBlock=(x:Node)=>x instanceof HTMLElement && blocks.has(x.tagName.toLowerCase());
      result+=saved?.separator || (isBlock(n)||isBlock(next)?"\n\n":"");
    }
  });
  return result;
}
function sourceOnlyReason(source:string):string {
  let insideFence=false;
  for(const line of source.split(/\r?\n/)) {
    if(!insideFence && /^\s*`{4,}/.test(line)) return "Long code fences are available in Markdown mode.";
    if(/^\s*```/.test(line)) {insideFence=!insideFence;continue;}
    if(insideFence) continue;
    if(/^(?: {4}|\t)\S/.test(line)||(/ {2,}$/.test(line)&&line.trim())) return "Indented blocks and hard line breaks are available in Markdown mode.";
    const prose=line.replace(/`[^`\n]+`/g,"");
    const nestedMarks=/(?:\*{3}|_{3})|\*\*[^*\n]*_[^_\n]+_[^*\n]*\*\*|__[^_\n]*\*[^*\n]+\*[^_\n]*__|_[^_\n]*\*\*[^*\n]+\*\*[^_\n]*_|\*[^*\n]*__[^_\n]+__[^*\n]*\*/.test(prose);
    if(nestedMarks) return "Nested emphasis is available in Markdown mode. Its formatting is preserved there.";
    if(/^\s*(?:~~~|!\[|\[\^|\[[^\]]+\]:|[-+*]\s+\[[ xX]\]|-\s*-\s*-[-\s]*$|={3,}\s*$|>\s*>)/.test(prose) ||
       /<\/?[a-z][\w-]*(?:\s+[^>]*|\/?)>|!\[[^\]]*\]\(|~~[^~]+~~|\[[^\]]+\]\[(?:[^\]]*)\]|\[[^\]]+\]\((?!https?:\/\/)/i.test(prose) || /`{2}/.test(line)) {
      return "This document has Markdown that the rich editor cannot format. Edit it in Markdown to keep the original.";
    }
    if(/^\s+([-*+]\s|\d+[.)]\s)/.test(line)) return "Nested lists are available in Markdown mode. Their indentation is preserved there.";
  }
  return insideFence ? "Close the code fence in Markdown to switch to Rich text." : "";
}
function nearestBlock(root:HTMLElement,node:Node):HTMLElement|null {
  let element=node instanceof HTMLElement?node:node.parentElement;
  while(element && element!==root && element.parentElement!==root) element=element.parentElement;
  return element===root?null:element;
}
function inside(root:HTMLElement|null,range:Range|null):range is Range {
  return !!root && !!range && root.contains(range.startContainer) && root.contains(range.endContainer);
}
const formatActions=[
  ["bold","Bold","B"],["italic","Italic","I"],["insertUnorderedList","Bulleted list","• List"],["insertOrderedList","Numbered list","1. List"],
] as const;

export default function RichTextEditor({disabled=false,value,onChange,render,invalid,errorId}:Props) {
  const [mode,setMode]=useState<Mode>(()=>sourceOnlyReason(value)?"Markdown":"Rich text");
  const [notice,setNotice]=useState(()=>sourceOnlyReason(value));
  const [marks,setMarks]=useState<MarkState>(baseState);
  const [projection,setProjection]=useState(value);
  const [pasteDraft,setPasteDraft]=useState<{text:string;range:Range}|null>(null);
  const toolbar=useRef<HTMLDivElement>(null);
  const root=useRef<HTMLDivElement>(null),stage=useRef<HTMLDivElement>(null),pasteStage=useRef<HTMLDivElement>(null),sourceArea=useRef<HTMLTextAreaElement>(null);
  const last=useRef<string|null>(null), selection=useRef<Range|null>(null), originals=useRef<Originals>({leading:"",blocks:new WeakMap()});
  const focusAfterSwitch=useRef(false),tabs=useId(),helpId=useId();
  const lastChange=useRef(onChange);
  lastChange.current=onChange;
  useLayoutEffect(()=>{
    if(mode!=="Rich text"||!root.current||!stage.current||value===last.current) return;
    if(projection!==value) {setProjection(value);return;}
    const reason=sourceOnlyReason(value);
    if(reason) {setNotice(reason);setMode("Markdown");return;}
    try {
      const {fragment,original}=getProjection(stage.current,value);
      originals.current=original;
      root.current.replaceChildren(fragment);
      if(!root.current.childNodes.length) root.current.append(document.createElement("p"));
      last.current=value;
      selection.current=null;
    } catch(e) {setNotice(e instanceof Error?e.message:"Switch to Markdown to edit this content.");setMode("Markdown");}
  },[mode,value,projection]);
  useEffect(()=>{
    const remember=()=>{
      const editor=root.current, picked=document.getSelection();
      if(!editor||!picked?.rangeCount) return;
      const range=picked.getRangeAt(0);
      if(!inside(editor,range)) return;
      selection.current=range.cloneRange();
      const element=range.startContainer instanceof Element?range.startContainer:range.startContainer.parentElement;
      const ancestor=element?.closest("p,h1,h2,h3,h4,h5,h6,blockquote,li,pre,td,th");
      const current=ancestor?.tagName.toLowerCase()||"p";
      setMarks({bold:document.queryCommandState("bold"),italic:document.queryCommandState("italic"),bullets:!!element?.closest("ul"),numbers:!!element?.closest("ol"),block:blockChoice.includes(current)?current:"p",structured:!!element?.closest("table,pre")});
    };
    document.addEventListener("selectionchange",remember);
    return ()=>document.removeEventListener("selectionchange",remember);
  },[]);
  useEffect(()=>{
    const bar=toolbar.current;
    if(!bar || "focusGroup" in HTMLElement.prototype)return;
    const controls=()=>Array.from(bar.querySelectorAll<HTMLElement>("button,select"));
    controls().forEach((control,index)=>control.tabIndex=index===0?0:-1);
    const focus=(event:FocusEvent)=>controls().forEach(control=>control.tabIndex=control===event.target?0:-1);
    const move=(event:KeyboardEvent)=>{
      if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
      const items=controls(),index=items.indexOf(document.activeElement as HTMLElement);
      if(index<0)return;
      const direction=getComputedStyle(bar).direction==="rtl"?-1:1;
      const next=event.key==="Home"?0:event.key==="End"?items.length-1:(index+(event.key==="ArrowRight"?direction:-direction)+items.length)%items.length;
      event.preventDefault();items[next]?.focus();
    };
    bar.addEventListener("focusin",focus);bar.addEventListener("keydown",move);
    return()=>{bar.removeEventListener("focusin",focus);bar.removeEventListener("keydown",move);};
  },[mode]);
  function emit() {
    if(!root.current)return;
    const md=serialize(root.current,originals.current);
    last.current=md;
    lastChange.current(md);
  }
  function restoreRange() {
    const el=root.current;
    if(!el)return null;
    const sel=document.getSelection();
    const current=sel?.rangeCount ? sel.getRangeAt(0) : null;
    const previous=inside(el,current) ? current.cloneRange() : selection.current;
    el.focus({preventScroll:true});
    const range=inside(el,previous)?previous:document.createRange();
    if(range!==previous){range.selectNodeContents(el);range.collapse(false);}
    sel?.removeAllRanges();sel?.addRange(range);
    return range;
  }
  function format(command:string,arg?:string) {
    if(marks.structured || !root.current || !restoreRange()) return;
    document.execCommand("styleWithCSS",false,"false");
    if(!document.execCommand(command,false,arg)) {
      setNotice("This browser cannot apply that format here. You can make the same change in Markdown.");
      return;
    }
    setNotice("");emit();
  }
  function switchMode(next:Mode) {
    if(next===mode)return;
    if(next==="Rich text") {
      const reason=sourceOnlyReason(value);
      if(reason){setNotice(reason);sourceArea.current?.focus();return;}
      setProjection(value);last.current=null;
    }
    focusAfterSwitch.current=true;setNotice("");setMode(next);
  }
  useEffect(()=>{
    if(!focusAfterSwitch.current)return;
    focusAfterSwitch.current=false;
    (mode==="Markdown"?sourceArea.current:root.current)?.focus({preventScroll:true});
  },[mode]);
  function paste(event:ClipboardEvent<HTMLDivElement>) {
    event.preventDefault();
    const md=event.clipboardData.getData("text/markdown");
    const text=md||event.clipboardData.getData("text/plain");
    if(!text){setNotice("Paste plain text or Markdown. An HTML-only clipboard cannot be inserted.");return;}
    const range=restoreRange();
    if(!range)return;
    const isMarkdown=!!md||/^\s*(?:#{1,6}\s|[-*]\s|\d+\.\s|\||```|>\s)/m.test(text)||/\*\*[^*]+\*\*/.test(text);
    if(isMarkdown) {
      const reason=sourceOnlyReason(text);
      if(reason){setNotice(reason+" Paste in Markdown mode.");return;}
      setPasteDraft({text,range:range.cloneRange()});return;
    }
    if(!document.execCommand("insertText",false,text)) {setNotice("The browser could not paste here. Paste in Markdown mode.");return;}
    setNotice("");emit();
  }
  useLayoutEffect(()=>{
    if(!pasteDraft||!pasteStage.current||!root.current)return;
    const editor=root.current;
    const range=pasteDraft.range;
    if(!inside(editor,range)) {setPasteDraft(null);setNotice("Select the insertion point and paste again.");return;}
    let fragment:DocumentFragment;
    try { ({fragment}=getProjection(pasteStage.current,pasteDraft.text)); }
    catch(error) {
      setPasteDraft(null);
      setNotice(error instanceof Error?error.message:"Paste this content in Markdown mode.");
      return;
    }
    const incoming=Array.from(fragment.children);
    const start=nearestBlock(editor,range.startContainer);
    const inline=incoming.length===1 && incoming[0].tagName==="P";
    if(!inline && start && !/^(P|DIV|H[1-6])$/.test(start.tagName)) {
      setPasteDraft(null);setNotice("Paste a block in a paragraph, or choose Markdown to edit a list, table or code block.");return;
    }
    range.deleteContents();
    let lastInserted:Node|null;
    if(inline) {
      const content=document.createDocumentFragment();
      content.append(...Array.from(incoming[0].childNodes));
      lastInserted=content.lastChild;
      range.insertNode(content);
    } else if(start && start.contains(range.startContainer)) {
      const tail=document.createRange();
      tail.setStart(range.startContainer,range.startOffset);
      tail.setEnd(start,start.childNodes.length);
      const trailing=start.cloneNode(false) as HTMLElement;
      trailing.append(tail.extractContents());
      lastInserted=fragment.lastChild;
      start.after(fragment);
      if(lastInserted && trailing.textContent) lastInserted.parentNode?.insertBefore(trailing,lastInserted.nextSibling);
      if(!start.textContent) start.remove();
    } else {
      lastInserted=fragment.lastChild;
      range.insertNode(fragment);
    }
    if(lastInserted?.isConnected) {
      range.selectNodeContents(lastInserted);range.collapse(false);
      const sel=document.getSelection();sel?.removeAllRanges();sel?.addRange(range);
      selection.current=range.cloneRange();
    }
    setPasteDraft(null);setNotice("");emit();
  },[pasteDraft]);
  const activeStates=[marks.bold,marks.italic,marks.bullets,marks.numbers];
  return <section className="rte" aria-label="Document content editor">
    <div className="rte-heading"><span className="with-info"><strong>Content</strong><InfoHelp label="supported formatting" id={helpId}>Use headings, paragraphs, bold, italic, lists, quotations, fenced code, HTTP links and pipe tables. Use Markdown to create links or tables and to edit nested lists or other syntax. Paste carries text and Markdown. File drops and pasted HTML are excluded.</InfoHelp></span>
      <div role="group" aria-label="Content editing mode" className="rte-modes">
        {(["Rich text","Markdown"] as const).map(item=><button key={item} type="button" aria-pressed={mode===item} aria-controls={tabs} onClick={()=>switchMode(item)}>{item}</button>)}
      </div>
    </div>
    <div hidden aria-hidden="true" ref={stage}>{render(projection)}</div>
    {pasteDraft&&<div hidden aria-hidden="true" ref={pasteStage}>{render(pasteDraft.text)}</div>}
    <div id={tabs} className="rte-surface" data-invalid={invalid||undefined}>
      {mode==="Rich text"?<>
        <div ref={toolbar} className="rte-tools" role="toolbar" aria-label="Text formatting" {...{focusgroup:"toolbar wrap"}} aria-controls={tabs+"-content"}>
          <label><span className="sr-only">Block type</span><select aria-label="Block type" value={marks.block} aria-disabled={marks.structured} onChange={e=>format("formatBlock",e.target.value)}>
            <option value="p">Paragraph</option>{[1,2,3,4,5,6].map(n=><option key={n} value={"h"+n}>Heading {n}</option>)}<option value="blockquote">Quote</option>
          </select></label>
          {formatActions.map(([command,title,label],i)=><button key={command} type="button" aria-label={title} title={title} aria-pressed={activeStates[i]}
            aria-disabled={marks.structured} onMouseDown={e=>e.preventDefault()} onClick={()=>format(command)}>{label}</button>)}
        </div>
        <div id={tabs+"-content"} className="rte-editable" ref={root} role="textbox" contentEditable={!disabled} aria-disabled={disabled} suppressContentEditableWarning aria-label="Content" aria-multiline="true" aria-required="true"
          aria-invalid={invalid||undefined} aria-describedby={[invalid&&errorId,helpId].filter(Boolean).join(" ")} spellCheck onInput={emit} onPaste={paste}
          onDrop={event=>{event.preventDefault();setNotice("Use paste to insert plain text or Markdown.");}}
          onBeforeInput={event=>{
            const input=event.nativeEvent as InputEvent;
            if(input.inputType==="insertFromDrop") event.preventDefault();
          }}/>
      </>:<textarea ref={sourceArea} className="rte-source" aria-label="Content" aria-required="true" aria-invalid={invalid||undefined}
        aria-describedby={[invalid&&errorId,helpId].filter(Boolean).join(" ")} rows={12} value={value} spellCheck={false} onChange={e=>{setNotice("");onChange(e.target.value);}}/>}
    </div>
    <p role="status" className="rte-message">{notice}</p>
  </section>;
}
