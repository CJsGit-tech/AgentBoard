import { SaveFailureControl } from "../../components/SaveFailureControl";
import { useState } from "react";
import { Project } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export function ProjectForm({
  project,
  onSaved,
}: {
  project?: Project;
  onSaved: (id: string) => void;
}) {
  const { name = "", purpose = "" } = project || {};
  const [values, setValues] = useState({ name, purpose });
  const [error, setError] = useState("");
  const { saveProject, setDirty, mode } = useWorkspace();
  const [saving, setSaving] = useState(false);
  return (
    <form
      noValidate
      aria-label="project form"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!values.name.trim()) {
          setError("Enter a project name.");
          e.currentTarget.querySelector<HTMLInputElement>("input")?.focus();
          return;
        }
        setSaving(true);
        try { onSaved(await saveProject({ name: values.name.trim(), purpose: values.purpose }, project)); }
        catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save project. Your draft is retained."); }
        finally { setSaving(false); }
      }}
    >
      <label htmlFor="projectform-1">
        Project name <span aria-hidden="true">*</span>
        <input
          id="projectform-1"

          required
          aria-invalid={!!error && !values.name.trim()}
          aria-describedby={error && !values.name.trim() ? "projectform-error" : undefined}
          value={values.name}
          onChange={(e) => {
            setError("");
            setValues({ ...values, name: e.target.value });
            setDirty(true);
          }}
        />
      </label>
      <label htmlFor="projectform-2">
        Purpose
        <textarea
          id="projectform-2"
          aria-label="Purpose"
          rows={4}
          value={values.purpose}
          onChange={(e) => {
            setError("");
            setValues({ ...values, purpose: e.target.value });
            setDirty(true);
          }}
        />
      </label>
      {error && (
        <p className="form-error" id="projectform-error" role="alert">
          {error}
        </p>
      )}
      <SaveFailureControl />
      <div className="form-footer">
        <small>{mode === "mock" ? "Saved only in this preview" : "Saved to the connected workspace"}</small>
        <button className="primary" disabled={saving}>
          {project ? "Save project" : "Create project"}
        </button>
      </div>
    </form>
  );
}
