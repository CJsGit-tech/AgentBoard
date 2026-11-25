import { mutateRecord } from "./features/operations/record-mutation";
import type { Row, WorkspaceRefresh } from "./model";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Alert, Button, Group, Loader, Stack, TextInput } from "@mantine/core";
import { ApiError, errorText, request } from "./model";
import { SubmissionGate } from "./formActions";

type Preview = {
  name: string;
  revision: number;
  activity_version: string;
  counts: Record<string, number>;
  previews: number;
};

const recordLabels = [
  ["milestones", "Milestones"],
  ["tickets", "Tickets"],
  ["roles", "Roles"],
  ["documents", "Documents"],
  ["runs", "Agent runs"],
] as const;

export function ProjectDeletion({ id, row, refresh, busy, setBusy, cancel, deleted }: {
  id: string;
  row: Row;
  refresh: WorkspaceRefresh;
  busy: boolean;
  setBusy: (busy: boolean) => void;
  cancel: () => void;
  deleted: () => void;
}) {
  const mutationGate=useRef(new SubmissionGate());
  const [preview, setPreview] = useState<Preview | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(false);
  const path = "projects/" + encodeURIComponent(id);

  useEffect(() => {
    let active = true;
    request<Preview>(path + "/deletion-preview").then(
      value => { if (active) setPreview(value); },
      err => {
        if (active) {
          setError(errorText(err));
          setReload(true);
        }
      },
    );
    return () => { active = false; };
  }, [path, attempt]);

  function reviewLatest() {
    setConfirmation("");
    setError("");
    setReload(false);
    setPreview(null);
    setAttempt(value => value + 1);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!preview || busy || reload || confirmation !== preview.name) return;
    return mutationGate.current.run(async () => {
      setBusy(true);
      setError("");
      try {
        await mutateRecord({kind:"projects",project:id,row,action:"purge",refresh,confirmed:deleted,
          write:()=>request(path + "/purge", "POST", {
            revision: preview.revision, activity_version: preview.activity_version, confirmation,
          })});
      } catch (err) {
        setError(errorText(err));
        if (!(err instanceof ApiError) || err.status === 409 || err.status === 404) {
          setReload(true);
        }
        setBusy(false);
        return;
      }
      setBusy(false);
    });
  }

  return <form className="project-deletion" onSubmit={submit} aria-busy={busy}>
    <Stack gap="md">
      {preview ? <>
        <Alert color="red" title="This action is permanent">
          <strong>{preview.name}</strong> and all its data will be deleted from AgentBoard, including activity history and records in Trash.
        </Alert>
        <dl className="deletion-counts" aria-label="Records to delete">
          {recordLabels.map(([kind, label]) => <div key={kind}>
            <dt>{label}</dt><dd>{preview.counts[kind] ?? 0}</dd>
          </div>)}
          <div><dt>Attached previews</dt><dd>{preview.previews}</dd></div>
        </dl>
        <TextInput
          label="Type the exact project name to confirm"
          description={preview.name}
          value={confirmation}
          onChange={event => setConfirmation(event.currentTarget.value)}
          disabled={busy || reload}
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
        />
      </> : !error && <Group><Loader size="sm" /> Loading project contents…</Group>}
      {error && <Alert role="alert" color="red">{error}</Alert>}
      <Group justify="flex-end">
        <Button type="button" variant="default" autoFocus disabled={busy} onClick={cancel}>Cancel</Button>
        {reload
          ? <Button type="button" variant="light" onClick={reviewLatest}>Review latest contents</Button>
          : <Button type="submit" color="red" loading={busy} disabled={!preview || confirmation !== preview.name}>
              Permanently delete project
            </Button>}
      </Group>
    </Stack>
  </form>;
}
