import { Radio, WifiOff } from "lucide-react";
export function LiveActivityControls({
  connected,
  buffered,
  gap,
  onToggle,
  onFlush,
  onSimulate,
  onCleanup,
  onReplay,
}: {
  connected: boolean;
  buffered: number;
  gap: boolean;
  onToggle: () => void;
  onFlush: () => void;
  onSimulate: () => void;
  onCleanup: () => void;
  onReplay: () => void;
}) {
  return (
    <div className="live-controls">
      <div className={"live-state " + (!connected ? "stale" : "")}>
        {connected ? <Radio size={14} /> : <WifiOff size={14} />}
        <strong>
          {connected ? "Live preview" : "Disconnected · showing retained data"}
        </strong>
        <small>Agent reporting is not exhaustive</small>
      </div>
      <div className="live-actions">
        <button onClick={onToggle}>
          {connected ? "Simulate disconnect" : "Reconnect"}
        </button>
        <button onClick={onSimulate}>Simulate incoming event</button>
        <button onClick={onReplay}>Replay last event</button>
        <button onClick={onCleanup}>Run retention cleanup</button>
      </div>
      {buffered > 0 && (
        <button className="new-events" onClick={onFlush}>
          {buffered} new event{buffered !== 1 ? "s" : ""} · Show
        </button>
      )}
      {gap && (
        <p className="notice" role="status">
          A retained cursor expired during disconnection. The unavailable
          interval is marked; retained events have been resynchronized.
        </p>
      )}
    </div>
  );
}
