/** Reject overlapping user actions rather than queueing a second mutation. */
export class SubmissionGate {
  private pending = false;

  get busy() { return this.pending; }

  async run<T>(action: () => Promise<T>): Promise<T | undefined> {
    if (this.pending) return undefined;
    this.pending = true;
    try { return await action(); }
    finally { this.pending = false; }
  }
}

export function submitsMessage(key: string, shift: boolean, composing: boolean, keyCode: number) {
  return key === "Enter" && !shift && !composing && keyCode !== 229;
}

export type TaskRequestFields = {message:string;model:string;mode:"Read only"|"Edit";ticketId:string;roleId:string};
export function sameTaskRequest(first:TaskRequestFields,second:TaskRequestFields) {
  return first.message===second.message && first.model===second.model && first.mode===second.mode &&
    first.roleId===second.roleId && (first.mode==="Read only"||first.ticketId===second.ticketId);
}

/** A transport failure or server timeout/error does not prove a write was rejected. */
export function uncertainSubmission(status?:number) {
  return status===undefined || status===408 || status>=500;
}

export const PREVIEW_NAVIGATION = "agentboard:preview-navigate";
export function guardDraftNavigation(
  target: EventTarget,
  state: () => {dirty: boolean; busy: boolean},
  askToDiscard: (resume: () => void) => void,
) {
  const listener = (event: Event) => {
    const current = state();
    if (!current.dirty && !current.busy) return;
    event.preventDefault();
    if (current.busy) return;
    const resume = (event as CustomEvent<{resume: () => void}>).detail?.resume;
    if (typeof resume !== "function") throw new Error("Navigation has no continuation.");
    askToDiscard(resume);
  };
  target.addEventListener(PREVIEW_NAVIGATION, listener);
  return () => target.removeEventListener(PREVIEW_NAVIGATION, listener);
}
