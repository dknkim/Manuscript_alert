interface CardProps {
  title: string;
  desc?: string;
  children: React.ReactNode;
  className?: string;
}

export default function Card({ title, desc, children, className }: CardProps) {
  return (
    <div
      className={`bg-surface-raised rounded-xl border border-border p-5 ${className ?? ""}`}
    >
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      {desc && <p className="text-xs text-text-muted mt-0.5 mb-3">{desc}</p>}
      {!desc && <div className="h-3" />}
      {children}
    </div>
  );
}
