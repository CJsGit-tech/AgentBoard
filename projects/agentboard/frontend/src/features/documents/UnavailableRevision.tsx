export function UnavailableRevision({ onBack }: { onBack: () => void }) {
  return (
    <section className="state-panel" role="alert">
      <h2>This revision is no longer available</h2>
      <p>
        It is outside the retention limit. Another revision has not been
        substituted.
      </p>
      <button onClick={onBack}>Return to retained versions</button>
    </section>
  );
}
