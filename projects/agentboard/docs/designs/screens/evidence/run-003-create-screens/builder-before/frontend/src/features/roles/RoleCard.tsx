import { UserRound } from "lucide-react";
import { Role } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export function RoleCard({ role, onEdit }: { role: Role; onEdit: () => void }) {
  const { db, navigate } = useWorkspace();
  const count = db.tickets.filter((t) => t.ownerId === role.id).length;
  return (
    <article className="role-card">
      <div className="role-card-top">
        <span className="avatar">
          <UserRound size={20} />
        </span>
        <button onClick={onEdit}>Edit</button>
      </div>
      <h2>{role.name}</h2>
      <p>{role.responsibilities}</p>
      <div className="role-footer">
        <button
          className="text-button"
          onClick={() => navigate("/tickets?owner=" + role.id)}
        >
          {count} assigned tickets →
        </button>
        <span>Role definition</span>
      </div>
    </article>
  );
}
