import { cn } from "@/lib/cn";

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-bg-sunken/40 px-6 py-12 text-center",
        className,
      )}
    >
      <div className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-bg-elevated font-mono text-[11px] uppercase tracking-wider text-fg-subtle">
        nil
      </div>
      <h3 className="text-sm font-semibold text-fg">{title}</h3>
      {description && <p className="max-w-md text-xs text-fg-muted">{description}</p>}
      {action}
    </div>
  );
}
