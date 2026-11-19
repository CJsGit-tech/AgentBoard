import { useWorkspace } from "../app/WorkspaceContext";
export function SaveFailureControl() {
  const { failNext, setFailNext } = useWorkspace();
  return (
    <label
      htmlFor="savefailurecontrol-1"
      className="check-label save-failure-control"
    >
      <input
        id="savefailurecontrol-1"
        type="checkbox"
        checked={failNext}
        onChange={(event) => setFailNext(event.target.checked)}
      />
      Fail next save
    </label>
  );
}
