"""Load and bundle the checked-in MCP tool contracts for discovery/validation."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


_HERE = Path(__file__).resolve()
_CONTRACT_CANDIDATES = (
    _HERE.parents[2] / "contracts",
    _HERE.parents[3] / "docs/technical-architecture/contracts",
)
CONTRACTS = next((path for path in _CONTRACT_CANDIDATES if (path / "mcp/tools.json").is_file()), None)
if CONTRACTS is None:
    raise RuntimeError("AgentBoard MCP contracts are missing from the runtime image")
DOMAIN = json.loads((CONTRACTS / "schemas/domain.schema.json").read_text(encoding="utf-8"))["$defs"]
CATALOG = json.loads((CONTRACTS / "mcp/tools.json").read_text(encoding="utf-8"))["tools"]


def _localize(value: Any) -> Any:
    if isinstance(value, list):
        return [_localize(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str) and child.startswith("../schemas/domain.schema.json#/"):
                result[key] = "#" + child.split("#", 1)[1]
            else:
                result[key] = _localize(child)
        return result
    return value


def _references(value: Any):
    if isinstance(value, list):
        for item in value:
            yield from _references(item)
    elif isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str) and child.startswith("#/$defs/"):
                yield child.removeprefix("#/$defs/").split("/", 1)[0]
            else:
                yield from _references(child)


def _bundled(value: dict[str, Any]) -> dict[str, Any]:
    schema = _localize(value)
    definitions = {}
    stack = list(_references(schema))
    while stack:
        name = stack.pop()
        if name in definitions:
            continue
        definition = _localize(DOMAIN[name])
        definitions[name] = definition
        stack.extend(_references(definition))
    if definitions:
        schema["$defs"] = definitions
    return schema


def _load_tool(entry: dict[str, Any]) -> dict[str, Any]:
    filename = entry["inputSchema"]["$ref"].split("#", 1)[0]
    path = CONTRACTS / "mcp" / filename
    contract = json.loads(path.read_text(encoding="utf-8"))
    input_schema = _bundled(contract["$defs"]["input"])
    output_schema = _bundled(contract["$defs"]["output"])
    return {
        "name": entry["name"],
        "description": entry["description"],
        "inputSchema": input_schema,
        "outputSchema": output_schema,
        "annotations": entry.get("annotations", {}),
        "permission": entry.get("x-agentbuild-permission", "read"),
        "input_validator": Draft202012Validator(input_schema, format_checker=FormatChecker()),
        "output_validator": Draft202012Validator(output_schema, format_checker=FormatChecker()),
    }


TOOLS = {entry["name"]: _load_tool(entry) for entry in CATALOG}
