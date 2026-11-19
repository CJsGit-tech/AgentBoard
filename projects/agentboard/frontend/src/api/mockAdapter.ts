import { Activity, Database } from "./types";
export function id(prefix: string) {
  return prefix + "-" + crypto.randomUUID().slice(0, 8);
}
export function timestamp() {
  return new Date().toISOString();
}
export function retained(events: Activity[]) {
  return events
    .filter((e) => Date.now() - Date.parse(e.time) < 30 * 86400000)
    .sort((a, b) => Date.parse(b.time) - Date.parse(a.time));
}
export function addEvent(db: Database, event: Activity) {
  return db.activity.some((e) => e.id === event.id)
    ? db
    : { ...db, activity: [event, ...db.activity] };
}
export function formatTime(t: string) {
  return new Date(t).toISOString().replace("T", " ").slice(0, 19) + " UTC";
}
