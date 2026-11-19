import { useWorkspace } from "../app/WorkspaceContext";
export function PreviewToolbar() {
  const { preview, setPreview, failNext, setFailNext, reset, mode } = useWorkspace();
  if (mode !== "mock") return null;
  return (
    <div className="preview-toolbar">
      <strong>AgentBoard · Interface preview</strong>
      <span>Mock data · changes stay in memory</span>
      <label htmlFor="previewtoolbar-1">
        Preview state
        <select
          id="previewtoolbar-1"
          aria-label="Preview state"
          value={preview}
          onChange={(e) => setPreview(e.target.value as typeof preview)}
        >
          {[
            "Ready",
            "Loading",
            "Empty",
            "Error",
            "Conflict",
            "Disconnected",
          ].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>
      <label htmlFor="previewtoolbar-2" className="check-label">
        <input
          id="previewtoolbar-2"
          type="checkbox"
          checked={failNext}
          onChange={(e) => setFailNext(e.target.checked)}
        />
        Fail next operation
      </label>
      <button onClick={reset}>Reset samples</button>
      <small>Pending review</small>
    </div>
  );
}
