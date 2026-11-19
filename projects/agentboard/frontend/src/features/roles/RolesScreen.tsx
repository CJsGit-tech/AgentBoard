import { useState } from "react";
import { Plus } from "lucide-react";
import { Role } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { Modal } from "../../components/Modal";
import { RoleForm } from "./RoleForm";
import { RoleCard } from "./RoleCard";
export function RolesScreen() {
  const { db, projectId, dirty, setDirty } = useWorkspace();
  const [editing, setEditing] = useState<Role | null | undefined>();
  const roles = db.roles.filter((r) => r.projectId === projectId);
  return (
    <>
      <PageHeader
        title="Roles"
        description="Define responsibilities. Keep ownership clear."
        actions={
          <button
            className="primary"
            onClick={() => {
              setEditing(null);
            }}
          >
            <Plus size={16} />
            New role
          </button>
        }
      />
      <div className="context-note">
        Roles are definitions, not running agents. Codex and Claude work
        independently.
      </div>
      <StatePanel
        empty={!roles.length}
        title="No roles defined"
        action={
          <button
            onClick={() => {
              setEditing(null);
            }}
          >
            Create role
          </button>
        }
      >
        <div className="role-grid">
          {roles.map((r) => (
            <RoleCard
              key={r.id}
              role={r}
              onEdit={() => {
                setEditing(r);
              }}
            />
          ))}
        </div>
      </StatePanel>
      <Modal
        open={editing !== undefined}
        title={editing ? "Edit role" : "Create role"}
        onClose={() => {
          if (dirty && !confirm("Discard unsaved role changes?")) return;
          setDirty(false);
          setEditing(undefined);
        }}
      >
        {editing !== undefined && (
          <RoleForm
            role={editing || undefined}
            onSaved={() => setEditing(undefined)}
          />
        )}
      </Modal>
    </>
  );
}
