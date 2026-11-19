import { SaveFailureControl } from "../../components/SaveFailureControl";
import { useState } from "react";
import { Role } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export function RoleForm({
  role,
  onSaved,
}: {
  role?: Role;
  onSaved: () => void;
}) {
  const { projectId, saveRole, setDirty, mode } = useWorkspace();
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState(role?.name || "");
  const [responsibilities, setResponsibilities] = useState(
    role?.responsibilities || "",
  );
  const [error, setError] = useState("");
  return (
    <form
      noValidate
      aria-label="role form"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!name.trim() || !responsibilities.trim()) {
          setError("Name and responsibilities are required.");
          e.currentTarget
            .querySelector<HTMLElement>(!name.trim() ? "input" : "textarea")
            ?.focus();
          return;
        }
        setSaving(true);
        try { await saveRole({ name: name.trim(), responsibilities: responsibilities.trim() }, role); onSaved(); }
        catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save role. Your draft is retained."); }
        finally { setSaving(false); }
      }}
    >
      <label htmlFor="roleform-1">
        Role name <span aria-hidden="true">*</span>
        <input
          id="roleform-1"

          required
          aria-invalid={!!error && !name.trim()}
          aria-describedby={error ? "roleform-error" : undefined}
          value={name}
          onChange={(e) => {
            setError("");
            setName(e.target.value);
            setDirty(true);
          }}
        />
      </label>
      <label htmlFor="roleform-2">
        Responsibilities <span aria-hidden="true">*</span>
        <textarea
          id="roleform-2"
          aria-label="Responsibilities"
          rows={5}
          required
          aria-invalid={!!error && !responsibilities.trim()}
          aria-describedby={error ? "roleform-error" : undefined}
          value={responsibilities}
          onChange={(e) => {
            setError("");
            setResponsibilities(e.target.value);
            setDirty(true);
          }}
        />
      </label>
      <p className="field-note">
        A role defines responsibility. It does not launch or control an agent.
      </p>
      {error && (
        <p id="roleform-error" role="alert" className="form-error">
          {error}
        </p>
      )}
      <SaveFailureControl />
      <div className="form-footer">
        <span />
        <button className="primary" disabled={saving}>{mode === "mock" ? "Save role" : "Save role"}</button>
      </div>
    </form>
  );
}
