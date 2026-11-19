import { ShieldAlert } from "lucide-react";
export function ApprovalBadge({ count = 1 }: { count?: number }) {
  return (
    <span className="approval">
      <ShieldAlert size={12} />
      Needs approval{count > 1 ? " · " + count : ""}
    </span>
  );
}
