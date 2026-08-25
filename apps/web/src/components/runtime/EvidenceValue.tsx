type EvidenceValueProps = {
  label: string;
  value: React.ReactNode;
  detail: React.ReactNode;
  meter?: number | null;
};

function EvidenceValue({ label, value, detail, meter }: EvidenceValueProps) {
  const boundedMeter = meter == null ? null : Math.max(0, Math.min(100, meter));

  return (
    <article className="evidence-value">
      <p>{label}</p>
      <strong>{value}</strong>
      <small>{detail}</small>
      {boundedMeter == null ? null : (
        <span
          aria-label={`${label}: ${boundedMeter.toFixed(0)} percent`}
          aria-valuemax={100}
          aria-valuemin={0}
          aria-valuenow={Math.round(boundedMeter)}
          className="evidence-meter"
          role="meter"
        >
          <i style={{ "--meter-value": `${boundedMeter}%` } as React.CSSProperties} />
        </span>
      )}
    </article>
  );
}

export { EvidenceValue };
