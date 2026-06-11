import type { Domain, ScoredItem } from "@/lib/types";
import { formatScore } from "@/lib/cn";
import { cn } from "@/lib/cn";

interface Props {
  item: ScoredItem;
  rank: number;
  domain: Domain;
  highlight?: "shared" | "unique" | null;
}

export function RecommendationCard({ item, rank, domain, highlight }: Props) {
  const borderClass =
    highlight === "shared"
      ? "border-accent/40 bg-accent-soft/40"
      : highlight === "unique"
      ? "border-warning/40 bg-warning/[0.04]"
      : "border-border hover:border-border-strong";

  return (
    <div
      className={cn(
        "group flex gap-3 rounded-lg border bg-surface p-3 transition-all duration-200",
        borderClass,
      )}
    >
      <div className="flex shrink-0 flex-col items-center gap-1.5 pt-0.5">
        <span className="font-mono text-[10px] uppercase tracking-wider text-fg-subtle">
          {String(rank).padStart(2, "0")}
        </span>
        <span className="tabular rounded-md border border-border bg-bg-elevated px-1.5 py-0.5 font-mono text-[10px] text-fg-muted">
          {formatScore(item.score, 3)}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        {domain === "movies" ? (
          <MovieBody item={item} />
        ) : (
          <NewsBody item={item} />
        )}
      </div>
    </div>
  );
}

function MovieBody({ item }: { item: ScoredItem }) {
  const meta = item.metadata ?? {};
  const genres = Array.isArray(meta.genres) ? (meta.genres as string[]) : [];
  const visibleGenres = genres.slice(0, 3);
  const extraGenres = genres.length - visibleGenres.length;
  const year =
    meta.release_year ??
    (typeof meta.release_date === "string"
      ? meta.release_date.match(/\d{4}/)?.[0]
      : null);

  const cleanTitle = String(item.title ?? "").replace(/\s*\(\d{4}\)\s*$/, "");

  return (
    <>
      <h4 className="line-clamp-2 text-sm font-medium leading-snug text-fg">
        {cleanTitle}
      </h4>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {year && (
          <span className="font-mono text-[10px] tabular text-fg-subtle">{year}</span>
        )}
        {visibleGenres.map((g) => (
          <span
            key={g}
            className="rounded-full border border-border bg-bg-elevated px-2 py-0.5 text-[10px] text-fg-muted"
          >
            {g}
          </span>
        ))}
        {extraGenres > 0 && (
          <span className="text-[10px] text-fg-subtle">+{extraGenres}</span>
        )}
      </div>
    </>
  );
}

function NewsBody({ item }: { item: ScoredItem }) {
  const meta = item.metadata ?? {};
  const category = typeof meta.category === "string" ? meta.category : undefined;
  const subcategory = typeof meta.subcategory === "string" ? meta.subcategory : undefined;
  const abstract = typeof meta.abstract === "string" ? meta.abstract : undefined;

  return (
    <>
      <h4 className="line-clamp-2 text-sm font-medium leading-snug text-fg">
        {item.title}
      </h4>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {category && (
          <span className="rounded-full border border-accent/30 bg-accent-soft px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-accent-fg">
            {category}
          </span>
        )}
        {subcategory && (
          <span className="font-mono text-[10px] text-fg-subtle">{subcategory}</span>
        )}
      </div>
      {abstract && (
        <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-fg-muted">
          {abstract}
        </p>
      )}
    </>
  );
}
