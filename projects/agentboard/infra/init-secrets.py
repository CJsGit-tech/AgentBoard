"""Create credentials for a manual AgentBoard Compose installation."""
import json
import os
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4


def main() -> None:
    directory = Path(__file__).resolve().parents[1] / ".local"
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_mode & 0o077:
        raise SystemExit("Set .local directory permissions to 0700 before creating credentials.")
    for name in ("db_password", "browser_token", "mcp_token"):
        try:
            fd = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        with os.fdopen(fd, "w") as file:
            if name == "mcp_token":
                identities = {
                    token_urlsafe(32): {"client_id": str(uuid4()), "name": client}
                    for client in ("Codex desktop", "Codex CLI", "Claude Code", "Claude Desktop")
                }
                json.dump(identities, file, indent=2)
                file.write("\n")
            else:
                file.write(token_urlsafe(32) + "\n")


if __name__ == "__main__":
    main()
