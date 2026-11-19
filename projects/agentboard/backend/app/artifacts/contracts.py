import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from app.api.errors import ApiError


local_schema = Path(__file__).resolve().parents[2] / "contracts/schemas/domain.schema.json"
schema_path = local_schema if local_schema.exists() else (
    Path(__file__).resolve().parents[3] / "docs/technical-architecture/contracts/schemas/domain.schema.json"
)
definitions = json.loads(schema_path.read_text())["$defs"]


def validate(name: str, body: dict) -> None:
    schema = {"$defs": definitions, "$ref": f"#/$defs/{name}"}
    error = next(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(body), None)
    if error:
        field = ".".join(map(str, error.absolute_path)) or "body"
        raise ApiError(422, "invalid_input", f"Invalid {field}: {error.validator}")
