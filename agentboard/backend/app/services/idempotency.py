import hashlib
import json

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.db.models import IdempotencyRecord


def reserve(db: Session, scope: str, key: str, payload: dict) -> tuple[IdempotencyRecord, bool]:
    if not key or len(key) > 128:
        raise ApiError(422, "invalid_idempotency_key", "Idempotency-Key must contain 1 to 128 characters")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    statement = insert(IdempotencyRecord).values(scope=scope, key=key, payload_hash=digest, result_json=None).on_conflict_do_nothing(index_elements=["scope", "key"]).returning(IdempotencyRecord.id)
    inserted_id = db.scalar(statement)
    row = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.scope == scope, IdempotencyRecord.key == key).with_for_update())
    if row is None:
        raise RuntimeError("Idempotency reservation was not visible in its transaction")
    if inserted_id is not None:
        return row, True
    if row.payload_hash != digest:
        raise ApiError(409, "idempotency_conflict", "This Idempotency-Key was already used with a different payload")
    if row.result_json is None:
        raise ApiError(409, "operation_in_progress", "The operation with this Idempotency-Key is still in progress")
    return row, False
