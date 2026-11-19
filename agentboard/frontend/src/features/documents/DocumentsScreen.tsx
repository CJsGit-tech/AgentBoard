import { useEffect, useRef, useState } from "react";
import { FileUp, Plus } from "lucide-react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { Modal } from "../../components/Modal";
import { DocumentList } from "./DocumentList";
import { DocumentEditor } from "./DocumentEditor";
import { TagFilter } from "../../components/TagFilter";
import { documentKinds, documentPayload, normalizeKind, projectTags } from "../../api/restClient";
type ImportDraft = {
  title: string; description: string; kind: string; featureTags: string[]; concernTags: string[];
  content: string; originalFrontmatter: string; filename: string; unknownTags: string[]; invalidTags: string[]; issues: string[];
  fromFile: { title?: string; description?: string; kind?: string; featureTags?: string[]; concernTags?: string[] };
  titleFromFilename: boolean;
};
export function DocumentsScreen() {
  const { db, projectId, navigate, dirty, setDirty, saveDocument, mode } = useWorkspace();
  const importInput = useRef<HTMLInputElement>(null);
  const importButton = useRef<HTMLButtonElement>(null);
  const importHeading = useRef<HTMLHeadingElement>(null);
  const [create, setCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [featureTag, setFeatureTag] = useState<string[]>([]);
  const [concernTag, setConcernTag] = useState<string[]>([]);
  const [importPreview, setImportPreview] = useState<ImportDraft | null>(null);
  const isImportOpen = importPreview !== null;
  useEffect(() => {
    if (!isImportOpen) return;
    importHeading.current?.focus();
    return () => { importButton.current?.focus(); };
  }, [isImportOpen]);
  const [allowedTags, setAllowedTags] = useState<string[]>([]);
  const [tagChecking, setTagChecking] = useState(false);
  const [tagCheckError, setTagCheckError] = useState("");
  const [importError, setImportError] = useState("");
  const [importSaving, setImportSaving] = useState(false);
  const docs = db.documents.filter(
    (d) =>
      d.projectId === projectId &&
      d.title.toLowerCase().includes(search.toLowerCase()) &&
      (!featureTag.length || featureTag.some((tag) => d.featureTags?.includes(tag))) &&
      (!concernTag.length || concernTag.some((tag) => d.concernTags?.includes(tag))),
  );
  const projectDocuments = db.documents.filter((document) => document.projectId === projectId);
  const featureTags = [...new Set(projectDocuments.flatMap((document) => document.featureTags || []))].sort();
  const concernTags = [...new Set(projectDocuments.flatMap((document) => document.concernTags || []))].sort();
  const importDuplicate = Boolean(importPreview && projectDocuments.some((document) =>
    document.title.trim().toLowerCase() === importPreview.title.trim().toLowerCase()
    || document.sourceFilename === importPreview.filename));
  const importPayload = importPreview ? documentPayload({
    title: importPreview.title,
    content: importPreview.content,
    originalFrontmatter: importPreview.originalFrontmatter,
    description: importPreview.description,
    kind: importPreview.kind,
    featureTags: importPreview.featureTags,
    concernTags: importPreview.concernTags,
  }, "upload", importPreview.filename) : null;
  const importPayloadBytes = importPayload ? new TextEncoder().encode(JSON.stringify(importPayload)).byteLength : 0;
  const importPayloadTooLarge = importPayloadBytes > 1_048_576;
  const updateImport = (changes: Partial<ImportDraft>) => setImportPreview((current) => {
    if (!current) return current;
    const updated = { ...current, ...changes };
    const tagValues = [...updated.featureTags, ...updated.concernTags];
    const validShape = /^(?:feature|concern):[a-z0-9]+(?:-[a-z0-9]+)*$/;
    return {
      ...updated,
      invalidTags: tagValues.filter((tag) => !validShape.test(tag)),
      unknownTags: tagValues.filter((tag) => validShape.test(tag) && !allowedTags.includes(tag)),
    };
  });
  const checkTagCatalog = async (draft = importPreview) => {
    if (!draft) return;
    setTagChecking(true);
    setTagCheckError("");
    try {
      const known = mode === "connected" ? await projectTags(projectId) : [
        "feature:product-project-management", "feature:agent-role-management", "feature:task-coordination",
        "feature:document-management", "feature:progress-tracking", "concern:authorization", "concern:auditability",
        "concern:data-integrity", "concern:retention", "concern:privacy", "concern:reliability",
        "concern:compatibility", "concern:security", "concern:accessibility",
      ];
      setAllowedTags(known);
      setImportPreview((current) => {
        if (!current) return current;
        const tags = [...current.featureTags, ...current.concernTags];
        const validShape = /^(?:feature|concern):[a-z0-9]+(?:-[a-z0-9]+)*$/;
        return {
          ...current,
          invalidTags: tags.filter((tag) => !validShape.test(tag)),
          unknownTags: tags.filter((tag) => validShape.test(tag) && !known.includes(tag)),
        };
      });
    } catch (cause) {
      setTagCheckError(cause instanceof Error ? cause.message : "Could not validate tags against the project catalog.");
    } finally {
      setTagChecking(false);
    }
  };
  return (
    <>
      <PageHeader
        title="Documents"
        description="Product context, decisions and outputs. Always close to the work."
        actions={
          <button
            className="primary"
            onClick={() => {
              setCreate(true);
            }}
          >
            <Plus size={16} />
            New document
          </button>
        }
      />
      <div className="toolbar">
        <label htmlFor="documentsscreen-1">
          Find document
          <input
            id="documentsscreen-1"
            value={search}
            placeholder="Document title"
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <TagFilter title="Feature tags" tags={featureTags} selected={featureTag} onChange={setFeatureTag} />
        <TagFilter title="Concern tags" tags={concernTags} selected={concernTag} onChange={setConcernTag} />
        <small className="tag-filter-hint">Any tag within a group matches; feature and concern groups apply together.</small>
        <span>{docs.length} {docs.length === 1 ? "document" : "documents"}</span>
        <button ref={importButton} type="button" className="secondary" onClick={() => importInput.current?.click()}>
          <FileUp size={16} /> Import Markdown
        </button>
        <input ref={importInput} id="markdown-import" type="file" accept=".md,.markdown,text/markdown"
          hidden onChange={async (event) => {
            const file = event.currentTarget.files?.[0];
            event.currentTarget.value = "";
            setImportError(""); setImportPreview(null);
            if (!file) return;
            if (file.size > 1_048_576) { setImportError("Markdown files must be 1 MiB or smaller."); return; }
            if (!/\.(md|markdown)$/i.test(file.name)) { setImportError("Choose a Markdown (.md) file."); return; }
            try {
              const source = new TextDecoder("utf-8", { ignoreBOM: true }).decode(await file.arrayBuffer());
              const parsed = parseMarkdown(source, file.name);
              const allTags = [...parsed.featureTags, ...parsed.concernTags];
              const validShape = /^(?:feature|concern):[a-z0-9]+(?:-[a-z0-9]+)*$/;
              const draft = { ...parsed, filename: file.name, unknownTags: [], invalidTags: allTags.filter((tag) => !validShape.test(tag)) };
              setImportPreview(draft);
              setTagCheckError("");
              if (allTags.length) await checkTagCatalog(draft);
            } catch (cause) { setImportError(cause instanceof Error ? cause.message : "This file could not be read as text."); }
          }} />
      </div>
      {importError && <p className="form-error" role="alert">{importError}</p>}
      {importPreview && <section className="import-review" aria-labelledby="import-review-title">
        <div><h2 ref={importHeading} tabIndex={-1} id="import-review-title">Review imported document</h2><p>We filled in details from the file. Review them before importing.</p></div>
        {importPreview.issues.length > 0 && <div className="notice" role="status"><strong>Metadata needs review</strong><ul>{importPreview.issues.map((issue) => <li key={issue}>{issue}</li>)}</ul></div>}
        <div className="import-review-fields">
          <label htmlFor="import-title">Title<input id="import-title" name="title" required maxLength={256} value={importPreview.title} onChange={(event) => updateImport({title:event.target.value})} /><small>{metadataOrigin(importPreview.title, importPreview.fromFile.title, importPreview.titleFromFilename)}</small></label>
          <label htmlFor="import-description">Description<input id="import-description" name="description" maxLength={240} value={importPreview.description} onChange={(event) => updateImport({description:event.target.value})} /><small>{metadataOrigin(importPreview.description, importPreview.fromFile.description)}</small></label>
          <label htmlFor="import-kind">Kind<select id="import-kind" name="kind" value={importPreview.kind || "document"} onChange={(event) => updateImport({kind:event.target.value})}>{documentKinds.map((kind) => <option key={kind}>{kind}</option>)}</select><small>{metadataOrigin(importPreview.kind, importPreview.fromFile.kind)}</small></label>
          <label htmlFor="import-feature-tags">Feature tags<input id="import-feature-tags" name="feature_tags" value={importPreview.featureTags.join(", ")} onChange={(event) => updateImport({featureTags:splitTagInput(event.target.value)})} /><small>{metadataOrigin(importPreview.featureTags.join(", "), importPreview.fromFile.featureTags?.join(", "))}. Separate tags with commas.</small></label>
          <label htmlFor="import-concern-tags">Concern tags<input id="import-concern-tags" name="concern_tags" value={importPreview.concernTags.join(", ")} onChange={(event) => updateImport({concernTags:splitTagInput(event.target.value)})} /><small>{metadataOrigin(importPreview.concernTags.join(", "), importPreview.fromFile.concernTags?.join(", "))}. Separate tags with commas.</small></label>
          <p className="field-note">Source file: {importPreview.filename}</p>
        </div>
        {importPreview.invalidTags.length > 0 && <p className="form-error" role="alert">Invalid tags: {importPreview.invalidTags.join(", ")}. Use a feature: or concern: tag ID.</p>}
        {importPreview.unknownTags.length > 0 && <p className="form-error" role="alert">Unknown project tags: {importPreview.unknownTags.join(", ")}. Correct or remove these tags before importing.</p>}
        {tagCheckError && <p className="form-error" role="alert">Could not verify tags: {tagCheckError} <button type="button" className="text-button" onClick={() => void checkTagCatalog()}>Retry tag check</button></p>}
        {importDuplicate && <p className="notice" role="status">A document with this title or source filename already exists. Continuing creates a separate record; existing documents will not be changed.</p>}
        <p className="field-note">Request size: {importPayloadBytes.toLocaleString()} bytes of 1,048,576 allowed.</p>
        {importPayloadTooLarge && <p className="form-error" role="alert">The reviewed upload request is {importPayloadBytes.toLocaleString()} bytes, above the server's 1,048,576-byte limit. Choose a smaller Markdown file and review it again.</p>}
        <div className="form-footer">
          <button onClick={() => setImportPreview(null)}>Cancel</button>
          <button className="primary" disabled={!importPreview.title.trim() || importPreview.invalidTags.length > 0 || importPreview.unknownTags.length > 0 || importSaving || tagChecking || Boolean(tagCheckError) || importPayloadTooLarge} onClick={async () => {
            const item = importPreview;
            const finalPayload = documentPayload({title:item.title,content:item.content,originalFrontmatter:item.originalFrontmatter,description:item.description,kind:item.kind || "document",featureTags:item.featureTags,concernTags:item.concernTags},"upload",item.filename);
            if (new TextEncoder().encode(JSON.stringify(finalPayload)).byteLength > 1_048_576) {
              setImportError("The reviewed upload request is above the server's 1,048,576-byte limit. Choose a smaller Markdown file and review it again.");
              return;
            }
            setImportSaving(true); setImportError("");
            try { const docId = await saveDocument({title:item.title,content:item.content,originalFrontmatter:item.originalFrontmatter,description:item.description,kind:item.kind || "document",featureTags:item.featureTags,concernTags:item.concernTags},undefined,"upload",item.filename); setImportPreview(null); navigate("/documents/" + docId); }
            catch (cause) { setImportError(cause instanceof Error ? cause.message : "Import failed. Your selected file is retained for retry."); }
            finally { setImportSaving(false); }
          }}>{importSaving ? "Importing…" : tagChecking ? "Checking tags…" : importDuplicate ? "Create separate copy" : "Confirm and import"}</button>
        </div>
        <details><summary>Preview Markdown content</summary><pre>{importPreview.content}</pre></details>
      </section>}
      <StatePanel
        empty={!docs.length}
        title="No documents found"
        action={
          <button
            onClick={() => {
              setCreate(true);
            }}
          >
            Create document
          </button>
        }
      >
        <DocumentList documents={docs} />
      </StatePanel>
      <Modal
        open={create}
        title="Create document"
        onClose={() => {
          if (dirty && !confirm("Discard unsaved document changes?")) return;
          setDirty(false);
          setCreate(false);
        }}
      >
        {create && (
          <DocumentEditor
            onSaved={(id) => {
              setCreate(false);
              navigate("/documents/" + id);
            }}
          />
        )}
      </Modal>
    </>
  );
}

function parseMarkdown(raw: string, filename: string) {
  const issues: string[] = [];
  const values = new Map<string, string | string[]>();
  const bomOffset = raw.startsWith("\uFEFF") ? 1 : 0;
  const sourceAfterBom = raw.slice(bomOffset);
  const opening = /^---[ \t]*\r?\n/.exec(sourceAfterBom);
  let body = raw;
  let originalFrontmatter = "";
  if (!opening) {
    issues.push("No YAML frontmatter found. The filename is used as a title suggestion; review the metadata fields before saving.");
  } else {
    const remainder = sourceAfterBom.slice(opening[0].length);
    const closing = /^---[ \t]*(?:\r?\n|$)/m.exec(remainder);
    if (!closing) {
      issues.push("The YAML frontmatter is missing its closing --- line. The whole file is preserved as document content.");
    } else {
      const frontmatter = remainder.slice(0, closing.index);
      const prefixLength = bomOffset + opening[0].length + closing.index + closing[0].length;
      originalFrontmatter = raw.slice(0, prefixLength);
      body = remainder.slice(closing.index + closing[0].length);
      parseFrontmatter(frontmatter, values, issues);
    }
  }

  const nameValue = firstScalar(values.get("name")) || firstScalar(values.get("title"));
  const descriptionValue = firstScalar(values.get("description"));
  const rawKind = firstScalar(values.get("kind"));
  const rawTags = Array.isArray(values.get("tags")) ? values.get("tags") as string[] : [];
  if (!nameValue) issues.push("Missing name: the filename is used as a title suggestion.");
  if (!descriptionValue) issues.push("Missing description: add one if this document needs a short summary.");
  if (!rawKind) issues.push("Missing kind: choose a document kind before saving.");
  if (!values.has("tags")) issues.push("Missing tags: no project tags will be assigned unless you add them.");
  if (rawKind && normalizeKind(rawKind) !== rawKind.toLowerCase()) {
    issues.push(`Unknown kind “${rawKind}”: it was changed to “document”; choose a valid kind in the review.`);
  }

  const featureTags = rawTags.filter((tag) => !tag.startsWith("concern:"));
  const concernTags = rawTags.filter((tag) => tag.startsWith("concern:"));
  const title = nameValue || filename.replace(/\.(md|markdown)$/i, "");
  return {
    title,
    description: descriptionValue,
    kind: normalizeKind(rawKind || "document"),
    featureTags,
    concernTags,
    content: body,
    originalFrontmatter,
    issues,
    invalidTags: [],
    fromFile: {
      title: nameValue || undefined,
      description: descriptionValue || undefined,
      kind: rawKind ? normalizeKind(rawKind) : undefined,
      featureTags: values.has("tags") ? featureTags : undefined,
      concernTags: values.has("tags") ? concernTags : undefined,
    },
    titleFromFilename: !nameValue,
  };
}

function parseFrontmatter(source: string, values: Map<string, string | string[]>, issues: string[]) {
  const lines = source.split(/\r?\n/);
  const supported = new Set(["name", "title", "description", "kind", "tags"]);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (!line.trim() || /^\s*#/.test(line)) continue;
    const entry = /^([A-Za-z][\w-]*)\s*:\s*(.*)$/.exec(line);
    if (!entry) {
      issues.push(`Frontmatter line ${index + 1} could not be read. Correct the supported fields below.`);
      continue;
    }
    const key = entry[1].toLowerCase();
    const rawValue = entry[2];
    if (values.has(key)) {
      issues.push(`Frontmatter contains duplicate “${key}” fields; the first value is used.`);
      continue;
    }
    if (!supported.has(key)) {
      issues.push(`Frontmatter field “${key}” is not imported. Only name, description, kind and tags are used.`);
      continue;
    }
    try {
      if (key === "tags") {
        if (rawValue.trim().startsWith("[")) {
          const list = rawValue.trim();
          if (!list.endsWith("]")) throw new Error("Unclosed tags list");
          values.set(key, splitYamlList(list.slice(1, -1)).map(parseYamlScalar).filter(Boolean));
        } else if (!rawValue.trim()) {
          const tags: string[] = [];
          let next = index + 1;
          while (next < lines.length && /^\s+-\s*/.test(lines[next])) {
            tags.push(parseYamlScalar(lines[next].replace(/^\s+-\s*/, "")));
            next += 1;
          }
          values.set(key, tags.filter(Boolean));
          index = next - 1;
        } else {
          values.set(key, [parseYamlScalar(rawValue)].filter(Boolean));
        }
      } else {
        if (/^[|>][+-]?$/.test(rawValue.trim())) {
          const blockLines: string[] = [];
          let next = index + 1;
          while (next < lines.length && (!lines[next].trim() || /^\s+/.test(lines[next]))) {
            blockLines.push(lines[next].trim() ? lines[next].trim() : "");
            next += 1;
          }
          const folded = rawValue.trim().startsWith(">");
          const blockValue = folded
            ? blockLines.join("\n").replace(/([^\n])\n(?!\n)/g, "$1 ").replace(/\n{3,}/g, "\n\n").replace(/\n+$/, "")
            : blockLines.join("\n").replace(/\n+$/, "");
          values.set(key, blockValue);
          index = next - 1;
        } else {
          values.set(key, parseYamlScalar(rawValue));
        }
      }
    } catch {
      issues.push(`Frontmatter field “${key}” has invalid YAML syntax. Correct the value in the review.`);
    }
  }
}

function splitYamlList(value: string) {
  const parts: string[] = [];
  let quote = "";
  let escaped = false;
  let start = 0;
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (escaped) { escaped = false; continue; }
    if (character === "\\" && quote === '"') { escaped = true; continue; }
    if ((character === "'" || character === '"') && (!quote || quote === character)) { quote = quote ? "" : character; continue; }
    if (character === "," && !quote) { parts.push(value.slice(start, index).trim()); start = index + 1; }
  }
  if (quote) throw new Error("Unclosed quoted list value");
  if (value.slice(start).trim()) parts.push(value.slice(start).trim());
  return parts;
}

function parseYamlScalar(input: string) {
  const value = input.trim().replace(/\s+#.*$/, "").trim();
  if (!value) return "";
  if (value.startsWith('"')) {
    const parsed: unknown = JSON.parse(value);
    if (typeof parsed !== "string") throw new Error("Expected a text value");
    return parsed;
  }
  if (value.startsWith("'")) {
    if (!value.endsWith("'") || value.length < 2) throw new Error("Unclosed single-quoted value");
    return value.slice(1, -1).replace(/''/g, "'");
  }
  return value;
}

function firstScalar(value: string | string[] | undefined) {
  return typeof value === "string" ? value.trim() : "";
}

function metadataOrigin(value: string, original: string | undefined, fromFilename = false) {
  if (fromFilename && value) return "Suggested from filename";
  if (original === undefined) return value ? "Added by you" : "Not provided by file";
  return value === original ? "Source-provided" : "Edited by you";
}
function splitTagInput(value: string) {
  return [...new Set(value.split(",").map((tag) => tag.trim()).filter(Boolean))];
}
