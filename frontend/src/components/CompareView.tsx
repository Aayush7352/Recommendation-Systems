"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import {
  ALGO_KEYS,
  ALGO_NAMES,
  ALGO_TINT,
  type AlgoKey,
  type CompareResponse,
  type Domain,
  type Item,
  type ScoredItem,
  type UserSummary,
} from "@/lib/types";
import { cn } from "@/lib/cn";
import { Card, CardBody, CardHeader, CardTitle } from "./Card";
import { Button } from "./Button";
import { Skeleton, SkeletonStack } from "./Skeleton";
import { ErrorState } from "./ErrorState";
import { EmptyState } from "./EmptyState";
import { RecommendationCard } from "./RecommendationCard";
import { UserHistoryList } from "./UserHistoryList";

const K_OPTIONS = [5, 10, 20];
const DEFAULT_ALGOS: AlgoKey[] = ["popularity", "content_based", "item_knn", "als"];

interface Props {
  domain: Domain;
  initialUserId: string | null;
}

export function CompareView({ domain, initialUserId }: Props) {
  const router = useRouter();
  const [users, setUsers] = useState<UserSummary[] | null>(null);
  const [userId, setUserId] = useState<string | null>(initialUserId);
  const [k, setK] = useState<number>(10);
  const [selectedAlgos, setSelectedAlgos] = useState<AlgoKey[]>(DEFAULT_ALGOS);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [history, setHistory] = useState<Item[] | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    api.getUsers(domain, 100).then(({ data }) => {
      if (!alive || !data) return;
      setUsers(data);
      if (!userId && data[0]) {
        setUserId(String(data[0].user_id));
      }
    });
    return () => {
      alive = false;
    };
  }, [domain, userId]);

  useEffect(() => {
    if (!userId) return;
    let alive = true;
    api.getUserHistory(domain, userId, 30).then(({ data }) => {
      if (!alive) return;
      setHistory(data ?? []);
    });
    return () => {
      alive = false;
    };
  }, [domain, userId]);

  useEffect(() => {
    if (!userId || selectedAlgos.length === 0) {
      setCompare(null);
      return;
    }
    let alive = true;
    setCompareLoading(true);
    setCompareError(null);
    api.compare(domain, userId, selectedAlgos, k).then(({ data, error }) => {
      if (!alive) return;
      setCompareLoading(false);
      if (error || !data) {
        setCompare(null);
        setCompareError(error ?? "Could not load recommendations");
        return;
      }
      setCompare(data);
    });
    return () => {
      alive = false;
    };
  }, [domain, userId, selectedAlgos, k]);

  const itemFrequency = useMemo(() => {
    const counts = new Map<string, number>();
    if (!compare) return counts;
    for (const algo of Object.keys(compare.results)) {
      for (const item of compare.results[algo]) {
        const key = String(item.item_id);
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
    }
    return counts;
  }, [compare]);

  const setUserAndUrl = (newId: string) => {
    setUserId(newId);
    const params = new URLSearchParams();
    params.set("user_id", newId);
    router.replace(`/${domain}/compare?${params.toString()}`, { scroll: false });
  };

  const toggleAlgo = (algo: AlgoKey) => {
    setSelectedAlgos((cur) => {
      if (cur.includes(algo)) {
        return cur.filter((a) => a !== algo);
      }
      return [...cur, algo];
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardBody className="flex flex-wrap items-end gap-x-6 gap-y-4">
          <Field label="User">
            <select
              value={userId ?? ""}
              onChange={(e) => setUserAndUrl(e.target.value)}
              className="h-9 min-w-[180px] rounded-md border border-border bg-bg px-2 font-mono text-xs tabular text-fg focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              {!users ? (
                <option>Loading…</option>
              ) : (
                users.map((u) => (
                  <option key={String(u.user_id)} value={String(u.user_id)}>
                    {String(u.user_id)} · {u.n_interactions} ints
                  </option>
                ))
              )}
            </select>
          </Field>

          <Field label="K">
            <div className="flex gap-1 rounded-md border border-border bg-bg p-1">
              {K_OPTIONS.map((n) => (
                <button
                  key={n}
                  onClick={() => setK(n)}
                  className={cn(
                    "h-7 w-10 rounded font-mono text-xs tabular transition-colors",
                    k === n ? "bg-accent text-white" : "text-fg-muted hover:text-fg",
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Algorithms" className="flex-1">
            <div className="flex flex-wrap gap-1.5">
              {ALGO_KEYS.map((a) => {
                const active = selectedAlgos.includes(a);
                return (
                  <button
                    key={a}
                    onClick={() => toggleAlgo(a)}
                    className={cn(
                      "group flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs transition-all",
                      active
                        ? "border-border-strong bg-surface text-fg shadow-sm"
                        : "border-border bg-bg-elevated text-fg-muted hover:text-fg",
                    )}
                  >
                    <span
                      className="h-2 w-2 rounded-full transition-opacity"
                      style={{
                        backgroundColor: ALGO_TINT[a],
                        opacity: active ? 1 : 0.35,
                      }}
                    />
                    {ALGO_NAMES[a]}
                  </button>
                );
              })}
            </div>
          </Field>

          {userId && (
            <Link href={`/${domain}/users`}>
              <Button variant="ghost" size="sm">Change user</Button>
            </Link>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <button
            onClick={() => setHistoryOpen((o) => !o)}
            className="flex w-full items-center justify-between gap-3 text-left"
          >
            <div>
              <CardTitle>User history</CardTitle>
              <p className="text-xs text-fg-muted">
                {history
                  ? `${history.length} most recent interactions`
                  : "Loading…"}
              </p>
            </div>
            <span className="font-mono text-[11px] uppercase tracking-wider text-fg-subtle">
              {historyOpen ? "hide ▴" : "show ▾"}
            </span>
          </button>
        </CardHeader>
        {historyOpen && (
          <CardBody>
            {!history ? (
              <SkeletonStack rows={5} />
            ) : history.length === 0 ? (
              <EmptyState title="No history" description="This user has no interactions in the training set." />
            ) : (
              <UserHistoryList items={history} domain={domain} compact />
            )}
          </CardBody>
        )}
      </Card>

      {compareError ? (
        <ErrorState title="Recommendations failed" description={compareError} />
      ) : selectedAlgos.length === 0 ? (
        <EmptyState
          title="No algorithms selected"
          description="Toggle one or more algorithms above to compare their top-K reclists."
        />
      ) : (
        <ResultsGrid
          compare={compare}
          selectedAlgos={selectedAlgos}
          k={k}
          loading={compareLoading}
          domain={domain}
          itemFrequency={itemFrequency}
        />
      )}
    </div>
  );
}

function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-fg-subtle">
        {label}
      </span>
      {children}
    </div>
  );
}

function ResultsGrid({
  compare,
  selectedAlgos,
  k,
  loading,
  domain,
  itemFrequency,
}: {
  compare: CompareResponse | null;
  selectedAlgos: AlgoKey[];
  k: number;
  loading: boolean;
  domain: Domain;
  itemFrequency: Map<string, number>;
}) {
  const gridCols =
    selectedAlgos.length === 1
      ? "grid-cols-1"
      : selectedAlgos.length === 2
      ? "grid-cols-1 lg:grid-cols-2"
      : selectedAlgos.length === 3
      ? "grid-cols-1 md:grid-cols-2 xl:grid-cols-3"
      : "grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4";

  return (
    <div className={cn("grid gap-4", gridCols)}>
      {selectedAlgos.map((algo, idx) => {
        const items = compare?.results?.[algo] as ScoredItem[] | undefined;
        return (
          <Card
            key={algo}
            className="flex flex-col animate-rise"
            style={{ animationDelay: `${idx * 60}ms` } as React.CSSProperties}
          >
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: ALGO_TINT[algo] }}
                  />
                  <CardTitle>{ALGO_NAMES[algo]}</CardTitle>
                </div>
                <span className="font-mono text-[10px] uppercase tracking-wider text-fg-subtle">
                  top {k}
                </span>
              </div>
            </CardHeader>
            <CardBody className="flex flex-col gap-2">
              {loading || !items ? (
                Array.from({ length: k }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))
              ) : items.length === 0 ? (
                <EmptyState title="No items returned" />
              ) : (
                items.map((item, i) => {
                  const freq = itemFrequency.get(String(item.item_id)) ?? 1;
                  const isShared = freq >= 2 && selectedAlgos.length >= 2;
                  const isUnique = freq === 1 && selectedAlgos.length >= 2;
                  return (
                    <RecommendationCard
                      key={`${item.item_id}-${i}`}
                      item={item}
                      rank={i + 1}
                      domain={domain}
                      highlight={isShared ? "shared" : isUnique ? "unique" : null}
                    />
                  );
                })
              )}
            </CardBody>
            {!loading && items && items.length > 0 && selectedAlgos.length >= 2 && (
              <div className="flex items-center justify-between gap-3 border-t border-border bg-bg-sunken/40 px-4 py-2 text-[11px]">
                <Legend swatch="bg-accent" label="appears in multiple" />
                <Legend swatch="bg-warning" label="unique to this algo" />
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-fg-subtle">
      <span className={cn("h-2 w-2 rounded-full opacity-70", swatch)} />
      {label}
    </span>
  );
}
