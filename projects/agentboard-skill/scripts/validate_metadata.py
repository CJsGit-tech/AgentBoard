#!/usr/bin/env python3
"""Validate project Markdown metadata frontmatter and controlled tags."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKIP_PARTS = {"history", "evidence", "reviews", "review", "archive", "archives"}
EXPECTED_FIELDS = {"name", "description", "kind", "tags"}


def parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, text, "missing YAML frontmatter"
    end = re.search(r"(?m)^---\s*$", text[4:])
    if not end:
        return None, text, "unterminated YAML frontmatter"
    stop = end.end() + 4
    raw = text[4:end.start() + 4]
    data = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(": ")
        if not sep or not key or key in data:
            return None, text, f"invalid or duplicate metadata field: {line!r}"
        try:
            data[key] = json.loads(value)
        except json.JSONDecodeError:
            return None, text, f"metadata value for {key!r} must use the simple JSON-compatible YAML form"
    body = text[stop:]
    if body.startswith("\n"):
        body = body[1:]
    return data, body, None


def canonical_markdown(docs: Path):
    for path in sorted(docs.rglob("*.md")):
        rel = path.relative_to(docs)
        if any(part.casefold() in SKIP_PARTS for part in rel.parts):
            continue
        yield path


def validate(project: Path) -> list[str]:
    project = Path(project).expanduser().resolve()
    docs = project / "docs"
    if not docs.is_dir():
        return []
    catalog_path = docs / "tag-vocabulary.json"
    # Older projects remain supported until they adopt the metadata catalog.
    if not catalog_path.is_file():
        return []
    errors = []
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"metadata: invalid tag-vocabulary.json: {exc}"]
    if catalog.get("schema_version") != 1:
        errors.append("metadata: unsupported tag vocabulary schema_version")
    features = catalog.get("features", [])
    concerns = catalog.get("concerns", [])
    kinds = catalog.get("kinds", [])
    def ids(rows, group):
        found=[]
        if not isinstance(rows,list):
            errors.append(f"metadata: {group} must be a list")
            return found
        for row in rows:
            if not isinstance(row,dict) or not isinstance(row.get("id"),str):
                errors.append(f"metadata: malformed {group} entry")
            else:
                found.append(row["id"])
        if len(found)!=len(set(found)): errors.append(f"metadata: duplicate IDs in {group}")
        return found
    feature_ids=ids(features,"features")
    concern_ids=ids(concerns,"concerns")
    allowed=set(feature_ids+concern_ids)
    if any(not x.startswith("feature:") for x in feature_ids): errors.append("metadata: feature IDs must start with feature:")
    if any(not x.startswith("concern:") for x in concern_ids): errors.append("metadata: concern IDs must start with concern:")
    if not isinstance(kinds,list) or not kinds or any(not isinstance(x,str) for x in kinds):
        errors.append("metadata: kinds must be a nonempty list of strings")
        kinds=[]
    if len(kinds)!=len(set(kinds)): errors.append("metadata: duplicate kinds")

    vision = docs / "product-vision.md"
    if vision.is_file():
        _, body, err = parse_frontmatter(vision.read_text(encoding="utf-8"))
        labels = set(re.findall(r"^\*\*([^*]+)\*\*$", body, re.M))
        catalog_labels = {r.get("label") for r in features if isinstance(r,dict)}
        if labels != catalog_labels:
            errors.append("metadata: feature catalog labels must match Product Vision feature names")
        def slug(value): return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
        for row in features:
            if isinstance(row,dict) and isinstance(row.get("label"),str) and row.get("id") != "feature:"+slug(row["label"]):
                errors.append(f"metadata: feature ID does not match Vision label {row['label']!r}")

    count=0
    for path in canonical_markdown(docs):
        label="metadata: "+path.relative_to(project).as_posix()
        if path.is_symlink():
            errors.append(label+": symlink is not allowed")
            continue
        text=path.read_text(encoding="utf-8")
        data,body,err=parse_frontmatter(text)
        if err:
            errors.append(label+": "+err)
            continue
        count+=1
        if set(data)!=EXPECTED_FIELDS:
            errors.append(label+f": expected fields {sorted(EXPECTED_FIELDS)}, got {sorted(data)}")
            continue
        if not isinstance(data["name"],str) or not data["name"].strip(): errors.append(label+": name must be nonempty text")
        if not isinstance(data["description"],str) or not data["description"].strip() or "\n" in data["description"] or len(data["description"])>240:
            errors.append(label+": description must be one nonempty sentence of at most 240 characters")
        if data["kind"] not in kinds: errors.append(label+f": unknown kind {data['kind']!r}")
        title=re.search(r"(?m)^#{1,3}\s+(.+?)\s*$",body)
        if title and data["name"]!=title.group(1): errors.append(label+": name must match the first Markdown heading")
        tags=data["tags"]
        if not isinstance(tags,list) or any(not isinstance(tag,str) for tag in tags):
            errors.append(label+": tags must be a list of tag IDs")
            continue
        if not tags and "AGENTBUILD:SKELETON" not in body:
            errors.append(label+": authored documents need at least one relevant retrieval tag")
        if len(tags)!=len(set(tags)): errors.append(label+": tags must not repeat")
        unknown=[tag for tag in tags if tag not in allowed]
        if unknown: errors.append(label+": unknown tags "+", ".join(unknown))

        if path.parent.name=="user-stories" and path.name.startswith("US-"):
            match=re.search(r"(?ms)^- \*\*Associated Features:\*\*\s*\n((?:  - .*\n?)+)",body)
            if match:
                by_label={row["label"]:row["id"] for row in features if isinstance(row,dict) and "label" in row}
                expected={by_label[x] for x in re.findall(r"^  - (.+)$",match.group(1),re.M) if x in by_label}
                actual={tag for tag in tags if tag.startswith("feature:")}
                if actual!=expected: errors.append(label+": feature tags must match Associated Features")
    if count==0: errors.append("metadata: no canonical Markdown documents found")
    return errors


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,required=True)
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args()
    issues=validate(args.project)
    if args.json: print(json.dumps({"valid":not issues,"errors":issues},indent=2))
    else:
        for issue in issues: print("ERROR: "+issue)
        print("Metadata consistency: "+("FAIL" if issues else "PASS"))
    raise SystemExit(bool(issues))
