import { OperationNotice } from "./OperationNotice";
import { useWorkspace } from "../app/WorkspaceContext";
import { ReactNode, useEffect, useRef } from "react";
import { X } from "lucide-react";
export function Modal({
  open,
  title,
  children,
  onClose,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const { notice, clearNotice } = useWorkspace();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby="modal-title"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <header className="modal-header">
        <h2 id="modal-title">{title}</h2>
        <button
          type="button"
          className="iconbutton"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={18} />
        </button>
      </header>
      {children}
      {open && (
        <OperationNotice message={notice} onDismiss={clearNotice} inline />
      )}
    </dialog>
  );
}
