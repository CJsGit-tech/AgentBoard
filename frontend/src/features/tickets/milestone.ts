import type { Row } from "../../model";

export function ticketsForMilestone(tickets: Row[], milestone: Row) {
  return tickets.filter(ticket => ticket.project === milestone.project && ticket.milestone === milestone.id);
}

export function milestoneFromTicketRoute(hash: string) {
  const [path, query = ""] = hash.split("?", 2);
  const parts = path.replace(/^#/, "").split("/");
  if (parts[0] !== "project" || parts[2] !== "tickets" || (parts[3] && !["attention", "overdue"].includes(parts[3]))) return "";
  return new URLSearchParams(query).get("milestone") || "";
}

export function withMilestoneTicketFilter(hash: string, milestoneId: string) {
  const [path, query = ""] = hash.split("?", 2);
  const params = new URLSearchParams(query);
  if (milestoneId) params.set("milestone", milestoneId);
  else params.delete("milestone");
  return params.size ? `${path}?${params}` : path;
}
