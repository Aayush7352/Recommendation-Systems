import { cn } from "@/lib/cn";

export function StatTile({
  label,
  value,
  hint,
  className,
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 rounded-xl border border-border bg-surface p-4 shadow-sm",
        className,
      )}
    >
      <span className="text-[10px] font-medium uppercase tracking-[0.1em] text-fg-subtle">
        {label}
      </span>
      <span className="tabular font-mono text-2xl font-semibold leading-none text-fg">
        {value}
      </span>
      {hint && (
        <span className="text-[11px] text-fg-muted">{hint}</span>
      )}
    </div>
  );
}
