import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-24 text-center">
      <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-fg-subtle">
        404
      </span>
      <h1 className="text-3xl font-semibold tracking-tight text-fg">
        Page not found
      </h1>
      <p className="max-w-md text-sm text-fg-muted">
        The route you requested does not exist. Valid domains are
        {" "}<span className="font-mono text-fg">/movies</span>
        {" and "}
        <span className="font-mono text-fg">/news</span>.
      </p>
      <Link
        href="/"
        className="rounded-md border border-border bg-bg-elevated px-4 py-2 text-sm font-medium text-fg transition-colors hover:border-border-strong"
      >
        Back to lab
      </Link>
    </div>
  );
}
