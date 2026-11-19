export type Status = "Planned" | "In progress" | "Blocked" | "Done";
export type Priority = "High" | "Medium" | "Low";
export interface Project {
  id: string;
  name: string;
  purpose: string;
  updated: string;
  revision?: number;
}
export interface Role {
  id: string;
  projectId: string;
  name: string;
  responsibilities: string;
  revision?: number;
}
export interface Link {
  documentId: string;
  relation: "Context" | "Output";
}
export interface Ticket {
  id: string;
  /** Human-readable source ticket number, when supplied by a connected source. */
  displayReference?: string;
  projectId: string;
  title: string;
  description: string;
  details?: string;
  status: Status;
  priority: Priority;
  ownerId: string;
  blocker: string;
  links: Link[];
  updated: string;
  revision?: number;
  featureTags?: string[];
  concernTags?: string[];
  executionRole?: "FE" | "BE";
  workType?: "BUG" | "BUILD";
  estimateDays?: number;
  estimateScope?: string;
  estimateBasis?: string;
  verification?: "reported" | "investigating" | "confirmed" | "not_reproduced" | "fixed" | "not_a_bug" | "not_applicable";
  assignment?: "confirmed" | "provisional";
}
export function ticketDisplayReference(ticket: Ticket): string | undefined {
  return ticket.displayReference || (/^T-\d{3}$/.test(ticket.id) ? ticket.id : undefined);
}
export interface Revision {
  id: string;
  number: number;
  content: string;
  updated: string;
  author: string;
}
export interface Doc {
  id: string;
  projectId: string;
  title: string;
  revisions: Revision[];
  description?: string;
  kind?: string;
  featureTags?: string[];
  concernTags?: string[];
  sourceFilename?: string;
  originalFrontmatter?: string;
  uploadedAt?: string;
  revision?: number;
}
export interface Approval {
  id: string;
  ticketId: string;
  action: string;
  before: string;
  after: string;
  client: string;
  state: "Pending" | "Unsupported" | "Rejected" | "Expired" | "Stale";
}
export interface Activity {
  id: string;
  projectId: string;
  ticketId?: string;
  agent: string;
  action: string;
  type: string;
  label: string;
  outcome: string;
  provenance: "Agent-reported" | "Server-observed";
  time: string;
  before?: string;
  after?: string;
}
export interface Database {
  projects: Project[];
  roles: Role[];
  tickets: Ticket[];
  documents: Doc[];
  approvals: Approval[];
  activity: Activity[];
}
export const statuses: Status[] = ["Planned", "In progress", "Blocked", "Done"];
