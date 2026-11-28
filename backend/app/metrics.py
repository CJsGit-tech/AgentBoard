"""Read-only Dashboard and Portfolio metrics (Design Profile V5, decision D; Technical Stack rev 12).

Every value is derived from saved records and activity. Nothing here writes.
Durations use the last update of a done ticket, because tickets have no completion timestamp yet.
"""
from datetime import date, datetime, timedelta, timezone
from statistics import median

from .db import connect
from .models import KPI_TARGET_DEFAULTS
from .store import RECORDS_WITH_EDIT, Problem, public

FINISHED_RUNS = ("Completed", "Failed", "Cancelled")
MAX_DAYS = 92


def _window(start: date | None, end: date | None, tz_offset: int):
    """Inclusive local-day window; defaults to the last 7 days ending today in the caller's offset."""
    tz = timezone(timedelta(minutes=tz_offset))
    today = datetime.now(tz).date()
    end = end or today
    start = start or end - timedelta(days=6)
    if start > end:
        raise Problem(422, "The start date must be on or before the end date.")
    if (end - start).days + 1 > MAX_DAYS:
        raise Problem(422, f"Choose a range of {MAX_DAYS} days or fewer.")
    return tz, start, end, [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _done_times(conn, projects):
    """When each currently Done ticket last became Done, from saved status activity."""
    rows = conn.execute("""
        SELECT a.project, a.record, max(a.at) AS at FROM activity a
          JOIN records r ON r.id=a.record AND r.kind='tickets' AND NOT r.deleted AND r.data->>'status'='Done'
          CROSS JOIN LATERAL jsonb_array_elements(a.changes) AS delta
         WHERE a.project = ANY(%s) AND a.kind='tickets' AND delta->>0='status' AND delta->>2='Done'
         GROUP BY a.project, a.record
    """, (projects,))
    return {(row["project"], row["record"]): row["at"] for row in rows}


def _per_day(times, tz, days):
    counts = {day: 0 for day in days}
    for at in times:
        day = at.astimezone(tz).date()
        if day in counts:
            counts[day] += 1
    return [{"day": day.isoformat(), "count": n} for day, n in counts.items()]


def _ratio(numerator, denominator):
    return {"value": numerator, "total": denominator, "percent": round(100 * numerator / denominator, 1) if denominator else None}


def _parse(stamp):
    try:
        return datetime.fromisoformat(stamp) if stamp else None
    except ValueError:
        return None


def project_metrics(project: str, start: date | None = None, end: date | None = None, tz_offset: int = 0):
    tz, start, end, days = _window(start, end, tz_offset)
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        owner = conn.execute("SELECT * FROM records WHERE id=%s AND kind='projects' AND NOT deleted", (project,)).fetchone()
        if not owner:
            raise Problem(404, "Project unavailable.")
        settings = public(owner)
        rows = [public(row) for row in conn.execute(
            RECORDS_WITH_EDIT + " WHERE records.project=%s AND NOT records.deleted AND records.kind IN ('tickets','runs')", (project,))]
        done_at = _done_times(conn, [project])
    tickets = [row for row in rows if row["record_path"].startswith("/#tickets/")]
    runs = [row for row in rows if row["record_path"].startswith("/#runs/")]
    done = [t for t in tickets if t.get("status") == "Done"]
    statuses = {status: sum(t.get("status") == status for t in tickets) for status in ("Done", "In progress", "Blocked", "Planned")}
    leads = [(_parse(t["updated_at"]) - _parse(t["created_at"])).total_seconds() / 3600 for t in done if _parse(t.get("updated_at")) and _parse(t.get("created_at"))]
    lo, hi = datetime.combine(start, datetime.min.time(), tz), datetime.combine(end + timedelta(days=1), datetime.min.time(), tz)
    in_range = [r for r in runs if (stamp := _parse(r.get("updated"))) and lo <= stamp < hi]
    finished = [r for r in runs if r.get("status") in FINISHED_RUNS]
    by_agent = {}
    for run in in_range:
        agent = by_agent.setdefault(run.get("agent") or "Not recorded", {"total": 0, "statuses": {}})
        agent["total"] += 1
        agent["statuses"][run.get("status") or "Unspecified"] = agent["statuses"].get(run.get("status") or "Unspecified", 0) + 1
    return {
        "project": project, "range": {"start": start.isoformat(), "end": end.isoformat(), "tz_offset": tz_offset},
        "targets": {key: settings.get(key, value) for key, value in KPI_TARGET_DEFAULTS.items()},
        "tickets": {"total": len(tickets), "statuses": statuses},
        "completion": _ratio(statuses["Done"], len(tickets)),
        "evidence_coverage": _ratio(sum(bool(t.get("output_documents")) for t in done), len(done)),
        "run_success": _ratio(sum(r.get("status") == "Completed" for r in finished), len(finished)),
        "median_hours_to_last_update": round(median(leads), 2) if leads else None,
        "done_per_day": _per_day([at for (p, _), at in done_at.items() if p == project], tz, days),
        "runs_by_agent": dict(sorted(by_agent.items(), key=lambda item: -item[1]["total"])),
        "runs_in_range": len(in_range),
        "note": "Durations use each done ticket's last update; tickets have no completion timestamp.",
    }


def portfolio_summary(start: date | None = None, end: date | None = None, tz_offset: int = 0):
    tz, start, end, days = _window(start, end, tz_offset)
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        projects = [public(row) for row in conn.execute("SELECT * FROM records WHERE kind='projects' AND NOT deleted ORDER BY created_at,id")]
        ids = [p["id"] for p in projects]
        statuses = {}
        for row in conn.execute("""
            SELECT project, data->>'status' AS status, count(*) AS n FROM records
             WHERE kind='tickets' AND NOT deleted AND project = ANY(%s) GROUP BY project, data->>'status'
        """, (ids,)):
            statuses.setdefault(row["project"], {})[row["status"] or "Unspecified"] = row["n"]
        agents = {}
        for row in conn.execute("""
            SELECT project, coalesce(data->>'agent','Not recorded') AS agent, coalesce(data->>'status','Unspecified') AS status, count(*) AS n
              FROM records WHERE kind='runs' AND NOT deleted AND project = ANY(%s) GROUP BY 1,2,3
        """, (ids,)):
            entry = agents.setdefault(row["project"], {}).setdefault(row["agent"], {"total": 0, "statuses": {}})
            entry["total"] += row["n"]
            entry["statuses"][row["status"]] = row["n"]
        done_at = _done_times(conn, ids)
    result = []
    for project in projects:
        counts = {status: statuses.get(project["id"], {}).get(status, 0) for status in ("Done", "In progress", "Blocked", "Planned")}
        total = sum(statuses.get(project["id"], {}).values())
        result.append({
            "id": project["id"], "name": project["name"], "statuses": counts, "total": total, "open": total - counts["Done"],
            "done_per_day": _per_day([at for (p, _), at in done_at.items() if p == project["id"]], tz, days),
            "runs_by_agent": agents.get(project["id"], {}),
            "targets": {key: project.get(key, value) for key, value in KPI_TARGET_DEFAULTS.items()},
        })
    totals = {"total": sum(p["total"] for p in result), "done": sum(p["statuses"]["Done"] for p in result)}
    totals["open"] = totals["total"] - totals["done"]
    return {"range": {"start": start.isoformat(), "end": end.isoformat(), "tz_offset": tz_offset}, "projects": result, "totals": totals}
