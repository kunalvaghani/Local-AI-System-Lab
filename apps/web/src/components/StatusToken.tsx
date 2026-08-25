type StatusTone =
  | "healthy"
  | "active"
  | "queued"
  | "warning"
  | "critical"
  | "blocked"
  | "partial"
  | "deferred"
  | "unavailable"
  | "stale"
  | "unknown";

type StatusTokenProps = {
  children: React.ReactNode;
  tone: StatusTone;
};

const glyphByTone: Record<StatusTone, string> = {
  healthy: "✓",
  active: "▶",
  queued: "Ⅱ",
  warning: "!",
  critical: "×",
  blocked: "■",
  partial: "◐",
  deferred: "→",
  unavailable: "—",
  stale: "↺",
  unknown: "?",
};

function StatusToken({ children, tone }: StatusTokenProps) {
  return (
    <span className="status-token" data-tone={tone}>
      <span aria-hidden="true">{glyphByTone[tone]}</span>
      {children}
    </span>
  );
}

export { StatusToken };
export type { StatusTone };
