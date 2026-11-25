"""Install the walkthrough fixtures into an empty workspace in one transaction."""
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from .db import connect
from .store import mutate
from . import reviews


def install():
    fixtures = json.loads((Path(__file__).resolve().parents[1]/"sample/workspace.json").read_text())
    refs = {}
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(625016)")
        if conn.execute("SELECT 1 FROM records LIMIT 1").fetchone():
            return "Workspace already contains records. Sample import skipped."
        for kind in ("projects","milestones","roles","documents","tickets","runs"):
            for fields in fixtures[kind]:
                source = fields.pop("id")
                for name in ("project","milestone","role","ticket"):
                    if fields.get(name):
                        fields[name] = refs[fields[name]]
                if "documents" in fields:
                    fields["documents"] = [refs[d] for d in fields["documents"]]
                if "dueOffset" in fields:
                    fields["due"] = (today + timedelta(days=fields.pop("dueOffset"))).isoformat()
                if kind == 'runs' and not fields.get('ticket'):
                    fields['mode'] = 'Read only'
                saved = mutate(conn,kind,"Created","Sample import",fields,historical_import=True)
                refs[source] = saved["id"]
        for project in conn.execute("SELECT id FROM records WHERE kind='projects'").fetchall():
            reviews.sync_project(conn, project['id'], 'Sample import')
    return "Installed the two sample projects."


if __name__ == "__main__":
    print(install())
