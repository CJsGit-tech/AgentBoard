export function OperationNotice({
  message,
  onDismiss,
  inline = false,
}: {
  message: string;
  onDismiss: () => void;
  inline?: boolean;
}) {
  if (!message) return null;
  return (
    <div className={inline ? "inline-operation-notice" : "toast"} role="status">
      {message}
      <button
        type="button"
        aria-label="Dismiss notification"
        onClick={onDismiss}
      >
        ×
      </button>
    </div>
  );
}
