import { kinds, type Workspace } from "./model";
import { Markdown } from "./features/documents/Markdown";
export function DocumentContent({text,db,project,prefix}:{text:string;db:Workspace;project?:string;prefix?:string}) {
 const links=new Map<string,string>();
 for(const kind of kinds)for(const row of db[kind])if((row.project||row.id)===project)links.set(row.id,`#${kind}/${row.id}`);
 return <div className="reader-text"><Markdown text={text} prefix={prefix} resolveRecord={id=>links.get(id)}/></div>;
}
