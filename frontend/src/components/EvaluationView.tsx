"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  ALGO_NAMES,
  METRICS,
  type AlgoKey,
  type Domain,
  type EvalResponse,
  type MetricKey,
} from "@/lib/types";
import { cn, formatNumber } from "@/lib/cn";
import { Card, CardBody, CardHeader, CardTitle } from "./Card";
import { Button } from "./Button";
import { Skeleton } from "./Skeleton";
import { ErrorState } from "./ErrorState";
import { MetricsBar } from "./MetricsBar";
import { StatTile } from "./StatTile";

const K_OPTIONS = [5, 10, 20];

export function EvaluationView({ domain }: { domain: Domain }) {
  const [k, setK] = useState(10);
  const [report, setReport] = useState<EvalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [metric, setMetric] = useState<MetricKey>("ndcg");

  const load = (refresh = false) => {
    let alive = true;
    setError(null);
    if (refresh) setRefreshing(true);
    else setLoading(true);
    api.evaluate(domain, k, refresh).then(({ data, error }) => {
      if (!alive) return;
      setLoading(false);
      setRefreshing(false);
      if (error || !data) {
        setError(error ?? "Could not load evaluation");
        setReport(null);
        return;
      }
      setReport(data);
    });
    return () => {
      alive = false;
    };
  };

  useEffect(() => {
    const cleanup = load(false);
    return cleanup;
  }, [domain, k]); // eslint-disable-line react-hooks/exhaustive-deps

  const bestPerMetric = report
    ? METRICS.map((m) => {
        const best = report.reports.reduce<{ algo: AlgoKey; value: number } | null>(
          (acc, r) => {
            const v = r[m.key];
            if (acc === null || v > acc.value) return { algo: r.algo, value: v };
            return acc;
          },
          null,
        );
        return { metric: m, best };
      })
    : [];

  const formatter = (n: number) => {
    if (metric === "novelty") return n.toFixed(2);
    if (metric === "coverage" || metric === "diversity") return n.toFixed(3);
    return n.toFixed(4);
  };

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardBody className="flex flex-wrap items-end gap-x-6 gap-y-4">
          <div className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-fg-subtle">
              K
            </span>
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
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-fg-subtle">
              Status
            </span>
            <div className="flex h-9 items-center gap-3 rounded-md border border-border bg-bg-elevated px-3 font-mono text-[11px] text-fg-muted">
              {report ? (
                <>
                  <span>{formatNumber(report.n_users)} users</span>
                  <span className="text-fg-subtle">·</span>
                  <span>{formatNumber(report.n_items)} items</span>
                  <span className="text-fg-subtle">·</span>
                  <span>{report.reports.length} algos</span>
                </>
              ) : (
                <span className="text-fg-subtle">—</span>
              )}
            </div>
          </div>

          <Button
            variant="primary"
            size="md"
            onClick={() => load(true)}
            disabled={refreshing || loading}
            className="ml-auto"
          >
            {refreshing ? "Recomputing…" : "Refresh evaluation"}
          </Button>
        </CardBody>
      </Card>

      {error ? (
        <ErrorState
          title="Evaluation unavailable"
          description={error}
          hint="The backend must be running and the domain trained. Evaluation can take a few seconds on first call."
        />
      ) : (
        <>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {loading && !report
              ? Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 w-full rounded-xl" />
                ))
              : bestPerMetric.map(({ metric: m, best }) => (
                  <StatTile
                    key={m.key}
                    label={m.label}
                    value={best ? formatter(best.value) : "—"}
                    hint={best ? `best: ${ALGO_NAMES[best.algo]}` : undefined}
                  />
                ))}
          </section>

          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <CardTitle>By algorithm</CardTitle>
                  <p className="text-xs text-fg-muted">
                    {METRICS.find((m) => m.key === metric)?.description}
                  </p>
                </div>
                <div className="flex flex-wrap gap-1 rounded-md border border-border bg-bg p-1">
                  {METRICS.map((m) => (
                    <button
                      key={m.key}
                      onClick={() => setMetric(m.key)}
                      className={cn(
                        "rounded px-2.5 py-1 text-[11px] font-medium transition-colors",
                        metric === m.key
                          ? "bg-accent text-white"
                          : "text-fg-muted hover:text-fg",
                      )}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardBody>
              {loading && !report ? (
                <Skeleton className="h-72 w-full" />
              ) : report ? (
                <MetricsBar reports={report.reports} metric={metric} formatY={formatter} />
              ) : null}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Full report</CardTitle>
              <p className="text-xs text-fg-muted">
                Per-algorithm metrics at K = {report?.k ?? k}
              </p>
            </CardHeader>
            <CardBody className="overflow-x-auto p-0">
              {loading && !report ? (
                <div className="space-y-2 p-5">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              ) : report ? (
                <ReportTable report={report} />
              ) : null}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}

function ReportTable({ report }: { report: EvalResponse }) {
  const bestValues: Record<MetricKey, number> = {
    precision: Math.max(...report.reports.map((r) => r.precision)),
    recall: Math.max(...report.reports.map((r) => r.recall)),
    ndcg: Math.max(...report.reports.map((r) => r.ndcg)),
    coverage: Math.max(...report.reports.map((r) => r.coverage)),
    diversity: Math.max(...report.reports.map((r) => r.diversity)),
    novelty: Math.max(...report.reports.map((r) => r.novelty)),
  };
  return (
    <table className="w-full text-sm">
      <thead className="border-b border-border bg-bg-sunken/50 text-left">
        <tr>
          <th className="px-4 py-2.5 text-[11px] font-medium uppercase tracking-wider text-fg-subtle">
            Algorithm
          </th>
          {METRICS.map((m) => (
            <th key={m.key} className="px-3 py-2.5 text-right text-[11px] font-medium uppercase tracking-wider text-fg-subtle">
              {m.label}
            </th>
          ))}
          <th className="px-3 py-2.5 text-right text-[11px] font-medium uppercase tracking-wider text-fg-subtle">
            N eval
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {report.reports.map((r) => (
          <tr key={r.algo} className="hover:bg-bg-elevated/60">
            <td className="px-4 py-2.5 text-sm font-medium text-fg">
              {ALGO_NAMES[r.algo]}
            </td>
            {METRICS.map((m) => {
              const v = r[m.key];
              const isBest = v === bestValues[m.key];
              return (
                <td
                  key={m.key}
                  className={cn(
                    "px-3 py-2.5 text-right font-mono text-xs tabular",
                    isBest ? "font-semibold text-accent-fg" : "text-fg-muted",
                  )}
                >
                  {v.toFixed(4)}
                </td>
              );
            })}
            <td className="px-3 py-2.5 text-right font-mono text-xs tabular text-fg-subtle">
              {formatNumber(r.n_users_evaluated)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
