interface ToggleProps {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}

export default function Toggle({ label, checked, onChange }: ToggleProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={() => onChange(!checked)}
        className="rounded border-border text-accent focus:ring-accent"
      />
      <span className="text-sm text-text-secondary">{label}</span>
    </label>
  );
}
