"""Project vocabulary shared by board edits and agent calls."""
import re

TAG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
CORE = {
    ("product-vision", "product brief"): "Product Brief",
    ("product-vision", "product vision"): "Product Brief",
    ("architecture-topic", "technical stack"): "Technical Stack",
    ("architecture-topic", "tech stack"): "Technical Stack",
    ("design-canvas", "design canvas"): "Design Canvas",
    ("design-topic", "design profile"): "Design Profile",
    ("unclassified", "tag catalog"): "Tag Catalog",
}


def core_name(data):
    return CORE.get((data.get("document_type", "unclassified"), data["name"].strip().lower()))


def entries(content):
    result = {}
    for section in re.split(r"(?m)^## ", content)[1:]:
        lines = section.splitlines()
        key = lines[0].strip() if lines else ""
        states = [line.removeprefix("State: ").strip() for line in lines if line.startswith("State: ")]
        if len(key) > 120 or not re.fullmatch(TAG, key) or key in result or states not in (["Active"], ["Retired"]):
            raise ValueError("Give each catalog entry a unique tag ID and one Active or Retired state.")
        result[key] = states[0]
    return result


def check_catalog(conn, kind, data, old, key):
    if kind not in ("documents", "tickets"):
        return
    name = core_name(data) if kind == "documents" else None
    added = set(data.get("tags", [])) - set(old.get("tags", []))
    if not (name or added):
        return
    rows = conn.execute("SELECT id,data FROM records WHERE kind='documents' AND project=%s AND NOT deleted",
                        (data["project"],)).fetchall()
    if name and any(row["id"] != key and core_name(row["data"]) == name for row in rows):
        if not old or core_name(old) != name:
            raise ValueError(f"The project already contains {name}. Reuse the existing document.")
    if name == "Tag Catalog":
        new = entries(data["content"])
        if old and core_name(old) == name:
            removed = entries(old["content"]).keys() - new.keys()
            if removed:
                raise ValueError("Retire existing tag IDs to keep historical assignments searchable.")
    if added:
        catalogs = [row for row in rows if core_name(row["data"]) == "Tag Catalog"]
        if len(catalogs) != 1:
            raise ValueError("Choose one Tag Catalog in this project before assigning tags.")
        vocabulary = entries(catalogs[0]["data"]["content"])
        invalid = sorted(tag for tag in added if vocabulary.get(tag) != "Active")
        if invalid:
            raise ValueError("Choose active catalog tags: " + ", ".join(invalid))
