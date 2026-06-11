import type { Domain, Item } from "@/lib/types";
import { cn } from "@/lib/cn";

interface Props {
  items: Item[];
  domain: Domain;
  compact?: boolean;
  className?: string;
}

export function UserHistoryList({ items, domain, compact = false, className }: Props) {
  if (items.length === 0) {
    return (
      <p className="text-xs text-fg-subtle">No interactions recorded for this user.</p>
    );
  }

  return (
    <ul
      className={cn(
        "divide-y divide-border overflow-hidden rounded-lg border border-border bg-surface",
        className,
      )}
    >
      {items.map((item, i) => (
        <li
          key={`${item.item_id}-${i}`}
          className={cn(
            "flex items-center gap-3 px-3",
            compact ? "py-1.5" : "py-2.5",
          )}
        >
          <span className="font-mono text-[10px] tabular text-fg-subtle">
            {String(i + 1).padStart(2, "0")}
          </span>
          <span className="font-mono text-[10px] tabular text-fg-subtle">
            #{String(item.item_id)}
          </span>
          <span className="flex-1 truncate text-xs text-fg">
            {item.title || "Untitled"}
          </span>
          {domain === "news" && typeof item.metadata?.category === "string" && (
            <span className="hidden shrink-0 rounded-full border border-border bg-bg-elevated px-2 py-0.5 text-[10px] text-fg-muted sm:inline">
              {item.metadata.category as string}
            </span>
          )}
          {domain === "movies" && Array.isArray(item.metadata?.genres) && (
            <span className="hidden shrink-0 truncate font-mono text-[10px] text-fg-subtle md:inline">
              {(item.metadata?.genres as string[]).slice(0, 2).join(" · ")}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
