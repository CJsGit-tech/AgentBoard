import { useState } from "react";
import { Button, Drawer, NativeSelect } from "@mantine/core";
import { errorText } from "./model";
import { InfoHelp } from "./features/help/InfoHelp";
import "./features/help/agentbuild-guide.css";

type Workflow = {
  name: "Setup" | "Create Documents" | "Create Visuals" | "Create Tickets";
  purpose: string;
  example: string;
};

const workflows: Workflow[] = [
  {
    name: "Setup",
    purpose: "Check the project, roles, and core documents before work starts.",
    example: "Check the roles and core documents.",
  },
  {
    name: "Create Documents",
    purpose: "Create or update User Experiences, UserScreens, the Design Profile, Product Brief, Technical Stack, and other project documents.",
    example: "Draft the Product Brief.",
  },
  {
    name: "Create Visuals",
    purpose: "Use the project journeys and Design Profile to build a local interactive Canvas for review. Publish a new immutable version on the Design Profile only when you request upload.",
    example: "Draft the screens for the selected journey and show them for review.",
  },
  {
    name: "Create Tickets",
    purpose: "Compare requested work with the agreed project scope and record its context.",
    example: "Create a FE-Bug in [milestone] for [issue].",
  },
];

const existingTicketPrompt = "Continue PocketReminder’s existing Forms and details ticket. Read the approved requirements and pinned Canvas before editing. Verify that older item types remain editable without appearing in the add menu. Link the exact capture or test result to that criterion and open it from the ticket before reporting completion.";

export function Guide({ opened, close, project }: {
  opened: boolean;
  close: () => void;
  project?: string;
}) {
  const [ide, setIde] = useState("Codex");
  const [copyState, setCopyState] = useState<{ workflow: string; type: "copied" | "error"; message: string } | null>(null);

  function commandFor(workflow: Workflow) {
    const prefix = ide === "Codex" ? "$agentbuild" : "/agentbuild";
    return `${prefix} ${workflow.name} for ${project || "[project]"}. ${workflow.example}`;
  }

  async function copy(workflow: string, command: string) {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard access is unavailable in this browser.");
      await navigator.clipboard.writeText(command);
      setCopyState({ workflow, type: "copied", message: workflow === "Existing ticket" ? "Example copied." : "Command copied." });
    } catch (error) {
      setCopyState({ workflow, type: "error", message: `Could not copy this ${workflow === "Existing ticket" ? "example" : "command"}. ${errorText(error)}` });
    }
  }

  function feedback(workflow: string) {
    const result = copyState?.workflow === workflow ? copyState : null;
    return result && <p className={`copy-feedback${result.type === "error" ? " is-error" : ""}`} role={result.type === "error" ? "alert" : "status"}>{result.message}</p>;
  }

  return (
    <Drawer
      opened={opened}
      onClose={close}
      title={<span className="with-info">AgentBuild guide<InfoHelp label="AgentBuild workflows">Run a named workflow in your IDE. Required document and scope checks happen as part of the workflow. Only a change to agreed scope needs your confirmation.</InfoHelp></span>}
      position="right"
      size="min(520px, 96vw)"
      closeButtonProps={{ "aria-label": "Close AgentBuild guide" }}
    >
      <div className="workflow-guide">
        <NativeSelect
          label="IDE"
          value={ide}
          onChange={(event) => {
            setIde(event.currentTarget.value);
            setCopyState(null);
          }}
          data={["Codex", "Claude Code"]}
        />
        <div className="guide-workflows">
          {workflows.map((workflow) => {
            const command = commandFor(workflow);
            return (
              <section className="guide-workflow" key={workflow.name}>
                <h2>{workflow.name}</h2>
                <p>{workflow.purpose}</p>
                <div className="guide-command">
                  <code>{command}</code>
                  <Button
                    type="button"
                    size="xs"
                    variant="default"
                    aria-label={`Copy ${workflow.name} command`}
                    onClick={() => { void copy(workflow.name, command); }}
                  >
                    Copy
                  </Button>
                </div>
                {feedback(workflow.name)}
              </section>
            );
          })}
        </div>
        <section className="guide-workflow">
          <h2>Continue an existing ticket</h2>
          <p>Worked example: PocketReminder’s Forms and details ticket. Paste this follow-up in {ide} after locating the reviewed ticket. You can also select the ticket in the InApp Assistant and use Edit mode after its checks are ready.</p>
          <div className="guide-command">
            <code>{existingTicketPrompt}</code>
            <Button type="button" size="xs" variant="default" aria-label="Copy existing-ticket example" onClick={() => { void copy("Existing ticket", existingTicketPrompt); }}>Copy</Button>
          </div>
          {feedback("Existing ticket")}
          <ol className="guide-handoff-steps">
            <li>Read the approved requirements in Context and open the exact design version for the criterion before changing the implementation.</li>
            <li>Save the report and captures as Outputs. On the criterion, link a specific report revision and heading or the exact screenshot. Use Unverified when the check or upload is incomplete.</li>
            <li>In AgentBoard, open PocketReminder → Tickets → Forms and details. Read the criterion and click its proof. Confirm the target opens before marking the ticket Done.</li>
          </ol>
          <p>Keep successful partial uploads linked and report the missing proof. Draft requirements and replacement designs still need review before upload.</p>
        </section>
      </div>
    </Drawer>
  );
}
