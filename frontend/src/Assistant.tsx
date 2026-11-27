import { ReviewSnapshot } from "./features/monitoring/ReviewHistory";
import { workspacePath } from "./model";
import { OperationFeedback, useOperationLock } from "./features/operations/Operations";
import { operations, projectResource, type Mutation } from "./features/operations/operation-store";
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Button, Modal, NativeSelect, PasswordInput, Tabs, Textarea } from "@mantine/core";
import { TicketSummary } from "./features/tickets/TicketSummary";
import { Empty, Icon, Tag } from "./Common";
import { describeWithHelp, InfoHelp } from "./features/help/InfoHelp";
import {
  ApiError,
  currentReview,
  errorText,
  request,
  reviewReady,
  stamp,
  type AssistantConfig,
  type AssistantConversation,
  type AssistantConversationSummary,
  type AssistantExecution,
  type AssistantMessage,
  type AssistantRestorePreview,
  type AssistantRun,
  type AssistantRunEvent,
  type AssistantRunEvents,
  type ChangeReview,
  type Row,
  type Workspace,
} from "./model";
import "./Assistant.css";
import "./features/assistant/assistant.css";
import { SubmissionGate, submitsMessage, sameTaskRequest, uncertainSubmission, type TaskRequestFields } from "./formActions";

type TaskAttempt = TaskRequestFields & {id:string;conversationId?:string};
// Only unsent/submitted task context is retained here. Credentials never enter this cache.
const pendingTasks = new Map<string, TaskAttempt>();

type ConnectionState = { kind: "idle" | "testing" | "connected" | "error"; model?: string; message?: string };
type Props = {
  projectId: string;
  projectName: string;
  db: Workspace;
  initialRunId?: string;
  onOpenRun: (runId: string) => void;
  onCloseRun: () => void;
  onShowRuns: () => void;
  onOpenTicket: (ticketId: string) => void;
  onShowTickets: () => void;
  onRefreshWorkspace: import("./model").WorkspaceRefresh;
};

const API = "assistant/";
const RELIABILITY_NOTICE = "API sessions can disconnect or stop unexpectedly. Check the latest saved step before continuing. If completion is uncertain, review before retrying.";
const RUN_POLL_MS = 2200;
const PROJECT_POLL_MS = 7000;
const TERMINAL_RUN_STATES = new Set(["Completed", "Failed", "Cancelled"]);

function api<T>(path: string, method = "GET", body?: unknown) {
  return request<T>(API + path, method, body);
}

function statusLabel(status: string) {
  return status.replaceAll("_", " ");
}

function roleLabel(message: AssistantMessage) {
  if (message.role === "user") return "You";
  if (message.role === "assistant") return "Assistant";
  return statusLabel(message.role);
}

function latestRun(runs: AssistantRun[]) {
  return [...runs].sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
}

function valueText(value: unknown) {
  return typeof value === "string" || typeof value === "number" ? String(value) : "";
}

function eventDetail(event: AssistantRunEvent) {
  for (const key of ["summary", "message", "step", "status"]) {
    const value = valueText(event.payload?.[key]);
    if (value) return value;
  }
  return "";
}

function eventLabel(type: string) {
  const short = type.startsWith("run.") ? type.slice(4) : type.replaceAll(".", " ");
  return statusLabel(short);
}

function checkLabel(check: string | Record<string, unknown>, index: number) {
  if (typeof check === "string") return check;
  return valueText(check.label) || valueText(check.name) || valueText(check.command) || `Check ${index + 1}`;
}

function checkResult(check: string | Record<string, unknown>) {
  if (typeof check === "string") return "Reported";
  if (typeof check.passed === "boolean") return check.passed ? "Passed" : "Failed";
  if (typeof check.exit_code === "number") return check.exit_code === 0 ? "Passed" : `Exit ${check.exit_code}`;
  return valueText(check.result) || valueText(check.status) || "Reported";
}

function projectPath(path: string) {
  return path || "Not reported";
}

export function Assistant({
  projectId,
  projectName,
  db,
  initialRunId,
  onOpenRun,
  onCloseRun,
  onShowRuns,
  onOpenTicket,
  onShowTickets,
  onRefreshWorkspace,
}: Props) {
  const actionResources = [projectResource(projectId), "assistant:settings"];
  const actionLocked = useOperationLock(actionResources);
  const tickets = useMemo(() => db.tickets.filter((ticket) => ticket.project === projectId), [db.tickets, projectId]);
  const roles = useMemo(() => db.roles.filter((role) => role.project === projectId), [db.roles, projectId]);

  const [config, setConfig] = useState<AssistantConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [configError, setConfigError] = useState("");
  const [keyInput, setKeyInput] = useState("");
  const [credentialBusy, setCredentialBusy] = useState(false);
  const [credentialError, setCredentialError] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [connection, setConnection] = useState<ConnectionState>({ kind: "idle" });

  const [execution, setExecution] = useState<AssistantExecution | null>(null);
  const [executionLoading, setExecutionLoading] = useState(true);
  const [executionError, setExecutionError] = useState("");
  const [executionExpanded, setExecutionExpanded] = useState(false);

  const [conversations, setConversations] = useState<AssistantConversationSummary[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [conversationsError, setConversationsError] = useState("");
  const [conversation, setConversation] = useState<AssistantConversation | null>(null);
  const [conversationBusy, setConversationBusy] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [settingsOpen,setSettingsOpen]=useState(false),[railTab,setRailTab]=useState<string|null>("history");
  const settingsButton=useRef<HTMLButtonElement>(null);

  const [recentRuns, setRecentRuns] = useState<AssistantRun[]>([]);
  const [recentRunsError, setRecentRunsError] = useState("");
  const [recentRunsLoading, setRecentRunsLoading] = useState(true);
  const [draft, setDraft] = useState(pendingTasks.get(projectId)?.message || "");
  const [mode, setMode] = useState<"Read only" | "Edit">(pendingTasks.get(projectId)?.mode || "Read only");
  const [ticketId, setTicketId] = useState(pendingTasks.get(projectId)?.ticketId || "");
  const [roleId, setRoleId] = useState(pendingTasks.get(projectId)?.roleId || "");
  const [submitting, setSubmitting] = useState(false);
  const [messageError, setMessageError] = useState("");
  const [submitNotice, setSubmitNotice] = useState("");

  type ChatDraft={message:string;mode:"Read only"|"Edit";ticketId:string;roleId:string};
  const storedDrafts=useRef<Record<string,ChatDraft>>({}),activeDraftKey=useRef("new");
  const draftState=useRef<ChatDraft>({message:draft,mode,ticketId,roleId});draftState.current={message:draft,mode,ticketId,roleId};
  function activateDraft(key:string,run?:AssistantRun) {
    if(key===activeDraftKey.current)return;
    storedDrafts.current[activeDraftKey.current]=draftState.current;
    const next=storedDrafts.current[key]||(pendingTasks.get(projectId)?.conversationId===key?pendingTasks.get(projectId):undefined)||{message:"",mode:run?.mode||"Read only",ticketId:run?.ticket_id||"",roleId:run?.role_id||""};
    activeDraftKey.current=key;setDraft(next.message);setMode(next.mode);setTicketId(next.ticketId);setRoleId(next.roleId);
  }
  function newChat(){if(operations.locked(actionResources))return;activateDraft("new");setConversation(null);setActiveRun(null);setHistoryOpen(false);setMessageError("");setSubmitNotice("");if(initialRunId)onCloseRun();}
  function closeSettings(){setSettingsOpen(false);setKeyInput("");requestAnimationFrame(()=>settingsButton.current?.focus());}

  const [detailRun, setDetailRun] = useState<AssistantRun | null>(null);
  const [activeRun, setActiveRun] = useState<AssistantRun | null>(null);
  const [runEvents, setRunEvents] = useState<AssistantRunEvent[]>([]);
  const [runPollingError, setRunPollingError] = useState("");
  const [runActionError, setRunActionError] = useState("");
  const [runActionBusy, setRunActionBusy] = useState("");
  const [runActionNotice, setRunActionNotice] = useState("");
  const [pollingEpoch, setPollingEpoch] = useState(0);
  const [restorePreview, setRestorePreview] = useState<AssistantRestorePreview | null>(null);
  const [reviewBusy, setReviewBusy] = useState("");
  const [reviewErrors, setReviewErrors] = useState<Record<string, string>>({});
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, string>>({});
  const [showAllScopeProposals, setShowAllScopeProposals] = useState(false);

  const credentialGate=useRef(new SubmissionGate());
  const messageGate=useRef(new SubmissionGate());
  const connectionGate=useRef(new SubmissionGate());
  const runGate=useRef(new SubmissionGate());
  const scopeGate=useRef(new SubmissionGate());
  const connectionEpoch=useRef(0);
  const conversationRead=useRef(0);
  const detailRead=useRef(0);
  const readTokens=useRef<Record<string,number>>({});
  const latestSeq = useRef(0);
  const pendingRequest = useRef<TaskAttempt | null>(pendingTasks.get(projectId)||null);
  const pendingView=useRef<TaskAttempt|null>(pendingTasks.get(projectId)||null);
  const selectedTicket = tickets.find((ticket) => ticket.id === ticketId);
  const selectedReview = selectedTicket ? currentReview(db, selectedTicket.id) : undefined;
  const editGateReady = !!selectedTicket && reviewReady(selectedReview) && execution?.status === "Ready";
  const activeConversation = conversation;
  const conversationRun = activeConversation ? latestRun(activeConversation.runs) : undefined;
  const visibleRun = detailRun || activeRun || conversationRun || null;
  const watchedRunId = initialRunId || activeRun?.id || "";
  const recentConversations = useMemo(() => new Map(conversations.map((item) => [item.id, item.title])), [conversations]);

  const loadConfig = useCallback(async (strict = false) => {
    const epoch=operations.epoch, token=(readTokens.current["loadConfig"]||0)+1;
    readTokens.current["loadConfig"]=token;
    setConfigLoading(true);
    setConfigError("");
    try {
      const result = await api<AssistantConfig>("config");
      if(epoch!==operations.epoch || token!==readTokens.current["loadConfig"]){if(strict===true)throw Error("Saved state changed during this read. Retry sync.");return;}
      setConfig(result);
      setSelectedModel((current) => current || result.models.find((item) => item.id === "gpt-6-luna")?.id || result.models[0]?.id || "");
      setConnection({ kind: "idle" });
    } catch (error) {
      if (strict === true) throw error;
      setConfigError(errorText(error));
    } finally {
      setConfigLoading(false);
    }
  }, []);

  const loadExecution = useCallback(async () => {
    setExecutionLoading(true);
    setExecutionError("");
    try {
      const result = await api<AssistantExecution>(`projects/${encodeURIComponent(projectId)}/execution`);
      setExecution(result);
    } catch (error) {
      setExecution(null);
      setExecutionError(errorText(error));
    } finally {
      setExecutionLoading(false);
    }
  }, [projectId]);

  const loadConversations = useCallback(async (strict = false) => {
    const epoch=operations.epoch, token=(readTokens.current["loadConversations"]||0)+1;
    readTokens.current["loadConversations"]=token;
    setConversationsLoading(true);
    setConversationsError("");
    try {
      const result = await api<AssistantConversationSummary[]>(`projects/${encodeURIComponent(projectId)}/conversations`);
      if(epoch!==operations.epoch || token!==readTokens.current["loadConversations"]){if(strict===true)throw Error("Saved state changed during this read. Retry sync.");return;}
      setConversations(result);
    } catch (error) {
      if (strict === true) throw error;
      setConversationsError(errorText(error));
    } finally {
      setConversationsLoading(false);
    }
  }, [projectId]);

  const loadRecentRuns = useCallback(async (strict = false) => {
    const epoch=operations.epoch, token=(readTokens.current["loadRecentRuns"]||0)+1;
    readTokens.current["loadRecentRuns"]=token;
    setRecentRunsLoading(true);
    setRecentRunsError("");
    try {
      const result = await api<AssistantRun[]>(`projects/${encodeURIComponent(projectId)}/runs`);
      if(epoch!==operations.epoch || token!==readTokens.current["loadRecentRuns"]){if(strict===true)throw Error("Saved state changed during this read. Retry sync.");return;}
      setRecentRuns(result);
    } catch (error) {
      if (strict === true) throw error;
      setRecentRunsError(errorText(error));
    } finally {
      setRecentRunsLoading(false);
    }
  }, [projectId]);

  const loadConversation = useCallback(async (id: string) => {
    const epoch=operations.epoch, token=++conversationRead.current;
    const result = await api<AssistantConversation>(`conversations/${encodeURIComponent(id)}`);
    if (epoch!==operations.epoch || token!==conversationRead.current) throw new Error("Conversation changed during this read. Refresh the saved conversation.");
    if (result.project !== projectId) throw new Error("This conversation belongs to another project.");
    activateDraft(result.id,latestRun(result.runs));
    setConversation(result);
    setActiveRun(latestRun(result.runs) || null);
    setConversations((current) => {
      const existing = current.findIndex((item) => item.id === result.id);
      if (existing < 0) return [result, ...current];
      const next = [...current];
      next[existing] = result;
      return next.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    });
    return result;
  }, [projectId]);

  useEffect(()=>{
    const current=pendingTasks.get(projectId);
    if(current){pendingView.current=current;return;}
    const prior=pendingView.current;
    if(actionLocked||!prior)return;
    pendingView.current=null;pendingRequest.current=null;
    if(draft===prior.message)setDraft("");
    // A component reopened during the request must adopt its saved conversation too.
    if(prior.conversationId&&conversation?.id!==prior.conversationId){
      setConversationBusy(true);
      void loadConversation(prior.conversationId).then(()=>loadRecentRuns()).catch(error=>setConversationsError(errorText(error))).finally(()=>setConversationBusy(false));
    }
  },[actionLocked,projectId,loadConversation,loadRecentRuns]);

  async function assistantMutation<T>(config: Omit<Mutation<T>, "resources">) {
    return operations.run({...config,resources:actionResources});
  }

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  useEffect(() => {
    void loadExecution();
    void loadConversations();
    void loadRecentRuns();
    const timer = window.setInterval(() => {
      if (document.visibilityState !== "visible" || operations.locked(actionResources)) return;
      void loadExecution();
      void loadRecentRuns();
    }, PROJECT_POLL_MS);
    return () => window.clearInterval(timer);
  }, [loadExecution, loadConversations, loadRecentRuns]);

  useEffect(() => {
    const token=++detailRead.current, epoch=operations.epoch;
    if (!initialRunId) {
      setDetailRun(null);
      setRunEvents([]);
      setRunPollingError("");
      setRestorePreview(null);
      setRunActionError("");
      setRunActionNotice("");
      return;
    }
    setDetailRun(null);
    setRunEvents([]);
    setRestorePreview(null);
    setRunActionError("");
    setRunActionNotice("");
    void api<AssistantRun>(`runs/${encodeURIComponent(initialRunId)}`).then((run) => {
      if(token!==detailRead.current||epoch!==operations.epoch)return;
      if (run.project !== projectId) throw new Error("This run belongs to another project.");
      setDetailRun(run);
    }).catch((error: unknown) => {
      if(token===detailRead.current)setRunPollingError(errorText(error));
    });
  }, [initialRunId, projectId]);

  useEffect(() => {
    if (!watchedRunId) return;
    let stopped = false;
    let timer = 0;
    latestSeq.current = 0;
    setRunPollingError("");
    setRunEvents([]);
    let terminal = false;

    const poll = async () => {
      const epoch=operations.epoch;
      try {
        if (document.visibilityState !== "visible" || operations.locked(actionResources)) return;
        const result = await api<AssistantRunEvents>(`runs/${encodeURIComponent(watchedRunId)}/events?after_seq=${latestSeq.current}`);
        if (stopped || epoch!==operations.epoch) return;
        if (result.run.project !== projectId) throw new Error("This run belongs to another project.");
        for (const event of result.events) latestSeq.current = Math.max(latestSeq.current, event.seq);
        setRunEvents((current) => {
          const existing = new Set(current.map((event) => event.seq));
          return [...current, ...result.events.filter((event) => !existing.has(event.seq))].sort((a, b) => a.seq - b.seq);
        });
        setRunPollingError("");
        setActiveRun(result.run);
        if (initialRunId === watchedRunId) setDetailRun(result.run);
        terminal = TERMINAL_RUN_STATES.has(result.run.status);
        setRecentRuns((current) => [result.run, ...current.filter((run) => run.id !== result.run.id)]
          .sort((a, b) => b.updated_at.localeCompare(a.updated_at)));
        if (terminal) {
          void loadConversation(result.run.conversation_id).catch((error: unknown) => {
            setConversationsError(errorText(error));
          });
        }
      } catch (error) {
        if (stopped) return;
        setRunPollingError(errorText(error));
      } finally {
        if (!stopped && !terminal) timer = window.setTimeout(poll, RUN_POLL_MS);
      }
    };

    void poll();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [watchedRunId, initialRunId, projectId, loadConversation, pollingEpoch]);

  async function credentialWrite(method:"PUT"|"DELETE",body?:{api_key:string}):Promise<AssistantConfig> {
    try {return await api("credential",method,body);}
    catch(error){
      // Provider/validation details must never echo a credential into shared status text.
      if(error instanceof ApiError)throw new ApiError(error.status,"The key request failed. Check the key settings and try again.");
      throw new Error("The key response was interrupted. Check configured status before trying again.");
    }
  }

  const saveCredential = async (event: FormEvent) => {
    event.preventDefault();
    if(operations.locked(actionResources))return;
    return credentialGate.current.run(async()=>{
      if(!keyInput.trim()){setCredentialError("Enter an API key before saving it.");return;}
      const previouslyConfigured=!!config?.credential.configured;
      connectionEpoch.current++;setConnection({kind:"idle"});setCredentialBusy(true);setCredentialError("");
      try {
        await assistantMutation<AssistantConfig>({label:"Saving session key",completed:"Key saved",
          write:()=>credentialWrite("PUT",{api_key:keyInput.trim()}),
          confirmed:result=>{setConfig(result);setKeyInput("");},
          reconcile:async()=>{const result=await api<AssistantConfig>("config");if(previouslyConfigured||!result.credential.configured||result.credential.source!=="session")throw Error("Key replacement cannot be verified from secret-free status alone.");return result;},
          sync:async()=>{await loadConfig(true);},
        });
      } catch(error){setCredentialError(errorText(error));}
      finally{setCredentialBusy(false);}
    });
  };
  const clearCredential = async () => {
    if(operations.locked(actionResources))return;
    return credentialGate.current.run(async()=>{
      connectionEpoch.current++;setConnection({kind:"idle"});setCredentialBusy(true);setCredentialError("");
      try {
        await assistantMutation<AssistantConfig>({label:"Clearing session key",completed:"Key cleared",
          write:()=>credentialWrite("DELETE"),confirmed:result=>{setConfig(result);setKeyInput("");},
          reconcile:async()=>{const result=await api<AssistantConfig>("config");if(result.credential.source==="session")throw Error("Key clear is not confirmed.");return result;},
          sync:async()=>{await loadConfig(true);},
        });
      }catch(error){setCredentialError(errorText(error));}finally{setCredentialBusy(false);}
    });
  };

  const testConnection = async () => {
    if(operations.locked(actionResources))return;
    return connectionGate.current.run(async()=>{
      if(!selectedModel||credentialGate.current.busy)return;
      const epoch=++connectionEpoch.current;setConnection({kind:"testing",model:selectedModel});
      try {
        await assistantMutation<{connected:true;model:string}>({label:"Testing connection",completed:"Connection checked",
          write:async()=>{try{return await api("connection","POST",{model:selectedModel});}catch(error){throw new ApiError(422,errorText(error));}},
          confirmed:result=>{if(epoch===connectionEpoch.current)setConnection({kind:"connected",model:result.model});},
          sync:async()=>{const result=await api<AssistantConfig>("config");setConfig(result);},
        });
      }catch(error){if(epoch===connectionEpoch.current)setConnection({kind:"error",model:selectedModel,message:errorText(error)});}
    });
  };

  const createConversation = async () => {
    const created = await api<AssistantConversationSummary>(`projects/${encodeURIComponent(projectId)}/conversations`, "POST", {});
    setConversations((current) => [created, ...current.filter((item) => item.id !== created.id)]);
    storedDrafts.current[created.id]=draftState.current;
    if(pendingRequest.current)pendingRequest.current.conversationId=created.id;
    const opened = await loadConversation(created.id);
    setHistoryOpen(false);
    setSubmitNotice("");
    return opened;
  };

  const openConversation = async (item: AssistantConversationSummary) => {
    if(operations.locked(actionResources))return;
    setConversationBusy(true);
    setConversationsError("");
    setMessageError("");
    try {
      await loadConversation(item.id);
      if(initialRunId)onCloseRun();
      setHistoryOpen(false);
    } catch (error) {
      setConversationsError(errorText(error));
    } finally {
      setConversationBusy(false);
    }
  };

  const submitMessage = async (event: FormEvent) => {
    event.preventDefault();
    if(operations.locked(actionResources))return;
    return messageGate.current.run(async () => {
      const message = draft.trim();
      if (!message) return;
      if (connection.kind !== "connected" || connection.model !== selectedModel || !selectedModel) {
        setMessageError("Test the model connection before starting a task.");
        return;
      }
      if (mode === "Edit" && !editGateReady) {
        setMessageError("Edit runs need a current reviewed ticket and a Ready local workspace.");
        return;
      }
      const context:TaskRequestFields={message,model:selectedModel,mode,ticketId,roleId};
      if (pendingRequest.current && !sameTaskRequest(pendingRequest.current,context)) {
        setMessageError("A previous request may have reached the server. Retry with the original text, model, mode, ticket and role, or check History before starting a different task.");
        return;
      }
      setSubmitting(true);
      setMessageError("");
      setSubmitNotice("");
      if (!pendingRequest.current) pendingRequest.current = { id: crypto.randomUUID(), ...context };
      const attempt=pendingRequest.current;
      pendingTasks.set(projectId,attempt);pendingView.current=attempt;
      try {
        await assistantMutation<AssistantRun>({label:"Submitting task",completed:"Task saved",
          write:async()=>{
            const target=attempt.conversationId?await loadConversation(attempt.conversationId):conversation||await createConversation();
            attempt.conversationId=target.id;
            const body:{request_id:string;message:string;model:string;mode:"Read only"|"Edit";ticket_id?:string;role_id?:string}={request_id:attempt.id,message:attempt.message,model:attempt.model,mode:attempt.mode};
            if(attempt.mode==="Edit")body.ticket_id=attempt.ticketId;if(attempt.roleId)body.role_id=attempt.roleId;
            return api<AssistantRun>(`conversations/${encodeURIComponent(target.id)}/runs`,"POST",body);
          },
          reconcile:async()=>{
            // The existing journal exposes request_id; a read is enough to find a saved task.
            if(!attempt.conversationId){await loadConversations(true);throw Error("Conversation creation was interrupted; check history before starting again.");}
            const saved=await api<AssistantConversation>(`conversations/${encodeURIComponent(attempt.conversationId)}`);
            const found=saved.runs.find(run=>run.request_id===attempt.id);
            if(!found)throw Error("The submitted request is not yet confirmed.");return found;
          },
          confirmed:run=>{
            pendingRequest.current=null;pendingTasks.delete(projectId);setActiveRun(run);setDraft("");delete storedDrafts.current[activeDraftKey.current];
            if(storedDrafts.current.new?.message===message)delete storedDrafts.current.new;
            setSubmitNotice("Task saved. Run status will update from saved events.");
          },
          sync:async run=>{await loadConversation(run.conversation_id);await loadRecentRuns(true);await onRefreshWorkspace();},
        });
      } catch (error) {
        if(error instanceof ApiError&&!uncertainSubmission(error.status)){pendingRequest.current=null;pendingTasks.delete(projectId);pendingView.current=null;}
        setMessageError(errorText(error));
      } finally { setSubmitting(false); }
    });
  };

  const handleMessageKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (!submitsMessage(event.key,event.shiftKey,event.nativeEvent.isComposing,event.nativeEvent.keyCode)) return;
    event.preventDefault();
    event.currentTarget.form?.requestSubmit();
  };

  const refreshRun = async (id: string) => {
    const epoch=operations.epoch, token=++detailRead.current;
    const run = await api<AssistantRun>(`runs/${encodeURIComponent(id)}`);
    if(epoch!==operations.epoch||token!==detailRead.current)throw Error("Run state changed during this read. Retry sync.");
    setActiveRun(run);
    if (initialRunId === id) setDetailRun(run);
    setPollingEpoch((current) => current + 1);
    return run;
  };

  async function changeRun(action:"cancel"|"continue"|"restore") {
    if(!detailRun||operations.locked(actionResources))return;
    if(action==="restore"&&(!restorePreview||restorePreview.conflicts.length))return;
    const before=detailRun;
    return runGate.current.run(async()=>{
      setRunActionBusy(action);setRunActionError("");setRunActionNotice("");
      const labels={cancel:["Requesting cancellation","Cancellation request saved"],continue:["Continuing run","Continue request saved"],restore:["Restoring run","Restored"]};
      try {
        await assistantMutation<AssistantRun>({label:labels[action][0],completed:labels[action][1],
          write:()=>api(`runs/${encodeURIComponent(before.id)}/${action}`,"POST",{}),
          reconcile:async()=>{
            const result=await api<AssistantRun>(`runs/${encodeURIComponent(before.id)}`);
            const changed=result.updated_at!==before.updated_at;
            const applied=action==="restore"?result.last_confirmed_step==="Selected run changes restored":action==="cancel"?(result.status==="Cancelled"||!!result.cancelled):changed&&["Queued","Running","Completed","Failed"].includes(result.status);
            if(!applied)throw Error("The request outcome is not confirmed. Review saved events before retrying.");return result;
          },
          confirmed:run=>{setDetailRun(run);setActiveRun(run);setRestorePreview(null);setPollingEpoch(value=>value+1);setRunActionNotice(action==="cancel"?"Cancellation request saved. The run status will confirm when work stops.":action==="continue"?"Continue request saved. Status will update from saved events.":"Restore completed for this run.");},
          sync:async()=>{await refreshRun(before.id);await loadRecentRuns(true);await onRefreshWorkspace();},
        });
      }catch(error){setRunActionError(errorText(error));try{await refreshRun(before.id);}catch{/* Keep the last confirmed step. */}}
      finally{setRunActionBusy("");}
    });
  }
  const cancelRun=()=>changeRun("cancel");
  const continueRun=()=>changeRun("continue");

  const previewRestore = async () => {
    if(!detailRun||operations.locked(actionResources))return;
    const id=detailRun.id;
    return runGate.current.run(async()=>{
      setRunActionBusy("preview");setRunActionError("");setRunActionNotice("");setRestorePreview(null);
      try {
        await assistantMutation<AssistantRestorePreview>({label:"Checking restore conflicts",completed:"Restore preview loaded",
          // This endpoint previews only; it never restores user files. Failed previews can be requested again.
          write:async()=>{try{return await api(`runs/${encodeURIComponent(id)}/restore-preview`,"POST",{});}catch(error){throw new ApiError(422,errorText(error));}},
          confirmed:preview=>setRestorePreview(preview),sync:async()=>{await refreshRun(id);},
        });
      }catch(error){setRunActionError(errorText(error));}finally{setRunActionBusy("");}
    });
  };
  const restoreRun=()=>changeRun("restore");

  const decideScope = async (review: ChangeReview, accept: boolean) => {
    if(operations.locked(actionResources))return;
    return scopeGate.current.run(async()=>{
      setReviewBusy(review.id);setReviewErrors(current=>({...current,[review.id]:""}));
      const expected=accept?(review.findings.some(item=>item.outcome==="Update required")?"Needs updates":"Confirmed"):"Declined";
      const verified=(data:Workspace)=>data.reviews.some(item=>item.id===review.id&&!item.superseded&&item.status===expected);
      try {
        await assistantMutation({label:"Saving scope decision",completed:"Scope decision saved",
          write:()=>request(`reviews/${encodeURIComponent(review.id)}/confirm`,"POST",{revision:review.revision,accept,note:accept?"User confirmed this scope change in InApp Assistant.":"User kept the existing scope in InApp Assistant."}),
          reconcile:async()=>{const data=await request<Workspace>(workspacePath(projectId));if(!verified(data))throw Error("Scope decision not confirmed.");},
          confirmed:()=>setReviewDecisions(current=>({...current,[review.id]:accept?"Scope change confirmed.":"Existing scope kept."})),
          sync:()=>onRefreshWorkspace(verified),
        });
      }catch(error){setReviewErrors(current=>({...current,[review.id]:errorText(error)}));}
      finally{setReviewBusy("");}
    });
  };

  const conversationTitle = conversation?.title || "New conversation";
  const displayRun = detailRun || visibleRun;
  const currentReviewStatus = selectedReview?.status || "No current review";
  const scopeProposals = useMemo(() => db.reviews
    .filter((review) => review.project === projectId && review.status === "Awaiting confirmation" && !review.superseded)
    .sort((a, b) => Number(b.subject === ticketId) - Number(a.subject === ticketId) || b.updated_at.localeCompare(a.updated_at)), [db.reviews, projectId, ticketId]);
  const visibleScopeProposals = showAllScopeProposals ? scopeProposals : scopeProposals.slice(0, 3);
  const connectionLabel = connection.kind === "connected"
    ? `Connected · ${connection.model || selectedModel}`
    : connection.kind === "testing" ? "Testing connection"
      : connection.kind === "error" ? "Connection failed"
        : config?.credential.configured ? "Not tested" : "No key configured";

  return <div className="ia-page">
    <div className="ia-layout">
      <aside className="ia-rail" aria-label="Assistant navigation">
        <Button variant="default" onClick={newChat} disabled={actionLocked||submitting||conversationBusy}>New chat</Button>
        <Tabs value={railTab} onChange={setRailTab} keepMounted={false}>
          <Tabs.List aria-label="Assistant navigation" onKeyDownCapture={event=>{
            if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
            const tabs=Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
            const current=tabs.indexOf(document.activeElement as HTMLButtonElement);
            const next=event.key==="Home"?0:event.key==="End"?tabs.length-1:(current+(event.key==="ArrowRight"?1:-1)+tabs.length)%tabs.length;
            event.preventDefault();event.stopPropagation();setRailTab(next===0?"history":"runs");tabs[next]?.focus();
          }}><Tabs.Tab value="history">Chat History</Tabs.Tab><Tabs.Tab value="runs">Assistant runs</Tabs.Tab></Tabs.List>
          <Tabs.Panel value="history"><div className="ia-nav-list">
            {conversationsLoading&&!conversations.length&&<p>Loading conversations…</p>}
            {conversationsError&&<p role="alert">{conversationsError}<button onClick={()=>void loadConversations()}>Retry</button></p>}
            {conversations.slice(0,8).map(item=><button key={item.id} type="button" aria-current={conversation?.id===item.id?"true":undefined} disabled={actionLocked||submitting||conversationBusy} onClick={()=>void openConversation(item)}><strong>{item.title||"Untitled conversation"}</strong><small>{stamp(item.updated_at)}</small></button>)}
            {!conversationsLoading&&!conversations.length&&<Empty>No saved conversations.</Empty>}
          </div><button className="ia-text-link" onClick={()=>setHistoryOpen(true)}>View all chats</button></Tabs.Panel>
          <Tabs.Panel value="runs">        <section className="ia-card ia-recent" aria-labelledby="ia-recent-title">
          <div className="ia-card-head">
            <h2 id="ia-recent-title">Runs started here</h2>
            <button className="ia-text-link" type="button" onClick={onShowRuns}>All project runs <Icon page="arrow" /></button>
          </div>
          {recentRunsError && <div className="ia-inline-error" role="alert">{recentRunsError}<button type="button" onClick={() => void loadRecentRuns()}>Retry</button></div>}
          {recentRunsLoading && !recentRuns.length && <p className="ia-loading">Loading recent runs…</p>}
          {!recentRunsLoading && !recentRunsError && !recentRuns.length && <>
            <Empty>No runs have been started in this project’s Assistant. Find Codex and Claude Code reports in all project runs.</Empty>
            <button className="ia-text-link" type="button" onClick={onShowRuns}>All project runs <Icon page="arrow" /></button>
          </>}
          {!!recentRuns.length && <div className="ia-recent-scroll" role="region" aria-label="Recent assistant runs" tabIndex={0}>
            <table className="ia-run-table">
              <thead><tr><th scope="col">Task</th><th scope="col">Agent / model</th><th scope="col">Status</th></tr></thead>
              <tbody>{recentRuns.slice(0, 8).map((run) => {
                const task = run.name || recentConversations.get(run.conversation_id) || tickets.find((ticket) => ticket.id === run.ticket_id)?.name || "Conversation";
                return <tr key={run.id}>
                  <td><button type="button" className="ia-run-task" disabled={actionLocked} onClick={() => onOpenRun(run.id)}>{task}</button></td>
                  <td>{run.role_name || run.model}</td>
                  <td><Tag value={run.status} /></td>
                </tr>;
              })}</tbody>
            </table>
          </div>}
        </section>
</Tabs.Panel>
        </Tabs>
      </aside>

      <section className="ia-chat-card" aria-label="Project conversation">
        <header className="ia-chat-head"><h1>{initialRunId?"Run details":conversationTitle}</h1><button className="ia-text-link" type="button" onClick={onShowRuns}>All project runs</button></header>



        {initialRunId ? <RunDetails
          db={db}
          run={detailRun}
          events={runEvents}
          pollingError={runPollingError}
          loading={!detailRun && !runPollingError}
          actionError={runActionError}
          actionNotice={runActionNotice}
          actionBusy={runActionBusy || (actionLocked ? "syncing" : "")}
          preview={restorePreview}
          onBack={onCloseRun}
          onRefresh={() => void refreshRun(initialRunId).catch((error: unknown) => setRunPollingError(errorText(error)))}
          onCancel={() => void cancelRun()}
          onContinue={() => void continueRun()}
          onPreviewRestore={() => void previewRestore()}
          onRestore={() => void restoreRun()}
          onOpenTicket={onOpenTicket}
          reliabilityNotice={config?.notice || RELIABILITY_NOTICE}
        /> : <>
          <div className="ia-conversation-bar">
            <span>{activeConversation ? `Saved · updated ${stamp(activeConversation.updated_at)}` : "New project conversation"}</span>
            <span className={`ia-connection is-${connection.kind}`}><i aria-hidden="true" />{connectionLabel}</span>
          </div>
          <div className="ia-transcript" role="log" aria-label="Conversation messages" aria-relevant="additions text">
            {!conversation && <div className="ia-empty-chat">
              <span className="ia-empty-icon"><Icon page="runs" /></span>
              <div className="with-info"><h2>What needs work?</h2><InfoHelp label="project conversations">{`Ask a read-only project question or describe a reviewed ticket to edit. This conversation and its run history belong to ${projectName}.`}</InfoHelp></div>
            </div>}
            {conversation?.messages.map((message) => <article key={message.id} className={`ia-message is-${message.role === "user" ? "user" : "assistant"}`}>
              <div className="ia-message-meta"><strong>{roleLabel(message)}</strong><time dateTime={message.created_at}>{stamp(message.created_at)}</time></div>
              <p>{message.content}</p>
              {message.run_id && <button type="button" className="ia-text-link" onClick={() => onOpenRun(message.run_id!)}>Open saved run details <Icon page="arrow" /></button>}
            </article>)}
            {!!scopeProposals.length && <section className="ia-scope-proposals" aria-labelledby="ia-scope-proposals-title">
              <div className="ia-scope-proposals-head"><div><span className="ia-kicker">Your decision needed</span><h2 id="ia-scope-proposals-title">Proposed scope changes</h2></div><span>{scopeProposals.length}</span></div>
              <div id="ia-scope-proposal-list" className="ia-scope-list">{visibleScopeProposals.map((review) => <article className="ia-scope-card" key={review.id}>
                <div className="ia-scope-title"><strong>{review.snapshot.subject.name}</strong><Tag value={review.status} /></div>
                <p><span>Requested change</span>{review.request}</p>
                <p><span>Why this changes scope</span>{review.rationale}</p>
                <ReviewSnapshot key={review.id + ':' + review.revision} project={projectId} id={review.id}
                  label={`Affected sources (${review.snapshot.documents.length})`}/>
                {reviewErrors[review.id] && <p className="ia-inline-error" role="alert">{reviewErrors[review.id]}</p>}
                {reviewDecisions[review.id] ? <p className="ia-success-note" role="status">{reviewDecisions[review.id]} The updated review is saved in Runs &amp; activity.</p> : <div className="ia-scope-actions">
                  <Button type="button" size="sm" loading={reviewBusy === review.id} disabled={actionLocked || !!reviewBusy} onClick={() => void decideScope(review, true)}>Confirm this scope change</Button>
                  <Button type="button" size="sm" variant="default" loading={reviewBusy === review.id} disabled={actionLocked || !!reviewBusy} onClick={() => void decideScope(review, false)}>Keep existing scope</Button>
                </div>}
              </article>)}</div>
              {scopeProposals.length > 3 && <button type="button" className="ia-text-link" aria-expanded={showAllScopeProposals} aria-controls="ia-scope-proposal-list" onClick={() => setShowAllScopeProposals((value) => !value)}>
                {showAllScopeProposals ? "Show fewer proposals" : `Show all ${scopeProposals.length} proposals`}
              </button>}
            </section>}
            {displayRun && <RunCard db={db} run={displayRun} title={displayRun.name || recentConversations.get(displayRun.conversation_id) || conversation?.title || "Assistant task"} onOpen={() => {if(!operations.locked(actionResources))onOpenRun(displayRun.id);}} onOpenTicket={onOpenTicket} />}
            {runPollingError && watchedRunId && <p className="ia-poll-warning" role="status">Could not refresh saved run events. Last confirmed status remains {displayRun?.status || "unknown"}. {runPollingError}</p>}
          </div>
          <form className="ia-composer" aria-busy={actionLocked} onSubmit={(event) => void submitMessage(event)} aria-labelledby="ia-composer-title">
            <h2 id="ia-composer-title" className="ia-sr-only">Send a project task</h2>
            {mode === "Edit" && <div className={`ia-gate-note ${editGateReady ? "is-ready" : "is-waiting"}`} role="status">
              {editGateReady
                ? `Ticket review: ${currentReviewStatus}. Backend checks Git and local file access again when the run starts.`
                : <>{!selectedTicket ? "Choose a ticket with a current Ready or Confirmed review." : `Ticket review: ${currentReviewStatus}. Edit is available after the review is current and local execution is Ready.`} {execution?.status !== "Ready" && `Local execution: ${execution?.status || "checking"}.`}<button type="button" className="ia-text-link" onClick={onShowTickets}>{selectedTicket ? "Review tickets" : "Open Tickets"} <Icon page="arrow" /></button></>}
            </div>}
            <div className="ia-compose-row">
              <Textarea
                name="message"
                aria-label="Message to the assistant"
                placeholder={connection.kind === "connected" ? "Message the assistant about this project…" : "Write a draft. Connect a model to send it."}
                autosize
                minRows={2}
                maxRows={6}
                value={draft}
                onChange={(event) => { setDraft(event.currentTarget.value); setMessageError(""); }}
                onKeyDown={handleMessageKeyDown}
                disabled={actionLocked || submitting || conversationBusy}
                ref={describeWithHelp("ia-composer-help")}
              />

            </div>
            <div className="ia-compose-tools"><button ref={settingsButton} type="button" className="ia-model-settings" aria-label="Assistant settings" aria-haspopup="dialog" aria-expanded={settingsOpen} onClick={()=>setSettingsOpen(true)}><span>{selectedModel||"Model settings"}</span><span aria-hidden="true">⚙</span></button><span className="ia-task-mode">{mode}</span><InfoHelp label="sending messages" id="ia-composer-help">Press Enter to send. Shift+Enter adds a line. The API must pass the ticket, review, Git, and workspace checks before editing.</InfoHelp><Button className="ia-send" type="submit" aria-label="Start task" title="Start task" loading={submitting} disabled={actionLocked || !draft.trim()||connection.kind!=="connected"||(mode==="Edit"&&!editGateReady)}><Icon page="arrow"/></Button></div>
            <div className="ia-composer-foot">
              {(messageError || submitNotice) && <p className={messageError ? "ia-inline-error" : "ia-success-note"} role={messageError ? "alert" : "status"}>{messageError || submitNotice}</p>}
              <p className="ia-reliability" role="note"><Icon page="warning" />{RELIABILITY_NOTICE}</p>
            </div>
          </form>
        </>}
      </section>
    </div>
    <Modal opened={settingsOpen} onClose={closeSettings} title="Assistant settings" closeButtonProps={{"aria-label":"Close Assistant settings"}} size="min(620px,95vw)" className="ia-settings">
      <OperationFeedback />
        <section className="ia-card ia-config" aria-labelledby="ia-config-title">
          <div className="ia-card-head">
            <h2 id="ia-config-title">Model</h2>
            <span className={`ia-connection is-${connection.kind}`}><i aria-hidden="true" />{connectionLabel}</span>
          </div>
          {configLoading && <p className="ia-loading">Loading model settings…</p>}
          {configError && <div className="ia-inline-error" role="alert">{configError}<button type="button" onClick={() => void loadConfig()}>Retry</button></div>}
          {config && <>
            <div className="field-info"><label className="ia-label" htmlFor="ia-model">Provider and model</label><InfoHelp label="model connection" id="ia-model-help">Test the selected model before sending a task.</InfoHelp></div>
            <NativeSelect
              id="ia-model"
              name="model"
              value={selectedModel}
              data={config.models.map((item) => ({ value: item.id, label: item.name }))}
              disabled={actionLocked || !config.models.length || connection.kind === "testing" || credentialBusy || submitting}
              onChange={(event) => {
                const next = event.currentTarget.value;
                connectionEpoch.current++;
                setSelectedModel(next);
                if (connection.model !== next) setConnection({ kind: "idle" });
              }}
              ref={describeWithHelp("ia-model-help")}
            />
            <p className="ia-help">Provider: {config.provider}</p>

            <div className="ia-credential-state" role="status">
              <strong>{config.credential.configured ? "API key configured" : "API key not configured"}</strong>
              <span>{config.credential.source === "environment" ? "Supplied by the Docker environment. Replace it in .env and restart Docker." : config.credential.source === "session" ? "Held in backend process memory. It must be entered again after a backend restart." : "The key is held only in backend process memory after saving."}</span>
            </div>

            {config.credential.source !== "environment" && <form className="ia-key-form" onSubmit={saveCredential}>
              <div className="field-info"><label htmlFor="ia-api-key">{config.credential.configured ? "Replace session key" : "OpenAI API key"}</label><InfoHelp label="API key entry" id="ia-key-help">This field clears after saving. The key is not kept in browser storage or chat.</InfoHelp></div>
              <PasswordInput
                id="ia-api-key"
                name="api_key"
                disabled={actionLocked || credentialBusy || submitting || connection.kind === "testing"}
                autoComplete="new-password"
                spellCheck={false}
                value={keyInput}
                onChange={(event) => setKeyInput(event.currentTarget.value)}
                error={credentialError || undefined}
                ref={describeWithHelp("ia-key-help")}
              />
              <Button type="submit" size="sm" loading={credentialBusy} disabled={actionLocked || !keyInput.trim() || submitting || connection.kind === "testing"}>
                {config.credential.configured ? "Replace key" : "Save key in session"}
              </Button>
              {config.credential.source === "session" && <Button type="button" size="sm" variant="default" loading={credentialBusy} disabled={actionLocked || submitting || connection.kind === "testing"} onClick={() => void clearCredential()}>Clear session key</Button>}
            </form>}
            {config.credential.source === "environment" && credentialError && <p className="ia-inline-error" role="alert">{credentialError}</p>}
            <div className="ia-connect-actions">
              <Button type="button" size="sm" loading={connection.kind === "testing"} disabled={actionLocked || !config.credential.configured || !selectedModel || connection.kind === "testing" || credentialBusy || submitting} onClick={() => void testConnection()}>
                Test connection
              </Button>
              <InfoHelp label="connection tests">Connection test is separate from local execution.</InfoHelp>
            </div>
            {connection.kind === "error" && connection.message && <p className="ia-inline-error" role="alert">{connection.message}</p>}
          </>}
        </section>

        <section className="ia-card ia-execution" aria-labelledby="ia-execution-title">
          <div className="ia-card-head">
            <div className="with-info"><h2 id="ia-execution-title">Local execution</h2><InfoHelp label="local execution">File changes, build checks, and restore stay disabled until the backend reports Ready.</InfoHelp></div>
            {execution && <Tag value={execution.status} />}
          </div>
          {executionLoading && <p className="ia-loading">Checking the project mount…</p>}
          {executionError && <div className="ia-inline-error" role="alert">{executionError}<button type="button" onClick={() => void loadExecution()}>Retry</button></div>}
          {execution && <>
            <p className="ia-execution-message">{execution.message}</p>
            <dl className="ia-paths">
              <div><dt>Host folder</dt><dd>{projectPath(execution.host_folder)}</dd></div>
              <div><dt>Project path</dt><dd>{projectPath(execution.project_path)}</dd></div>
              <div><dt>Container</dt><dd>{execution.container_folder || "/workspaces"}</dd></div>
              <div><dt>Access</dt><dd>{execution.access || "Not available"}</dd></div>
            </dl>
            <button className="ia-instructions-toggle" type="button" aria-expanded={executionExpanded} aria-controls="ia-execution-instructions" onClick={() => setExecutionExpanded((value) => !value)}>
              <span>{execution.status === "Ready" ? "View setup details" : "Set up local execution"}</span><Icon page="arrow" />
            </button>
            {executionExpanded && <div id="ia-execution-instructions" className="ia-instructions">
              <p>The host helper applies a Docker mount. A browser path cannot grant file access. Choose the host folder in the host setup command, then restart and let the backend verify the mapping.</p>
              {execution.setup_command && <pre><code>{execution.setup_command}</code></pre>}
            </div>}
          </>}
        </section>

<section className="ia-card"><h2>Task options</h2>            <fieldset className="ia-mode-fieldset" disabled={actionLocked || submitting}>
              <legend>Run mode</legend>
              <label><input type="radio" name="run-mode" value="Read only" checked={mode === "Read only"} onChange={() => { setMode("Read only"); setMessageError(""); }} />Read only</label>
              <label><input type="radio" name="run-mode" value="Edit" checked={mode === "Edit"} onChange={() => { setMode("Edit"); setMessageError(""); }} />Edit</label>
            </fieldset>
            <div className="ia-composer-options">
              {mode === "Edit" && <div className="ia-option-field">
                <label htmlFor="ia-ticket">Reviewed ticket</label>
                <select id="ia-ticket" name="ticket_id" disabled={actionLocked || submitting} value={ticketId} onChange={(event) => setTicketId(event.currentTarget.value)} required>
                  <option value="">Choose a project ticket</option>
                  {tickets.map((ticket) => {
                    const review = currentReview(db, ticket.id);
                    return <option key={ticket.id} value={ticket.id}>{ticket.name} · {review?.status || "No current review"}</option>;
                  })}
                </select>
              </div>}
              <div className="ia-option-field">
                <label htmlFor="ia-role">Role <span>(optional)</span></label>
                <select id="ia-role" name="role_id" disabled={actionLocked || submitting} value={roleId} onChange={(event) => setRoleId(event.currentTarget.value)}>
                  <option value="">No role</option>
                  {roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
                </select>
              </div>
            </div>
</section>
    </Modal>
    <Modal opened={historyOpen} onClose={()=>setHistoryOpen(false)} title="Conversation history" closeButtonProps={{"aria-label":"Close conversation history"}} size="min(620px,95vw)">        <section id="ia-history" className="ia-history" aria-label="Project conversation history">
          <div className="ia-history-head"><div><strong>History</strong><span>{conversations.length} conversations in this project</span></div><button type="button" className="ia-text-link" onClick={() => void loadConversations()}>Refresh</button></div>
          {conversationsLoading && !conversations.length && <p className="ia-loading">Loading history…</p>}
          {conversationsError && <div className="ia-inline-error" role="alert">{conversationsError}<button type="button" onClick={() => void loadConversations()}>Retry</button></div>}
          {!conversationsLoading && !conversationsError && !conversations.length && <Empty>No saved conversations for this project.</Empty>}
          {!!conversations.length && <ul className="ia-history-list">{conversations.map((item) => <li key={item.id}>
            <button type="button" className={conversation?.id === item.id ? "is-current" : ""} disabled={actionLocked || conversationBusy || submitting} onClick={() => void openConversation(item)}>
              <span>{item.title || "Untitled conversation"}</span><small>{stamp(item.updated_at)}</small><Icon page="arrow" />
            </button>
          </li>)}</ul>}
        </section></Modal>
  </div>;
}

function RunCard({ db, run, title, onOpen, onOpenTicket }: { db:Workspace; run: AssistantRun; title: string; onOpen: () => void; onOpenTicket: (id: string) => void }) {
  const ticket=db.tickets.find(t=>t.id===run.ticket_id&&t.project===run.project);
  return <article className="ia-task-card" aria-label="Saved assistant task">
    <div className="ia-task-head"><div><span className="ia-kicker">Task</span><strong>{title}</strong></div><span>Run status <Tag value={run.status} /></span></div>
    <div className="ia-task-meta">Mode: {run.mode} · Model: {run.model} · Run role: {run.role_name||"Not recorded"}</div>
    {ticket?<div className="ia-linked-work"><span>Ticket status</span><TicketSummary db={db} ticket={ticket} status open={()=>onOpenTicket(ticket.id)}/></div>:<p>{run.ticket_id?"Linked ticket unavailable":"Project task · No linked ticket"}</p>}
    {run.last_confirmed_step && <p className="ia-last-step"><span>Last confirmed step</span>{run.last_confirmed_step}</p>}
    <div className="ia-task-actions">
      {run.ticket_id && <button type="button" className="ia-text-link" onClick={() => onOpenTicket(run.ticket_id!)}>View ticket <Icon page="arrow" /></button>}
      <button type="button" className="ia-text-link" onClick={onOpen}>View run details <Icon page="arrow" /></button>
    </div>
  </article>;
}

function RunDetails({
  db,
  run,
  events,
  pollingError,
  loading,
  actionError,
  actionNotice,
  actionBusy,
  preview,
  onBack,
  onRefresh,
  onCancel,
  onContinue,
  onPreviewRestore,
  onRestore,
  onOpenTicket,
  reliabilityNotice,
}: {
  db: Workspace;
  run: AssistantRun | null;
  events: AssistantRunEvent[];
  pollingError: string;
  loading: boolean;
  actionError: string;
  actionNotice: string;
  actionBusy: string;
  preview: AssistantRestorePreview | null;
  onBack: () => void;
  onRefresh: () => void;
  onCancel: () => void;
  onContinue: () => void;
  onPreviewRestore: () => void;
  onRestore: () => void;
  onOpenTicket: (id: string) => void;
  reliabilityNotice: string;
}) {
  if (loading) return <div className="ia-run-detail-state"><p>Loading saved run details…</p></div>;
  if (!run) return <div className="ia-run-detail-state" role="alert"><p>The run details are unavailable.</p>{pollingError && <p>{pollingError}</p>}<button type="button" className="ia-text-link" disabled={!!actionBusy} onClick={onRefresh}>Retry</button><button type="button" className="ia-text-link" disabled={!!actionBusy} onClick={onBack}>Back to conversation</button></div>;
  const ticket=db.tickets.find(t=>t.id===run.ticket_id&&t.project===run.project);
  const expires=run.restore_point?.expires_at;
  const expired=!!expires&&Number.isFinite(Date.parse(expires))&&Date.parse(expires)<=Date.now();
  const restoreAvailable=run.mode==="Edit"&&!!run.restore_point&&!expired;
  const active = ["Queued", "Running"].includes(run.status);
  const recoverable = ["Blocked", "Failed", "Waiting for input"].includes(run.status);
  return <div className="ia-run-detail">
    <div className="ia-detail-toolbar"><button type="button" className="ia-text-link" disabled={!!actionBusy} onClick={onBack}><Icon page="arrow" />Back to conversation</button><button type="button" className="ia-text-link" disabled={!!actionBusy} onClick={onRefresh}>Refresh saved state</button></div>
    <header className="ia-detail-head">
      <div><span className="ia-kicker">Run details</span><h2>{run.name || (run.ticket_id ? "Ticket task" : "Project task")}</h2><p>{run.mode} · {run.role_name || run.model} · started {stamp(run.created_at)}</p></div>
      <span>Run status <Tag value={run.status} /></span>
    </header>
    <dl className="ia-run-facts"><div><dt>Run role</dt><dd>{run.role_name||"Not recorded"}</dd></div><div><dt>Model</dt><dd>{run.model}</dd></div><div><dt>Mode</dt><dd>{run.mode}</dd></div></dl>
    {ticket?<section className="ia-linked-work" aria-label="Linked ticket"><span>Ticket status</span><TicketSummary db={db} ticket={ticket} status open={()=>onOpenTicket(ticket.id)}/></section>:<Empty>{run.ticket_id?"Linked ticket unavailable.":"Project task · No linked ticket."}</Empty>}
    {recoverable&&<p className="ia-needs-review" role="status">Needs review. Check the last confirmed step before Continue or Restore. No editing action is retried automatically.</p>}
    <section className="ia-detail-card" aria-labelledby="ia-last-step-title">
      <div className="ia-card-head"><h3 id="ia-last-step-title">Last confirmed step</h3>{run.last_confirmed_step && <span className="ia-detail-time">Updated {stamp(run.updated_at)}</span>}</div>
      <p className="ia-step-copy">{run.last_confirmed_step || "No confirmed step has been saved yet."}</p>
      {run.error && <p className="ia-run-error" role="alert">{run.error}</p>}
      {pollingError && <p className="ia-poll-warning" role="status">The browser cannot reach saved run events. The status below is the last server response: {pollingError}</p>}
    </section>

    <div className="ia-detail-grid">
      <section className="ia-detail-card" aria-labelledby="ia-files-title">
        <div className="ia-card-head"><h3 id="ia-files-title">Changed files</h3><span>{run.changed_files?.length || 0}</span></div>
        {run.changed_files?.length ? <ul className="ia-file-list">{run.changed_files.map((file) => <li key={file}><code>{file}</code></li>)}</ul> : <Empty>No changed files reported.</Empty>}
      </section>
      <section className="ia-detail-card" aria-labelledby="ia-checks-title">
        <div className="ia-card-head"><h3 id="ia-checks-title">Checks and evidence</h3><span>{run.checks?.length || 0}</span></div>
        {run.checks?.length ? <ul className="ia-check-list">{run.checks.map((check, index) => <li key={`${index}-${checkLabel(check, index)}`}>
          <div><strong>{checkLabel(check, index)}</strong><span>{checkResult(check)}</span></div>
          {typeof check !== "string" && typeof check.output === "string" && !!check.output && <details><summary>Check output</summary><pre>{check.output}</pre></details>}
        </li>)}</ul> : <Empty>No checks reported.</Empty>}
      </section>
    </div>

    <section className="ia-detail-card" aria-labelledby="ia-events-title">
      <div className="ia-card-head"><h3 id="ia-events-title">Saved run events</h3><span>{events.length}</span></div>
      {events.length ? <ol className="ia-event-list">{events.map((event) => <li key={event.seq}>
        <time dateTime={event.created_at}>{stamp(event.created_at)}</time><strong>{statusLabel(event.type)}</strong>{eventDetail(event) && <p>{eventDetail(event)}</p>}
      </li>)}</ol> : <Empty>No saved events received yet.</Empty>}
    </section>

    {ticket?.output_documents?.length ? <section className="ia-detail-card"><h3>Output evidence</h3><ul>{ticket.output_documents.map(id=><li key={id}><a href={"#documents/"+id}>{db.documents.find(d=>d.id===id)?.name||"Evidence document unavailable"}</a></li>)}</ul></section>:null}
    {!run.restore_point&&<p className="ia-help">{run.mode==="Read only"?"Read-only run. No file restore point was created.":"No restore point is recorded. File restore is unavailable."}</p>}
    {expired&&<p className="ia-inline-error" role="status">This restore point expired. File restore is unavailable.</p>}
    {run.restore_point && <section className="ia-detail-card ia-restore-policy" aria-labelledby="ia-restore-title">
      <div className="ia-card-head"><h3 id="ia-restore-title">Restore point</h3><span>Retained for two calendar months</span></div>
      <p>Created {stamp(run.restore_point.created_at || run.created_at)}{run.restore_point.expires_at ? ` · expires ${stamp(run.restore_point.expires_at)}` : ""}. Restore affects only this run.</p>
    </section>}

    <section className="ia-recovery" aria-labelledby="ia-recovery-title">
      <div><h3 id="ia-recovery-title">Recovery actions</h3><p>Review the saved step, file changes, checks, and conflicts before continuing or restoring this run.</p></div>
      <div className="ia-recovery-actions">
        {active && <Button type="button" variant="default" loading={actionBusy === "cancel"} disabled={!!actionBusy} onClick={onCancel}>Cancel run</Button>}
        {recoverable && <Button type="button" loading={actionBusy === "continue"} disabled={!!actionBusy} onClick={onContinue}>Continue</Button>}
        {restoreAvailable && !active && <Button type="button" variant="default" loading={actionBusy === "preview"} disabled={!!actionBusy} onClick={onPreviewRestore}>Review restore conflicts</Button>}
      </div>
      {run.restore_point && active && <p className="ia-help">Stop or finish this run before reviewing restore conflicts.</p>}
      {actionError && <p className="ia-inline-error" role="alert">{actionError}</p>}
      {actionNotice && <p className="ia-success-note" role="status">{actionNotice}</p>}
      <p className="ia-reliability" role="note"><Icon page="warning" />{reliabilityNotice}</p>
      {preview && <div className={`ia-restore-preview ${preview.conflicts.length ? "has-conflicts" : ""}`}>
        <strong>{preview.conflicts.length ? "Restore conflicts need review" : "Restore preview"}</strong>
        <div className="ia-preview-columns">
          <div><span>Changes to restore</span>{preview.changes.length ? <ul>{preview.changes.map((item) => <li key={item}><code>{item}</code></li>)}</ul> : <p>No changes are listed for this run.</p>}</div>
          <div><span>Conflicts</span>{preview.conflicts.length ? <ul>{preview.conflicts.map((item) => <li key={item}><code>{item}</code></li>)}</ul> : <p>No overlapping changes found.</p>}</div>
        </div>
        {restoreAvailable && !active && !preview.conflicts.length && preview.changes.length > 0 && <Button type="button" color="red" loading={actionBusy === "restore"} disabled={!!actionBusy} onClick={onRestore}>Restore this run</Button>}
      </div>}
    </section>
  </div>;
}
