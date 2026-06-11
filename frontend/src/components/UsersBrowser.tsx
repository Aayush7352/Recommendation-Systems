"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Domain, Item, UserSummary } from "@/lib/types";
import { cn, formatNumber } from "@/lib/cn";
import { Card, CardBody, CardHeader, CardTitle } from "./Card";
import { Button } from "./Button";
import { Skeleton } from "./Skeleton";
import { ErrorState } from "./ErrorState";
import { EmptyState } from "./EmptyState";
import { UserHistoryList } from "./UserHistoryList";

export function UsersBrowser({ domain }: { domain: Domain }) {
  const [users, setUsers] = useState<UserSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<UserSummary | null>(null);
  const [history, setHistory] = useState<Item[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    let alive = true;
    setUsers(null);
    setError(null);
    api.getUsers(domain, limit).then(({ data, error }) => {
      if (!alive) return;
      if (error || !data) {
        setError(error ?? "Unknown error");
        return;
      }
      setUsers(data);
      setSelected((cur) => cur ?? data[0] ?? null);
    });
    return () => {
      alive = false;
    };
  }, [domain, limit]);

  useEffect(() => {
    if (!selected) {
      setHistory(null);
      return;
    }
    let alive = true;
    setHistoryLoading(true);
    setHistoryError(null);
    api.getUserHistory(domain, selected.user_id, 50).then(({ data, error }) => {
      if (!alive) return;
      setHistoryLoading(false);
      if (error || !data) {
        setHistoryError(error ?? "Failed to load history");
        setHistory(null);
        return;
      }
      setHistory(data);
    });
    return () => {
      alive = false;
    };
  }, [selected, domain]);

  const filtered = useMemo(() => {
    if (!users) return null;
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter((u) => String(u.user_id).toLowerCase().includes(q));
  }, [users, query]);

  if (error) {
    return (
      <ErrorState
        title="Could not load users"
        description={error}
        hint="The backend must be running and this domain must have an index of users."
      />
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(320px,400px)_1fr]">
      <Card className="flex h-fit flex-col">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>Top users</CardTitle>
            <span className="font-mono text-[10px] uppercase tracking-wider text-fg-subtle">
              by interactions
            </span>
          </div>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search user_id (e.g. ${domain === "movies" ? "42" : "U13740"})`}
            className="mt-2 h-9 w-full rounded-md border border-border bg-bg px-3 font-mono text-xs text-fg placeholder:text-fg-subtle focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
          />
        </CardHeader>
        <div className="max-h-[60vh] overflow-y-auto">
          {!filtered ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-4">
              <EmptyState title="No users match your search" />
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {filtered.map((u) => {
                const isActive = selected?.user_id === u.user_id;
                return (
                  <li key={String(u.user_id)}>
                    <button
                      type="button"
                      onClick={() => setSelected(u)}
                      className={cn(
                        "flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left transition-colors",
                        isActive
                          ? "bg-accent-soft text-accent-fg"
                          : "hover:bg-bg-elevated",
                      )}
                    >
                      <div className="flex flex-col">
                        <span className="font-mono text-sm tabular text-fg">
                          {String(u.user_id)}
                        </span>
                        <span className="text-[11px] text-fg-subtle">
                          {formatNumber(u.n_interactions)} interactions
                        </span>
                      </div>
                      <Sparkbar value={u.n_interactions} max={users?.[0]?.n_interactions ?? 1} active={isActive} />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
        <div className="border-t border-border bg-bg-sunken/40 p-3">
          <div className="flex items-center justify-between gap-2 text-[11px]">
            <span className="text-fg-subtle">Show</span>
            <div className="flex gap-1">
              {[25, 50, 100, 250].map((n) => (
                <button
                  key={n}
                  onClick={() => setLimit(n)}
                  className={cn(
                    "rounded px-2 py-0.5 font-mono text-[10px] transition-colors",
                    limit === n
                      ? "bg-accent text-white"
                      : "text-fg-muted hover:text-fg",
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <Card className="h-fit">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-col">
              <CardTitle>
                {selected ? (
                  <span className="font-mono">user {String(selected.user_id)}</span>
                ) : (
                  "Select a user"
                )}
              </CardTitle>
              {selected && (
                <span className="text-[11px] text-fg-muted">
                  {formatNumber(selected.n_interactions)} interactions in training set
                </span>
              )}
            </div>
            {selected && (
              <Link
                href={`/${domain}/compare?user_id=${encodeURIComponent(String(selected.user_id))}`}
              >
                <Button variant="primary" size="sm">
                  Compare algorithms →
                </Button>
              </Link>
            )}
          </div>
        </CardHeader>
        <CardBody>
          {historyError ? (
            <ErrorState title="History unavailable" description={historyError} />
          ) : historyLoading || !history ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-full" />
              ))}
            </div>
          ) : history.length === 0 ? (
            <EmptyState
              title="No history"
              description="This user has no interactions in the training set."
            />
          ) : (
            <UserHistoryList items={history} domain={domain} />
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function Sparkbar({ value, max, active }: { value: number; max: number; active: boolean }) {
  const pct = max > 0 ? Math.min(1, value / max) : 0;
  return (
    <div className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-bg-sunken sm:block">
      <div
        className={cn("h-full transition-all", active ? "bg-accent" : "bg-fg-subtle/40")}
        style={{ width: `${pct * 100}%` }}
      />
    </div>
  );
}
