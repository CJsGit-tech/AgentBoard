import { type ReactNode } from "react";
export type ReaderBlock =
  | { type: "heading"; level: number; value: string; line: number }
  | { type: "paragraph" | "quote"; value: string; line: number }
  | { type: "code"; value: string; line: number; info?: string }
  | { type: "list"; ordered: boolean; items: string[]; line: number }
  | { type: "table"; columns: string[]; rows: string[][]; line: number };

export function splitReaderText(text: string): ReaderBlock[] {
  const lines = text.split(/\r?\n/);
  const blocks: ReaderBlock[] = [];
  const heading = /^(#{1,6})\s+(.+)/;
  const list = /^\s*([-*+]\s+|\d+[.)]\s+)(.*)/;
  const fence = /^\s*```/;
  const cells = (line:string) => line.trim().replace(/^\||\|$/g, "").split(/(?<!\\)\|/).map(cell => cell.trim().replace(/\\\|/g,"|"));
  const tableAt = (i:number) => /\|/.test(lines[i] || "") && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i + 1] || "");
  let i = 0;
  while (i < lines.length) {
    const start = i, line = lines[i++];
    if (!line.trim()) continue;
    const title = heading.exec(line), item = list.exec(line);
    if (fence.test(line)) {
      const first = i;
      while (i < lines.length && !fence.test(lines[i])) i++;
      blocks.push({type:"code",value:lines.slice(first,i).join("\n"),line:start,info:line.trim().slice(3).trim()});
      if (i < lines.length) i++;
    } else if (title) {
      blocks.push({type:"heading",level:title[1].length,value:title[2].trim(),line:start});
    } else if (tableAt(start)) {
      const columns = cells(line), rows: string[][] = [];
      i++;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) rows.push(cells(lines[i++]));
      blocks.push({type:"table",columns,rows,line:start});
    } else if (item) {
      const ordered = /^\d/.test(item[1]), items = [line];
      while (i < lines.length) {
        const next = list.exec(lines[i]);
        if (!next || (!/^\s/.test(lines[i]) && /^\d/.test(next[1]) !== ordered)) break;
        items.push(lines[i]); i++;
      }
      blocks.push({type:"list",ordered,items,line:start});
    } else if (/^>\s?/.test(line)) {
      const quote = [line.replace(/^>\s?/, "")];
      while (i < lines.length && /^>\s?/.test(lines[i])) quote.push(lines[i++].replace(/^>\s?/, ""));
      blocks.push({type:"quote",value:quote.join(" "),line:start});
    } else {
      while (i < lines.length && lines[i].trim() && !heading.test(lines[i]) && !list.test(lines[i]) && !fence.test(lines[i]) && !/^>/.test(lines[i]) && !tableAt(i)) i++;
      blocks.push({type:"paragraph",value:lines.slice(start,i).join(" "),line:start});
    }
  }
  return blocks;
}

function readerInline(text:string, resolveRecord?:(id:string)=>string|undefined) {
  return text.split(/(\b(?:AB|P|M|D|R|RUN)-[a-f0-9]{12}\b|\*\*[^*\n]+\*\*|__[^_\n]+__|`[^`\n]+`|\[[^\]\n]+\]\(https?:\/\/[^)\s]+\)|\*[^*\n]+\*|(?<!\w)_[^_\n]+_(?!\w))/g).map((part,i) => {
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) return <strong key={i}>{part.slice(2,-2)}</strong>;
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) return <em key={i}>{part.slice(1,-1)}</em>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={i}>{part.slice(1,-1)}</code>;
    const recordURL=resolveRecord?.(part);
    if(recordURL)return <a key={i} href={recordURL}>{part}</a>;
    const link = /^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/.exec(part);
    return link ? <a href={link[2]} key={i}>{link[1]}</a> : part;
  });
}
function ReaderList({lines,ordered,resolveRecord}: {lines:string[];ordered:boolean;resolveRecord?:(id:string)=>string|undefined}) {
 const indent=(line:string)=>line.match(/^\s*/)?.[0].replace(/\t/g,"    ").length||0;
 const base=indent(lines[0]||""),items:ReactNode[]=[];
 for(let i=0;i<lines.length;) {
   const line=lines[i++],children:string[]=[];
   while(i<lines.length && indent(lines[i])>base)children.push(lines[i++]);
   items.push(<li key={i}>{readerInline(line.replace(/^\s*(?:[-*+]\s+|\d+[.)]\s+)/,""),resolveRecord)}{children.length>0 && <ReaderList lines={children} ordered={/^\s*\d/.test(children[0])} resolveRecord={resolveRecord}/>}</li>);
 }
 const List=ordered?"ol":"ul";return <List>{items}</List>;
}
export function Markdown({text, blocks = splitReaderText(text), prefix, resolveRecord}: {text:string;blocks?:ReaderBlock[];prefix?:string;resolveRecord?:(id:string)=>string|undefined}) {
  const headings = blocks.filter(b => b.type === "heading");
  const shallowest = headings.length ? Math.min(...headings.map(b => b.level)) : 1;
  return <div className="cp-prose cp-document-prose">{blocks.map(b => {
    if (b.type === "heading") {
      const Level = (["h2","h3","h4","h5","h6"] as const)[Math.min(4,b.level-shallowest)];
      return <Level key={b.line} data-md-line={b.line} data-md-level={b.level} tabIndex={-1} id={prefix ? prefix+"-"+b.line : undefined}>{readerInline(b.value,resolveRecord)}</Level>;
    }
    if (b.type === "code") return <pre key={b.line} data-md-line={b.line} data-md-info={b.info} tabIndex={0} aria-label="Code example"><code>{b.value}</code></pre>;
    if (b.type === "quote") return <blockquote key={b.line} data-md-line={b.line}>{readerInline(b.value,resolveRecord)}</blockquote>;
    if (b.type === "list") {
      const List = b.ordered ? "ol" : "ul";
      return <div key={b.line} data-md-line={b.line} className="reader-list-block"><ReaderList lines={b.items} ordered={b.ordered} resolveRecord={resolveRecord}/></div>;
    }
    if (b.type === "table") {
      const context = headings.filter(h=>h.line < b.line).at(-1)?.value;
      return <div key={b.line} data-md-line={b.line} className="cp-evidence" role="region" aria-label={context ? context+" table" : "Document table"} tabIndex={0}>
        <table><thead><tr>{b.columns.map((c,n)=><th scope="col" key={n}>{readerInline(c,resolveRecord)}</th>)}</tr></thead>
          <tbody>{b.rows.map((row,r)=><tr key={r}>{b.columns.map((_,n)=>n===0 ? <th key={n} scope="row">{readerInline(row[n]||"",resolveRecord)}</th> : <td key={n}>{readerInline(row[n]||"",resolveRecord)}</td>)}</tr>)}</tbody></table>
      </div>;
    }
    return <p key={b.line} data-md-line={b.line}>{readerInline(b.value,resolveRecord)}</p>;
  })}</div>;
}
