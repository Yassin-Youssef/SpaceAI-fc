/** Labelled range input with its current value shown beside the label. */
export function RangeField({ label, display, min, max, step = 1, value, onChange }: {
  label: string;
  display?: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium text-text-secondary">{label}</span>
        <span className="tabular text-sm text-text-primary">{display ?? value}</span>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full" />
    </label>
  );
}
