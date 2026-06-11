import { cn } from "@/lib/cn";

export function ErrorState({
  title = "Backend unavailable",
  description,
  hint,
  action,
  className,
}: {
  title?: string;
  description?: string;
  hint?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-danger/30 bg-danger/[0.04] p-6",
        className,
      )}
    >
      <div className="flex items-start gap-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-danger/40 bg-danger/10 font-mono text-[11px] uppercase tracking-wider text-danger">
          err
        </div>
        <div className="flex-1 space-y-2">
          <h3 className="text-sm font-semibold text-fg">{title}</h3>
          {description && <p className="font-mono text-xs text-fg-muted">{description}</p>}
          {hint && <p className="text-xs text-fg-subtle">{hint}</p>}
          {action && <div className="pt-1">{action}</div>}
        </div>
      </div>
    </div>
  );
}
