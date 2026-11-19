import { Status } from "../api/types";
export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={"status " + status.toLowerCase().replaceAll(" ", "-")}>
      <span aria-hidden="true">
        {{ Planned: "○", "In progress": "◔", Blocked: "△", Done: "✓" }[status]}
      </span>
      {status}
    </span>
  );
}
