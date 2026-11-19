import { ElementType, Fragment, ReactNode } from "react";

export interface MarkdownHeading {
  id: string;
  text: string;
  level: number;
}

type MarkdownBlock =
  | { type: "heading"; heading: MarkdownHeading; source: string }
  | { type: "paragraph"; lines: string[] }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "quote"; lines: string[] }
  | { type: "code"; language: string; source: string }
  | { type: "table"; rows: string[][] }
  | { type: "rule" };

const headingPattern = /^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$/;
const unorderedPattern = /^ {0,3}[-+*]\s+(.+)$/;
const orderedPattern = /^ {0,3}\d+[.)]\s+(.+)$/;
const fencePattern = /^ {0,3}(`{3,}|~{3,})(.*)$/;
const rulePattern = /^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$/;

function plainText(markdown: string) {
  return markdown
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    .replace(/~~([^~]+)~~/g, "$1")
    .trim();
}

function slugify(text: string) {
  const slug = text.toLocaleLowerCase().trim()
    .replace(/[^\p{L}\p{N}\s_-]/gu, "")
    .replace(/[\s_]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  return slug || "section";
}

function splitTableRow(line: string) {
  return line.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
}

function isTableSeparator(line: string) {
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function parseBlocks(source: string): MarkdownBlock[] {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  const slugs = new Map<string, number>();
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }

    const fence = line.match(fencePattern);
    if (fence) {
      const marker = fence[1];
      const language = fence[2].trim().split(/\s+/)[0] || "";
      const code: string[] = [];
      index += 1;
      while (index < lines.length && !new RegExp(`^ {0,3}${marker[0]}{${marker.length},}\\s*$`).test(lines[index])) {
        code.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      blocks.push({ type: "code", language, source: code.join("\n") });
      continue;
    }

    const heading = line.match(headingPattern);
    if (heading) {
      const text = plainText(heading[2]);
      const base = slugify(text);
      const occurrence = slugs.get(base) || 0;
      slugs.set(base, occurrence + 1);
      blocks.push({ type: "heading", heading: { id: occurrence ? `${base}-${occurrence + 1}` : base, text, level: heading[1].length }, source: heading[2] });
      index += 1;
      continue;
    }

    if (index + 1 < lines.length && /^(?:=+|-+)\s*$/.test(lines[index + 1])) {
      const text = plainText(line);
      const base = slugify(text);
      const occurrence = slugs.get(base) || 0;
      slugs.set(base, occurrence + 1);
      blocks.push({ type: "heading", heading: { id: occurrence ? `${base}-${occurrence + 1}` : base, text, level: lines[index + 1].includes("=") ? 1 : 2 }, source: line });
      index += 2;
      continue;
    }

    if (rulePattern.test(line)) { blocks.push({ type: "rule" }); index += 1; continue; }

    if (index + 1 < lines.length && line.includes("|") && isTableSeparator(lines[index + 1])) {
      const rows = [splitTableRow(line)];
      index += 2;
      while (index < lines.length && lines[index].trim() && lines[index].includes("|")) {
        rows.push(splitTableRow(lines[index]));
        index += 1;
      }
      blocks.push({ type: "table", rows });
      continue;
    }

    const unordered = line.match(unorderedPattern);
    const ordered = line.match(orderedPattern);
    if (unordered || ordered) {
      const isOrdered = Boolean(ordered);
      const items: string[] = [];
      while (index < lines.length) {
        const match = lines[index].match(isOrdered ? orderedPattern : unorderedPattern);
        if (!match) break;
        items.push(match[1]);
        index += 1;
      }
      blocks.push({ type: "list", ordered: isOrdered, items });
      continue;
    }

    if (/^ {0,3}>/.test(line)) {
      const quote: string[] = [];
      while (index < lines.length && /^ {0,3}>/.test(lines[index])) {
        quote.push(lines[index].replace(/^ {0,3}> ?/, ""));
        index += 1;
      }
      blocks.push({ type: "quote", lines: quote });
      continue;
    }

    const paragraph = [line];
    index += 1;
    while (index < lines.length && lines[index].trim() && !startsBlock(lines, index)) {
      paragraph.push(lines[index]);
      index += 1;
    }
    blocks.push({ type: "paragraph", lines: paragraph });
  }

  return blocks;
}

function startsBlock(lines: string[], index: number) {
  const line = lines[index];
  return headingPattern.test(line) || fencePattern.test(line) || rulePattern.test(line)
    || unorderedPattern.test(line) || orderedPattern.test(line) || /^ {0,3}>/.test(line)
    || (index + 1 < lines.length && /^(?:=+|-+)\s*$/.test(lines[index + 1]))
    || (line.includes("|") && index + 1 < lines.length && isTableSeparator(lines[index + 1]));
}

function safeLinkTarget(target: string) {
  const value = target.trim();
  if (!value || /[\u0000-\u001f]/.test(value)) return null;
  if (value.startsWith("#")) return { href: value, external: false };
  try {
    const url = new URL(value, "https://agentboard.invalid/");
    if (!["https:", "http:", "mailto:"].includes(url.protocol)) return null;
    return { href: value, external: url.origin !== "https://agentboard.invalid" || url.protocol === "mailto:", };
  } catch {
    return null;
  }
}

export function renderInline(markdown: string): ReactNode[] {
  const token = /(!?\[([^\]]*)\]\(([^)\s]+)(?:\s+['"][^'"]*['"])?\)|`([^`]+)`|\*\*([^*]+)\*\*|__([^_]+)__|~~([^~]+)~~|\*([^*]+)\*|_([^_]+)_)/g;
  const result: ReactNode[] = [];
  let cursor = 0;
  let match: RegExpExecArray | null;
  while ((match = token.exec(markdown))) {
    if (match.index > cursor) result.push(markdown.slice(cursor, match.index));
    const key = `inline-${match.index}`;
    if (match[3] !== undefined) {
      if (match[1].startsWith("!")) {
        result.push(match[2]);
      } else {
        const safeTarget = safeLinkTarget(match[3]);
        result.push(safeTarget
          ? <a key={key} href={safeTarget.href} {...(safeTarget.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}>{renderInline(match[2])}</a>
          : match[2]);
      }
    } else if (match[4]) result.push(<code key={key}>{match[4]}</code>);
    else if (match[5] || match[6]) result.push(<strong key={key}>{renderInline(match[5] || match[6])}</strong>);
    else if (match[7]) result.push(<del key={key}>{renderInline(match[7])}</del>);
    else result.push(<em key={key}>{renderInline(match[8] || match[9])}</em>);
    cursor = token.lastIndex;
  }
  if (cursor < markdown.length) result.push(markdown.slice(cursor));
  return result;
}

export function getMarkdownHeadings(source: string): MarkdownHeading[] {
  return parseBlocks(source)
    .filter((block): block is Extract<MarkdownBlock, { type: "heading" }> => block.type === "heading")
    .map((block) => block.heading);
}

function renderParagraph(lines: string[]) {
  return lines.map((line, index) => {
    const hardBreak = /(?: {2,}|\\)$/.test(line);
    const text = hardBreak ? line.replace(/(?: {2,}|\\)$/, "") : line;
    return <Fragment key={index}>{renderInline(text)}{index < lines.length - 1 ? hardBreak ? <br /> : " " : null}</Fragment>;
  });
}

export function MarkdownDocument({ source }: { source: string }) {
  return <div className="markdown-body">{parseBlocks(source).map((block, index) => {
    switch (block.type) {
      case "heading": {
        const Heading = `h${block.heading.level}` as ElementType;
        return <Heading id={block.heading.id} key={`${block.heading.id}-${index}`}>{renderInline(block.source)}</Heading>;
      }
      case "paragraph": return <p key={`paragraph-${index}`}>{renderParagraph(block.lines)}</p>;
      case "list": {
        const List = block.ordered ? "ol" : "ul";
        return <List key={`list-${index}`}>{block.items.map((item, itemIndex) => <li key={itemIndex}>{renderInline(item)}</li>)}</List>;
      }
      case "quote": return <blockquote key={`quote-${index}`}><p>{renderInline(block.lines.join(" "))}</p></blockquote>;
      case "code": return <pre key={`code-${index}`}><code className={block.language ? `language-${block.language}` : undefined}>{block.source}</code></pre>;
      case "table": return <div className="markdown-table-wrap" key={`table-${index}`}><table><thead><tr>{block.rows[0].map((cell, cellIndex) => <th scope="col" key={cellIndex}>{renderInline(cell)}</th>)}</tr></thead><tbody>{block.rows.slice(1).map((row, rowIndex) => <tr key={rowIndex}>{block.rows[0].map((_, cellIndex) => <td key={cellIndex}>{renderInline(row[cellIndex] || "")}</td>)}</tr>)}</tbody></table></div>;
      case "rule": return <hr key={`rule-${index}`} />;
    }
  })}</div>;
}
