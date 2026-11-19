import { Database } from "./types";
const now = Date.now();
const time = (hours: number) => new Date(now - hours * 3600000).toISOString();
export function fixtures(): Database {
  return {
    projects: [
      {
        id: "agentboard",
        name: "AgentBoard",
        purpose:
          "Coordinate agents, tasks and product decisions in one local workspace.",
        updated: time(1),
      },
      {
        id: "fieldnotes",
        name: "Fieldnotes",
        purpose: "A quiet place to capture field research and observations.",
        updated: time(7),
      },
    ],
    roles: [
      {
        id: "backend",
        projectId: "agentboard",
        name: "Backend",
        responsibilities: "Build typed MCP tools and reliable data services.",
      },
      {
        id: "frontend",
        projectId: "agentboard",
        name: "Frontend",
        responsibilities: "Create accessible, responsive desktop interfaces.",
      },
      {
        id: "designer",
        projectId: "agentboard",
        name: "Designer",
        responsibilities: "Shape clear workflows and a quiet visual system.",
      },
      {
        id: "architect",
        projectId: "agentboard",
        name: "Architect",
        responsibilities:
          "Maintain contracts, boundaries and technical decisions.",
      },
      {
        id: "researcher",
        projectId: "fieldnotes",
        name: "Researcher",
        responsibilities: "Synthesize field observations.",
      },
    ],
    tickets: [
      {
        id: "8f24c9e7",
        projectId: "agentboard",
        title: "Build MCP ticket tools",
        description:
          "Expose typed ticket creation and updates to Codex and Claude. Preserve project boundaries and explicit outcomes.",
        status: "In progress",
        priority: "High",
        ownerId: "backend",
        blocker: "",
        links: [{ documentId: "doc-mcp", relation: "Context" }],
        updated: time(0.2),
      },
      {
        id: "b3e9d1a2",
        projectId: "agentboard",
        title: "Design document history",
        description:
          "Let builders compare and rework retained document revisions.",
        status: "Planned",
        priority: "Medium",
        ownerId: "designer",
        blocker: "",
        links: [{ documentId: "doc-vision", relation: "Context" }],
        updated: time(0.5),
      },
      {
        id: "d7c4e8f1",
        projectId: "agentboard",
        title: "Add activity filters",
        description:
          "Make agent work reviewable by ticket, type, label and time.",
        status: "In progress",
        priority: "Medium",
        ownerId: "frontend",
        blocker: "",
        links: [],
        updated: time(1),
      },
      {
        id: "f1a9c2d4",
        projectId: "agentboard",
        title: "Define revision retention",
        description:
          "Keep current content and three previous document versions.",
        status: "Done",
        priority: "High",
        ownerId: "architect",
        blocker: "",
        links: [{ documentId: "doc-mcp", relation: "Output" }],
        updated: time(2),
      },
      {
        id: "c9b7e3a8",
        projectId: "agentboard",
        title: "Validate client approval",
        description:
          "Ensure clients without approval capability never apply protected mutations.",
        status: "Blocked",
        priority: "High",
        ownerId: "backend",
        blocker: "Waiting for a client approval capability check.",
        links: [],
        updated: time(3),
      },
      {
        id: "e2d8b5f0",
        projectId: "agentboard",
        title: "Create project overview",
        description: "Display accurate ticket counts and blockers.",
        status: "Planned",
        priority: "Low",
        ownerId: "",
        blocker: "",
        links: [],
        updated: time(5),
      },
    ],
    documents: [
      {
        id: "doc-mcp",
        projectId: "agentboard",
        title: "MCP ticket tool contract",
        revisions: [
          {
            id: "rev-4",
            number: 4,
            content:
              "Purpose\nExpose typed ticket operations to Codex and Claude.\n\nApproval rules\nCreate and Read are unrestricted. Update and Delete require verified client approval.\n\nPending requests\nNeeds approval is separate from task status.\n\nAudit\nRecord agent, ticket, action and time. Retain logs for 30 days.",
            updated: time(0.7),
            author: "Architect",
          },
          {
            id: "rev-3",
            number: 3,
            content:
              "Purpose\nExpose typed ticket operations to Codex and Claude.\n\nApproval rules\nCreate and Read are unrestricted. Update and Delete require verified client approval.\n\nAudit\nRecord agent, ticket, action and time. Retain logs for 30 days.",
            updated: time(2),
            author: "Architect",
          },
          {
            id: "rev-2",
            number: 2,
            content:
              "Purpose\nExpose ticket operations through MCP.\n\nApproval rules\nUpdate and Delete require approval.",
            updated: time(6),
            author: "Backend",
          },
          {
            id: "rev-1",
            number: 1,
            content: "Purpose\nExpose ticket operations through MCP.",
            updated: time(24),
            author: "Me",
          },
        ],
      },
      {
        id: "doc-vision",
        projectId: "agentboard",
        title: "Product vision",
        revisions: [
          {
            id: "vision-1",
            number: 1,
            content:
              "Product overview\nAgentBoard brings projects, agent roles, tickets and documents into one local workspace.\n\nValue\nSee what needs attention and keep supporting context close to the work.",
            updated: time(4),
            author: "Me",
          },
        ],
      },
    ],
    approvals: [
      {
        id: "req-8f24",
        ticketId: "8f24c9e7",
        action: "Update ticket status",
        before: "In progress",
        after: "Done",
        client: "Codex",
        state: "Pending",
      },
      {
        id: "req-8f25",
        ticketId: "8f24c9e7",
        action: "Update ticket priority",
        before: "High",
        after: "Medium",
        client: "Claude",
        state: "Unsupported",
      },
    ],
    activity: [
      {
        id: "event-1",
        projectId: "agentboard",
        ticketId: "8f24c9e7",
        agent: "Codex",
        action: "Requested ticket status update",
        type: "Ticket update",
        label: "mcp",
        outcome: "Needs approval",
        provenance: "Server-observed",
        time: time(0.1),
        before: "In progress",
        after: "Done",
      },
      {
        id: "event-2",
        projectId: "agentboard",
        ticketId: "d7c4e8f1",
        agent: "Claude",
        action: "Called tool: inspect activity schema",
        type: "Tool call",
        label: "frontend",
        outcome: "Succeeded",
        provenance: "Agent-reported",
        time: time(0.4),
      },
      {
        id: "event-3",
        projectId: "agentboard",
        ticketId: "8f24c9e7",
        agent: "Me",
        action: "Changed ownership",
        type: "Assignment",
        label: "ticket",
        outcome: "Succeeded",
        provenance: "Server-observed",
        time: time(1),
        before: "Unassigned",
        after: "Backend",
      },
      {
        id: "event-expired",
        projectId: "agentboard",
        agent: "Codex",
        action: "Expired example event",
        type: "Dispatch",
        label: "archive",
        outcome: "Succeeded",
        provenance: "Agent-reported",
        time: time(31 * 24),
      },
    ],
  };
}
