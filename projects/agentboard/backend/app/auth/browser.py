from hashlib import sha256
from hmac import digest
from pathlib import Path
import secrets
import time

from app.settings import settings


def _pairing_secret() -> bytes | None:
    path = settings.browser_token_file
    if not path:
        return None
    try:
        value = Path(path).read_bytes().strip()
    except OSError:
        return None
    return value or None


def pair_token_matches(value: str) -> bool:
    expected = _pairing_secret()
    return bool(expected and value and secrets.compare_digest(expected, value.encode("utf-8")))


def _signature(secret: bytes, session: str) -> str:
    return digest(secret, b"agentboard/browser-session:" + session.encode("ascii"), sha256).hex()


def issue_session_token() -> str:
    secret = _pairing_secret()
    if not secret:
        raise RuntimeError("Browser pairing credential is unavailable")
    expiry = int(time.time()) + 24 * 3600
    session = f"{expiry}.{secrets.token_urlsafe(32)}"
    return session + "." + _signature(secret, session)


def session_token_matches(value: str | None) -> bool:
    secret = _pairing_secret()
    if not secret or not value or len(value) > 160 or not value.isascii():
        return False
    try:
        session, supplied_signature = value.rsplit(".", 1)
        expiry, nonce = session.split(".", 1)
        if int(expiry) <= time.time() or not nonce:
            return False
    except ValueError:
        return False
    return secrets.compare_digest(supplied_signature, _signature(secret, session))
