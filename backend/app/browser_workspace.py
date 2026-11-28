"""Lightweight read models for the browser. The legacy workspace export stays available."""

from . import reviews
from .db import connect
from .models import MODELS
from .store import Problem, RECORDS_WITH_EDIT, activity_row, public


def _directory(conn, result):
    counts = {row["project"]: row for row in conn.execute("""
        SELECT project, count(*) FILTER (WHERE kind='documents') AS documents,
               count(*) FILTER (WHERE kind='milestones') AS milestones,
               count(*) FILTER (WHERE data->>'status'='Done' AND kind='tickets') AS done,
               count(*) FILTER (WHERE data->>'status'='In progress' AND kind='tickets') AS working,
               count(*) FILTER (WHERE data->>'status'='Planned' AND kind='tickets') AS planned,
               count(*) FILTER (WHERE data->>'status'='Blocked' AND kind='tickets') AS blocked
          FROM records WHERE NOT deleted AND kind IN ('tickets','documents','milestones')
         GROUP BY project
    """)}
    completed = {row["project"]: row["n"] for row in conn.execute("""
        SELECT project, count(*) AS n FROM (
            SELECT project, data->>'milestone' FROM records WHERE kind='tickets' AND NOT deleted
             GROUP BY project, data->>'milestone' HAVING bool_and(data->>'status'='Done')
        ) finished GROUP BY project
    """)}
    # Read-only activity facts for the Projects cards: last change, and when each currently Done ticket last became Done.
    last_activity = {row["project"]: row["at"].isoformat() for row in conn.execute(
        "SELECT project, max(at) AS at FROM activity GROUP BY project")}
    recent_done = {}
    for row in conn.execute("""
        SELECT a.project, max(a.at) AS at FROM activity a
          JOIN records r ON r.id=a.record AND r.kind='tickets' AND NOT r.deleted AND r.data->>'status'='Done'
          CROSS JOIN LATERAL jsonb_array_elements(a.changes) AS delta
         WHERE a.kind='tickets' AND delta->>0='status' AND delta->>2='Done'
         GROUP BY a.project, a.record
        HAVING max(a.at) > now() - interval '8 days'
         ORDER BY 2
    """):
        recent_done.setdefault(row["project"], []).append(row["at"].isoformat())
    for row in conn.execute("SELECT * FROM records WHERE kind='projects' ORDER BY created_at,id"):
        project = public(row)
        if row["deleted"]:
            result["trash"].append({"k": "projects", "r": project})
            continue
        count = counts.get(row["id"], {})
        project["summary"] = {
            "documents": count.get("documents", 0), "milestones": count.get("milestones", 0),
            "completed_milestones": completed.get(row["id"], 0),
            "statuses": {status: count.get(field, 0) for status, field in (
                ("Done", "done"), ("In progress", "working"), ("Planned", "planned"), ("Blocked", "blocked"))},
            "last_activity": last_activity.get(row["id"]),
            "recent_done": recent_done.get(row["id"], []),
        }
        result["projects"].append(project)


def _project_workspace(conn, project, result):
    for row in conn.execute(RECORDS_WITH_EDIT + " WHERE records.project=%s ORDER BY created_at,id", (project,)):
        record = public(row)
        if row["deleted"]:
            result["trash"].append({"k": row["kind"], "r": record})
        else:
            result[row["kind"]].append(record)
    # Preserve all delivery checkpoints; unrelated audit values are paged separately.
    result["activity"] = [activity_row(row) for row in conn.execute("""
        SELECT a.seq, a.at, a.project, a.actor, a.action, a.kind, a.record, a.name, a.editor_role,
               jsonb_build_array(delta) AS changes
          FROM activity a JOIN records r ON r.id=a.record AND NOT r.deleted
          CROSS JOIN LATERAL jsonb_array_elements(a.changes) AS delta
         WHERE a.project=%s AND a.kind='tickets' AND delta->>0='status' ORDER BY seq DESC
    """, (project,))]
    result["activity_count"] = conn.execute("SELECT count(*) AS n FROM activity WHERE project=%s", (project,)).fetchone()["n"]
    result["reviews"] = [reviews.public(row) for row in conn.execute("""
        SELECT c.id, c.revision, c.project, c.subject, c.review_type, c.operation, c.request, c.status,
               c.conclusion, c.rationale, c.findings, c.reviewer, c.confirmed_by, c.confirmation_note,
               c.created_at, c.updated_at, c.superseded, c.signature,
               jsonb_build_object('subject', (c.snapshot->'subject') - 'fields' - 'baseline',
                   'missing_context', c.snapshot->'missing_context',
                   'documents', (SELECT coalesce(jsonb_agg(doc - 'fields' - 'baseline' ORDER BY ord), '[]')
                    FROM jsonb_array_elements(c.snapshot->'documents') WITH ORDINALITY docs(doc,ord))) AS snapshot
          FROM change_reviews c JOIN records r ON r.id=c.subject AND NOT r.deleted
         WHERE c.project=%s AND NOT c.superseded ORDER BY c.created_at DESC,c.id
    """, (project,))]


def browser_state(project, previous_etag):
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        if project:
            version = conn.execute("SELECT coalesce(max(seq),0) AS n FROM activity WHERE project=%s", (project,)).fetchone()["n"]
        else:
            version = conn.execute("SELECT coalesce(max(seq),0) AS n FROM activity").fetchone()["n"]
        purge = conn.execute("SELECT version FROM workspace_purge_version").fetchone()["version"]
        etag = f'"browser-v1-{project or "directory"}-{version}-{purge}"'
        if previous_etag == etag:
            return etag, None
        result = {kind: [] for kind in MODELS}
        result.update(trash=[], activity=[], activity_count=0, reviews=[])
        if project:
            _project_workspace(conn, project, result)
        else:
            _directory(conn, result)
        return etag, result


def owner(kind, key):
    with connect() as conn:
        row = conn.execute("SELECT project FROM records WHERE kind=%s AND id=%s AND NOT deleted", (kind, key)).fetchone()
        if not row:
            raise Problem(404, "Record unavailable.")
        return row


def review_history(project, subject, offset, limit):
    with connect() as conn:
        rows = conn.execute("""
            SELECT c.id, c.revision, c.status, c.created_at, c.review_type, c.superseded
              FROM change_reviews c JOIN records r ON r.id=c.subject AND NOT r.deleted
             WHERE c.project=%s AND c.subject=%s ORDER BY c.created_at DESC,c.id
             OFFSET %s LIMIT %s
        """, (project, subject, offset, limit + 1)).fetchall()
        return {"items": [reviews.public(row) for row in rows[:limit]],
                "next_offset": offset + limit if len(rows) > limit else None}


def review_detail(project, key):
    with connect() as conn:
        row = conn.execute("""SELECT c.* FROM change_reviews c JOIN records r ON r.id=c.subject AND NOT r.deleted
                               WHERE c.id=%s AND c.project=%s""", (key, project)).fetchone()
        if not row:
            raise Problem(404, "Review unavailable.")
        return reviews.public(row)


def history_page(project, before, limit, record, actor, action, kind, search, start, end):
    from psycopg import sql

    conditions = [sql.SQL("project=%s")]
    params = [project]
    for field, value in (("record", record), ("actor", actor), ("action", action), ("kind", kind)):
        if value:
            conditions.append(sql.SQL("{}=%s").format(sql.Identifier(field)))
            params.append(value)
    if start is not None:
        conditions.append(sql.SQL("at >= %s"))
        params.append(start)
    if end is not None:
        conditions.append(sql.SQL("at < %s"))
        params.append(end)
    if search:
        conditions.append(sql.SQL("""(EXISTS (SELECT FROM unnest(ARRAY[name,actor,action,record,kind]) x
                                             WHERE strpos(lower(x),lower(%s))>0)
                           OR EXISTS (SELECT FROM jsonb_array_elements(changes) change
                                      WHERE strpos(lower(change->>0),lower(%s))>0))"""))
        params.extend([search, search])

    where = sql.SQL(" FROM activity WHERE ") + sql.SQL(" AND ").join(conditions)
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        total = conn.execute(sql.SQL("SELECT count(*) AS n") + where, params).fetchone()["n"]
        if before is not None:
            where += sql.SQL(" AND seq < %s")
            params.append(before)
        rows = conn.execute(sql.SQL("SELECT *") + where + sql.SQL(" ORDER BY seq DESC LIMIT %s"),
                            [*params, limit + 1]).fetchall()
        facets = conn.execute("""
            SELECT ARRAY(SELECT DISTINCT actor FROM activity WHERE project=%s ORDER BY actor) AS actors,
                   ARRAY(SELECT DISTINCT action FROM activity WHERE project=%s ORDER BY action) AS actions,
                   ARRAY(SELECT DISTINCT kind FROM activity WHERE project=%s ORDER BY kind) AS kinds
        """, (project, project, project)).fetchone()
        return {"items": [activity_row(row) for row in rows[:limit]], "total": total, "facets": facets,
                "next_before": str(rows[limit - 1]["seq"]) if len(rows) > limit else None}
