import { useState } from "react";
import { Button, Drawer, NativeSelect } from "@mantine/core";
import { errorText } from "./model";
import { InfoHelp } from "./features/help/InfoHelp";

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
    example: "Mock up the checkout flow.",
  },
  {
    name: "Create Tickets",
    purpose: "Compare requested work with the agreed project scope and record its context.",
    example: "Create a FE-Bug in [milestone] for [issue].",
  },
];

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

  async function copy(workflow: Workflow) {
    const command = commandFor(workflow);
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard access is unavailable in this browser.");
      await navigator.clipboard.writeText(command);
      setCopyState({ workflow: workflow.name, type: "copied", message: "Command copied." });
    } catch (error) {
      setCopyState({ workflow: workflow.name, type: "error", message: `Could not copy this command. ${errorText(error)}` });
    }
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
            const result = copyState?.workflow === workflow.name ? copyState : null;
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
                    onClick={() => { void copy(workflow); }}
                  >
                    Copy
                  </Button>
                </div>
                {result && (
                  <p className={`copy-feedback${result.type === "error" ? " is-error" : ""}`} role={result.type === "error" ? "alert" : "status"}>
                    {result.message}
                  </p>
                )}
              </section>
            );
          })}
        </div>
      </div>
    </Drawer>
  );
}
