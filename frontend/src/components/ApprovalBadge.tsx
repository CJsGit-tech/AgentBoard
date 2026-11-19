import { ShieldAlert } from "lucide-react";
export function ApprovalBadge({ count = 1 }: { count?: number }) {
  if (count <= 0) return <span className="muted small">No pending requests</span>;
  return (
    <span className="approval">
      <ShieldAlert size={12} />
      Needs approval{count > 1 ? " · " + count : ""}
    </span>
  );
}
