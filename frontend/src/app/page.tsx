import Link from "next/link";
import { api } from "@/lib/api";
import { ALGO_KEYS, ALGO_NAMES, type Domain } from "@/lib/types";
import { Card } from "@/components/Card";

const DOMAIN_CARDS: {
  slug: Domain;
  name: string;
  source: string;
  blurb: string;
  scale: string;
}[] = [
  {
    slug: "movies",
    name: "Movies",
    source: "MovieLens-100K",
    blurb: "943 users, 1,682 films, 100K ratings from the classic GroupLens benchmark.",
    scale: "100,000",
  },
  {
    slug: "news",
    name: "News",
    source: "Microsoft MIND-small",
    blurb: "Filtered to the most active readers across hundreds of news outlets.",
    scale: "MIND",
  },
];

export default async function HomePage() {
  const { data: service } = await api.getService();

  return (
    <div className="flex flex-col gap-16 py-10 lg:gap-20 lg:py-16">
      <section className="animate-rise">
        <div className="flex flex-col gap-6">
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-border bg-bg-elevated px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-fg-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Research Harness · v0.1
          </span>
          <h1 className="max-w-3xl text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-fg sm:text-5xl lg:text-6xl">
            Six recommendation algorithms.<br />
            <span className="text-fg-muted">Two datasets. Side by side.</span>
          </h1>
          <p className="max-w-2xl text-balance text-base leading-relaxed text-fg-muted">
            RecSys Lab is a comparison harness for popularity, content, collaborative,
            matrix-factorization, hybrid, and neural recommenders — trained on MovieLens-100K and
            Microsoft MIND-small. Pick a user, pick algorithms, see how their top-K differ.
          </p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2 lg:gap-6">
        {DOMAIN_CARDS.map((d, i) => {
          const loaded = service?.loaded?.[d.slug];
          return (
            <Link
              key={d.slug}
              href={`/${d.slug}`}
              className="group block animate-rise"
              style={{ animationDelay: `${80 * (i + 1)}ms` }}
            >
              <Card
                interactive
                className="relative h-full overflow-hidden p-7"
              >
                <div className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-accent/[0.06] blur-3xl transition-all duration-500 group-hover:scale-150 group-hover:bg-accent/[0.1]" />
                <div className="relative flex h-full flex-col gap-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex flex-col gap-1">
                      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-fg-subtle">
                        {d.source}
                      </span>
                      <h2 className="text-2xl font-semibold tracking-tight text-fg">
                        {d.name}
                      </h2>
                    </div>
                    <StatusBadge state={loaded ? "loaded" : service ? "unloaded" : "unknown"} />
                  </div>

                  <p className="text-sm leading-relaxed text-fg-muted">{d.blurb}</p>

                  <div className="mt-auto flex items-end justify-between gap-4 border-t border-border pt-5">
                    <div className="flex items-baseline gap-2">
                      <span className="tabular font-mono text-2xl font-semibold text-fg">
                        {d.scale}
                      </span>
                      <span className="text-xs text-fg-subtle">interactions</span>
                    </div>
                    <span className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-accent-fg transition-transform duration-300 group-hover:translate-x-1">
                      Open →
                    </span>
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}
      </section>

      <section className="animate-rise" style={{ animationDelay: "240ms" }}>
        <div className="mb-4 flex items-baseline justify-between gap-4">
          <h3 className="text-sm font-semibold tracking-tight text-fg">
            Algorithms
          </h3>
          <span className="font-mono text-[11px] uppercase tracking-wider text-fg-subtle">
            6 implementations · same interface
          </span>
        </div>
        <div className="grid gap-px overflow-hidden rounded-xl border border-border bg-border md:grid-cols-2 lg:grid-cols-3">
          {ALGO_KEYS.map((key) => (
            <div
              key={key}
              className="flex items-center justify-between gap-3 bg-surface px-4 py-3 transition-colors hover:bg-bg-elevated"
            >
              <div className="flex flex-col">
                <span className="text-sm font-medium text-fg">{ALGO_NAMES[key]}</span>
                <span className="font-mono text-[11px] text-fg-subtle">{key}</span>
              </div>
              <AlgoFamily algo={key} />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function StatusBadge({ state }: { state: "loaded" | "unloaded" | "unknown" }) {
  const config = {
    loaded: { dot: "bg-success", text: "loaded", color: "text-success" },
    unloaded: { dot: "bg-warning", text: "not loaded", color: "text-warning" },
    unknown: { dot: "bg-fg-subtle", text: "offline", color: "text-fg-subtle" },
  }[state];
  return (
    <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border bg-bg-elevated px-2.5 py-1">
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      <span className={`font-mono text-[10px] uppercase tracking-wider ${config.color}`}>
        {config.text}
      </span>
    </span>
  );
}

function AlgoFamily({ algo }: { algo: string }) {
  const family =
    algo === "popularity"
      ? "baseline"
      : algo === "content_based"
      ? "content"
      : algo === "item_knn"
      ? "memory"
      : algo === "als"
      ? "matrix-fact"
      : algo === "hybrid"
      ? "blend"
      : "neural";
  return (
    <span className="font-mono text-[10px] uppercase tracking-wider text-fg-subtle">
      {family}
    </span>
  );
}
