#!/usr/bin/env python3
"""Structure-only validator for AgentBuild local project artifacts.

Does NOT verify AgentBoard records, human approval, business facts or the
semantic quality of architecture/design documents.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

STATES = {"not_started", "draft", "in_review", "approved", "blocked", "superseded"}
REQUIRED_HEADINGS = {
    "vision": ["Product Overview", "PainPoints", "Features & Value Proposition"],
    "stories": [],
    "architecture": ["Environment & Constraints", "High-Level System Architecture", "Technology & SDK Decisions", "Data & Storage Design", "Frontend Folder Structure", "Backend Folder Structure", "Security & Nonfunctional Requirements", "Architectural Decisions"],
    "design": ["Design Direction", "Design Principles", "Information Architecture & Navigation", "Visual Hierarchy & Information Density", "Progressive Disclosure", "Color Palette & Semantic Roles", "Typography", "Layout, Spacing & Responsiveness", "Components & Interaction States", "Accessibility", "Screen Inventory & Story Mapping"],
    "review": ["Scope & Evidence", "Verdict", "Findings", "Traceability & Coverage"],
}


def validate_vision_format(text: str) -> list[str]:
    errors = []
    sections = re.split(r"^## +(.+?)\s*$", text, flags=re.MULTILINE)
    if sections[1::2] != REQUIRED_HEADINGS["vision"]:
        return ["vision: use exactly Product Overview, PainPoints, Features & Value Proposition"]
    overview, pains, features = [part.strip() for part in sections[2::2]]
    if not overview or len(re.split(r"\n\s*\n", overview)) != 1 or re.search(r"^\s*(?:#|[-*+] |\|)", overview, re.MULTILINE):
        errors.append("vision: Product Overview must be one prose paragraph")
    bullet = re.compile(r"^[-*+] +\S")
    pain_lines = [line for line in pains.splitlines() if line.strip()]
    if not pain_lines or any(not bullet.match(line) for line in pain_lines):
        errors.append("vision: PainPoints must contain bullet points")
    count = 0
    values = 0
    for line in features.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"\*\*[^*]+\*\*", line):
            if count and not values:
                errors.append("vision: each feature needs value bullets")
            count += 1
            values = 0
        elif bullet.match(line) and count:
            values += 1
        else:
            errors.append("vision: use a bold feature line followed by value bullets; no tables")
    if not count or not values:
        errors.append("vision: each feature needs value bullets")
    return errors


def strip_frontmatter(text: str) -> str:
    """Remove a leading metadata-only YAML block before validating Markdown body shape."""
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text[end + 5:] if end >= 0 else text


def validate_stories_format(text: str, vision_features: set[str] | None = None) -> list[str]:
    text = strip_frontmatter(text)
    errors = []
    parts = re.split(r"^### +(US-\d{3,}[^\n]*)\n", text, flags=re.MULTILINE)
    if len(parts) == 1:
        return ["stories: no US-### story details found"]
    if re.search(r"^#{2} ", text, re.MULTILINE):
        errors.append("stories: include only story details, without index or scope sections")
    preamble = [line for line in parts[0].splitlines() if line.strip()]
    if any(not line.startswith(("# ", "> ")) for line in preamble):
        errors.append("stories: only document title and metadata may precede details")
    expected = ["Story", "Acceptance Criteria", "Associated Features"]
    for title, body in zip(parts[1::2], parts[2::2]):
        fields = re.split(r"^- \*\*([^*]+):\*\*\s*\n", body, flags=re.MULTILINE)
        if fields[1::2] != expected or fields[0].strip():
            errors.append(f"stories: {title} must contain only the three required fields in order")
            continue
        for name, content in zip(fields[1::2], fields[2::2]):
            lines = [line for line in content.splitlines() if line.strip()]
            if not lines or any(not re.match(r"^  - \S", line) for line in lines):
                errors.append(f"stories: {title} {name} must contain nested bullets")
            if name == "Story" and len(lines) != 1:
                errors.append(f"stories: {title} needs one story description")
            if name == "Associated Features" and vision_features is not None:
                for line in lines:
                    if line.removeprefix("  - ").strip() not in vision_features:
                        errors.append(f"stories: {title} references a feature absent from Product Vision")
    return errors


def validate_folder(project: Path, folder: Path, kind: str, features: set[str] | None = None) -> list[str]:
    """Check ordinary Markdown files and navigation; no generated store."""
    from urllib.parse import unquote
    errors=[]
    docs=(project/'docs').resolve()
    if folder.is_symlink() or not folder.is_dir(): return [f'{kind}: unsafe/missing folder']
    readme=folder/'README.md'
    if not readme.is_file() or readme.is_symlink(): return [f'{kind}: missing regular README.md']
    files=sorted(folder.rglob('*'))
    markdown=[];ids=[];linked=set();graph={}
    for file in files:
        if kind=='design' and file.relative_to(folder).parts[0] in ('mockups','screens'):
            continue  # Isolated proposals are not authoritative design topics.
        if file.is_symlink():
            errors.append(f'{kind}: symlink not allowed: {file.name}')
            continue
        if not file.is_file() or file.suffix.lower()!='.md': continue
        text=file.read_text(encoding='utf-8');markdown.append((file,text));graph[file.resolve()]=set()
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'): continue
            path=unquote(target.split('#',1)[0])
            resolved=(file.parent/path).resolve()
            if not resolved.is_relative_to(docs) or not resolved.is_file():
                errors.append(f'{kind}: broken/escaping link {target} in {file.name}')
            else: graph[file.resolve()].add(resolved)
        if file==readme: continue
        if kind=='stories':
            found=re.findall(r'^### (US-\d{3,})\b',text,re.MULTILINE)
            ids.extend(found)
            if len(found)!=1: errors.append(f'stories: {file.name} must contain one story')
            elif not file.name.startswith(found[0]+'-'):
                errors.append(f'stories: filename does not match story ID: {file.name}')
            errors.extend(validate_stories_format(text,features))
    frontier=[readme.resolve()]
    while frontier:
        current=frontier.pop()
        for target in graph.get(current,set()):
            if target not in linked: linked.add(target);frontier.append(target)
    for file,_ in markdown:
        if file!=readme and file.resolve() not in linked:
            errors.append(f'{kind}: README navigation cannot reach {file.name}')
    if kind=='stories':
        if not ids: errors.append('stories: folder has no stories')
        if len(ids)!=len(set(ids)): errors.append('stories: duplicate story IDs across files')
    if kind=='design':
        for name in ('navigation-layout.md','visual-system.md','accessibility.md','interaction-states.md'):
            if not (folder/name).is_file(): errors.append(f'design: missing core topic {name}')
        known=set()
        for story in (project/'docs/user-stories').glob('US-*.md'):
            known.update(re.findall(r'^### (US-\d{3,})\b',story.read_text(),re.MULTILINE))
        for file,text in markdown:
            if file.name=='design-profile.md': errors.append('design: archive the monolith outside the active designs folder')
            visible=re.sub(r'```.*?```','',strip_frontmatter(text),flags=re.DOTALL)
            limit=250 if file==readme else 450
            if len(visible.split())>limit: errors.append(f'design: keep {file.name} concise (maximum {limit} words); split by concern')
            for field in ('Owner:','Version:','Status:','Last Updated:'):
                if field not in text[:1000]: errors.append(f'design: {file.name} missing {field}')
            if file==readme: continue
            for field in ('Purpose','Related stories','Required context'):
                if not re.search(r'\*\*'+field+r':\*\*\s*\S',text): errors.append(f'design: {file.name} missing {field}')
            for story_id in set(re.findall(r'\bUS-\d{3,}\b',text)):
                if story_id not in known: errors.append(f'design: {file.name} references unknown story {story_id}')
    if kind=='architecture' and (folder/'document-plan.json').exists():
        from architecture_documents import validate_documents
        errors.extend(validate_documents(folder,project))
    elif kind=='architecture':
        if (folder/'contracts/manifest.json').is_file():
            from validate_contracts import validate
            errors.extend(validate(folder))
        combined='\n'.join(text for _,text in markdown)
        headings=re.findall(r'^#{1,4}\s+(.+)$',combined,re.MULTILINE)
        for required in REQUIRED_HEADINGS['architecture']:
            if not any(required.casefold() in heading.casefold() for heading in headings):
                errors.append(f'architecture: missing section {required}')
    return errors


def inspect_project(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    project = project.expanduser().resolve()
    manifest = project / "project-manifest.json"
    if not manifest.is_file():
        return [f"Missing manifest: {manifest}"], warnings
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Invalid manifest JSON: {exc}"], warnings

    info = data.get("project")
    if not isinstance(info, dict) or not isinstance(info.get("name"), str) or not info["name"].strip():
        errors.append("project.name must be a nonempty string")
    else:
        if info.get("agentboard_project_id") is None and info.get("sync_state") == "synced":
            errors.append("sync_state='synced' without a confirmed agentboard_project_id")
        if data.get("schema_version") == "2.0":
            mode = info.get("storage_mode")
            if mode not in {"local", "agentboard", "hybrid"}:
                errors.append(f"Unrecognized storage_mode {mode!r}")
            if mode == "local" and info.get("sync_state") not in {"local_only", "pending_sync"}:
                errors.append("Local mode needs sync_state='local_only' (or explicitly configured pending_sync)")
            if mode == "local" and info.get("local_storage_confirmed") is not True:
                warnings.append("Local project has no recorded user consent; do not write until approved")
            if mode == "local" and not (project / "docs").is_dir():
                errors.append("Local project is missing docs/ directory")
            if (project / "docs").is_symlink():
                errors.append("Local project docs/ cannot be a symlink")
            agents = data.get("agents")
            if mode == "local" and not isinstance(agents, dict):
                errors.append("Local project requires agents metadata")
            elif mode == "local":
                for role in ("product-manager", "product-designer", "solution-architect", "backend-programmer", "frontend-programmer", "code-reviewer"):
                    role_data = agents.get(role, {})
                    role_path = f"agents/{role}.md"
                    path = project / role_path
                    if role_data.get("local_role_path") != role_path or not path.is_file() or path.is_symlink():
                        errors.append(f"Missing/inconsistent local role: {role_path}")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        return errors + ["artifacts must be a nonempty object"], warnings

    for key, item in artifacts.items():
        if not isinstance(item, dict):
            errors.append(f"{key}: artifact metadata must be an object")
            continue
        state = item.get("state")
        if state not in STATES:
            errors.append(f"{key}: unrecognized state: {state!r}")
        path_str = item.get("path")
        if not isinstance(path_str, str) or not path_str:
            errors.append(f"{key}: missing artifact path")
            continue
        normalized = path_str.replace("\\", "/")
        rel = PurePosixPath(normalized)
        if rel.is_absolute() or any(p in ("..", ".") for p in rel.parts) or not normalized.startswith("docs/"):
            errors.append(f"{key}: artifact path must stay under docs/: {path_str!r}")
            continue
        target = project / normalized
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != project.parent and project in parent.parents):
            errors.append(f"{key}: symlink artifact path not permitted by local validator")
            continue
        if state in ("draft", "in_review", "approved") and not target.is_file():
            if item.get("agentboard_document_id"):
                warnings.append(f"{key}: remote-only document; local contents not validated")
            else:
                errors.append(f"{key}: state={state} but local file missing: {path_str}")
            continue
        if not target.exists():
            continue
        if not target.is_file():
            errors.append(f"{key}: artifact path is not a regular file")
            continue
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{key}: cannot read UTF-8: {exc}")
            continue
        if not text.strip():
            errors.append(f"{key}: empty document")
            continue
        folder_layout = item.get('layout') == 'folder' and key in ('stories','architecture','design')
        if folder_layout:
            if target.name != 'README.md':
                errors.append(f'{key}: folder artifact must point to README.md')
            vision_item = artifacts.get('vision', {})
            vision_rel = vision_item.get('path', 'docs/product-vision.md')
            features = None
            if isinstance(vision_rel, str) and vision_rel.startswith('docs/') and '..' not in PurePosixPath(vision_rel).parts:
                vision_file = project / vision_rel
                if vision_file.is_file() and not vision_file.is_symlink():
                    features=set(re.findall(r'^\*\*([^*]+)\*\*$',vision_file.read_text(),re.MULTILINE))
            errors.extend(validate_folder(project,target.parent,key,features))
        if key in REQUIRED_HEADINGS:
            version_match = re.search(r"\bVersion:\s*([^|\n]+)", text[:1000])
            status_match = re.search(r"\bStatus:\s*([^|\n]+)", text[:1000])
            if version_match and version_match.group(1).strip() != (item.get("version") or ""):
                warnings.append(f"{key}: document version differs from manifest")
            if status_match and status_match.group(1).strip() != state:
                warnings.append(f"{key}: document status differs from manifest")
            headings = re.findall(r"^#{1,4}\s+(.+)$", text, re.MULTILINE)
            for required in ([] if folder_layout else REQUIRED_HEADINGS[key]):
                if not any(required.casefold() in heading.casefold() for heading in headings):
                    errors.append(f"{key}: missing section '{required}'")
            for metadata in ("Owner:", "Version:", "Status:", "Last Updated:"):
                if metadata not in text[:1000]:
                    errors.append(f"{key}: missing metadata '{metadata}'")
        if key == "vision":
            errors.extend(validate_vision_format(text))
        if key == "stories" and not folder_layout:
            vision_item = artifacts.get("vision", {})
            vision_path = vision_item.get("path", "docs/product-vision.md")
            features = None
            if isinstance(vision_path, str) and vision_path.startswith("docs/") and ".." not in PurePosixPath(vision_path).parts:
                source = project / vision_path
                if source.is_file() and not source.is_symlink():
                    vision_text = source.read_text(encoding="utf-8")
                    features = set(re.findall(r"^\*\*([^*]+)\*\*$", vision_text, re.MULTILINE))
            if features is None:
                warnings.append("stories: Vision features unavailable for association validation")
            errors.extend(validate_stories_format(text, features))
            ids = re.findall(r"^###\s+(US-\d{3,})\b", text, re.MULTILINE)
            if len(ids) != len(set(ids)):
                errors.append("stories: duplicate detailed story IDs")
            if not ids:
                warnings.append("stories: no detailed US-### headings found")
        if key in ("architecture-svg",) or target.suffix.lower() == ".svg":
            try:
                root = ET.fromstring(text)
                if root.tag.rsplit("}", 1)[-1] != "svg":
                    errors.append(f"{key}: XML root is not <svg>")
                if len(list(root.iter())) < 5:
                    warnings.append(f"{key}: SVG may be too sparse for a system architecture")
                if "TEMPLATE" in text or "Replace with real role" in text:
                    errors.append(f"{key}: placeholder architecture diagram is not a deliverable")
            except ET.ParseError as exc:
                errors.append(f"{key}: malformed SVG: {exc}")
        if key == "tokens" or target.suffix.lower() == ".json":
            try:
                tokens = json.loads(text)
                if key == "tokens":
                    for required in ("color", "typography", "spacingPx"):
                        if required not in tokens:
                            errors.append(f"tokens: missing '{required}'")
            except ValueError as exc:
                errors.append(f"{key}: invalid JSON: {exc}")
        if state == "approved" and re.search(r"<ProjectName>|<YYYY-MM-DD>|<version>|\bTBD\b", text, re.IGNORECASE):
            errors.append(f"{key}: approved artifact still contains unresolved template placeholders")
        if state in ("draft", "in_review") and ("<ProjectName>" in text or "<YYYY-MM-DD>" in text):
            warnings.append(f"{key}: draft contains template placeholders")
        for dependency in item.get("depends_on", []):
            if dependency not in artifacts:
                errors.append(f"{key}: unrecognized dependency artifact {dependency!r}")
        if state in ("draft", "in_review", "approved") and not item.get("version"):
            errors.append(f"{key}: state={state} requires version metadata in manifest")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="Project folder with project-manifest.json")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable report")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failures")
    args = parser.parse_args()
    errors, warnings = inspect_project(args.project)
    if args.json:
        print(json.dumps({"valid": not errors and (not args.strict or not warnings), "errors": errors, "warnings": warnings}, indent=2))
    else:
        for issue in errors:
            print("ERROR:", issue)
        for issue in warnings:
            print("WARN: ", issue)
        print(f"Project validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
