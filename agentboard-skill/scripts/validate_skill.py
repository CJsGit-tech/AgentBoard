#!/usr/bin/env python3
"""Check the AgentBuild skill bundle is structurally complete and portable."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ["help", "setup", "vision-document", "user-stories", "technical-documents", "design-profile", "create-screens", "create-tickets", "update", "status", "review"]
ROLES = ["product-manager", "product-designer", "solution-architect", "backend-programmer", "frontend-programmer", "code-reviewer"]
TEMPLATES = ["product-vision.md", "user-stories.md", "user-story.md", "technical-architecture.md", "system-architecture.svg", "design-profile.md", "design-topic.md", "design-tokens.json", "project-manifest.json", "review-report.md", "ticket.md", "mcp-index.md", "tag-vocabulary.json"]
CONTRACT_HEADINGS = ["Purpose", "Preconditions", "Owner", "Required context", "Execution", "Output artifacts", "Acceptance checks", "Persistence updates", "Failure handling"]


def validate(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return ["Missing SKILL.md"]
    content = skill.read_text(encoding="utf-8")
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        issues.append("SKILL.md needs valid-looking YAML frontmatter delimiters")
    else:
        metadata = content.split("---", 2)[1]
        if "name: agentbuild" not in metadata:
            issues.append("SKILL.md name is not agentbuild")
        if "description:" not in metadata:
            issues.append("SKILL.md missing description")
    if "local" not in content.lower() or "ask" not in content.lower() or "--user-approved-local" not in content:
        issues.append("SKILL.md must mandate explicit confirmation before local fallback")
    if not (root / "references/concise-design-documents.md").is_file():
        issues.append("Missing concise design document rules")
    for reference in sorted(set(re.findall(r'\b(?:commands|references|assets|scripts|roles)/[A-Za-z0-9_./-]+\.(?:md|py|json|svg|txt)\b', content))):
        path = root/reference
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            issues.append('Missing/unsafe entrypoint reference: '+reference)
    for command in COMMANDS:
        file = root / "commands" / f"{command}.md"
        if not file.is_file():
            issues.append(f"Missing command: {command}")
            continue
        text = file.read_text(encoding="utf-8")
        for heading in CONTRACT_HEADINGS:
            if f"## {heading}" not in text:
                issues.append(f"{command}: missing contract heading: {heading}")
    for role in ROLES:
        file = root / "roles" / f"{role}.md"
        if not file.is_file() or file.stat().st_size < 100:
            issues.append(f"Missing/incomplete role: {role}")
    for template in TEMPLATES:
        file = root / "assets" / "templates" / template
        if not file.is_file() or file.stat().st_size == 0:
            issues.append(f"Missing/incomplete template: {template}")
    for template in ("product-vision.md", "user-stories.md", "user-story.md", "design-profile.md", "design-topic.md", "ticket.md", "mcp-index.md"):
        content = (root / "assets" / "templates" / template).read_text(encoding="utf-8")
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            issues.append(f"Artifact template needs YAML metadata frontmatter: {template}")
    for template in ("design-tokens.json", "project-manifest.json", "tag-vocabulary.json"):
        try:
            json.loads((root / "assets" / "templates" / template).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            issues.append(f"Invalid JSON in {template}: {exc}")
    try:
        manifest_template = json.loads((root / "assets/templates/project-manifest.json").read_text(encoding="utf-8"))
        vocabulary_artifact = manifest_template.get("artifacts", {}).get("tag-vocabulary", {})
        if vocabulary_artifact.get("path") != "docs/tag-vocabulary.json":
            issues.append("Project manifest template must track docs/tag-vocabulary.json")
    except (OSError, ValueError, AttributeError) as exc:
        issues.append(f"Invalid tag-vocabulary manifest entry: {exc}")
    try:
        el = ET.parse(root / "assets" / "templates" / "system-architecture.svg").getroot()
        if el.tag.rsplit("}", 1)[-1] != "svg":
            issues.append("Architecture template root must be SVG")
    except (ET.ParseError, OSError) as exc:
        issues.append(f"Invalid architecture SVG template: {exc}")
    for path in ("references/behavior-evaluations.md", "references/tickets.md", "scripts/check_tickets.py", "references/modern-web-guidance.md", "references/screen-verification.md", "scripts/check_screen_evidence.py", "references/create-screens.md", "references/output-consistency.md", "scripts/check_outputs.py", "scripts/sync_navigation.py", "assets/templates/mcp-index.md", "references/contracts-and-examples.md", "scripts/validate_contracts.py", "requirements-contracts.txt", "references/architecture-document-profiles.md", "assets/architecture-documents.json", "scripts/architecture_documents.py", "references/document-folders.md", "references/architecture-discovery.md", "assets/references/system-architecture-modules.svg", "references/agentboard-integration.md", "references/local-workspace.md", "references/quality-gates.md", "references/document-lifecycle.md", "references/command-contract.md", "references/delegation-policy.md", "scripts/scaffold_project.py", "scripts/save_artifact.py", "scripts/validate_project.py", "references/artifact-metadata.md", "scripts/validate_metadata.py", "assets/templates/tag-vocabulary.json"):
        if not (root / path).is_file():
            issues.append(f"Missing supporting file: {path}")
    try:
        catalog = json.loads((root / "assets/architecture-documents.json").read_text(encoding="utf-8"))
        if catalog.get("schema_version") != 1 or set(catalog.get("profiles", {})) != {"web", "ios"}:
            issues.append("Architecture catalog needs web and ios profiles")
        documents = list(catalog.get("core", {}).values())
        for profile in catalog.get("profiles", {}).values():
            documents.extend(profile.values())
        documents.extend(item["document"] for item in catalog.get("optional", {}).values())
        if not documents or any(not d.get("headings") or set(d["headings"]) != set(d.get("prompts", {})) for d in documents):
            issues.append("Architecture catalog document contracts are incomplete")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(f"Invalid architecture catalog: {exc}")
    other_skill_files = [p.relative_to(root) for p in root.rglob("*.md") if p.name.casefold() == "skill.md" and p != skill]
    if other_skill_files:
        issues.append(f"Skill bundle must have exactly one SKILL.md: {other_skill_files}")
    return issues


if __name__ == "__main__":
    found = validate()
    if found:
        print("AgentBuild skill validation FAILED:")
        for issue in found:
            print("-", issue)
        sys.exit(1)
    print("AgentBuild skill validation PASSED")
