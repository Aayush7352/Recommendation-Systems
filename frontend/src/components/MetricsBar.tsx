"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ALGO_NAMES, ALGO_SHORT, ALGO_TINT, type AlgoKey, type MetricKey, type MetricReport } from "@/lib/types";

interface Props {
  reports: MetricReport[];
  metric: MetricKey;
  formatY?: (n: number) => string;
}

interface TooltipPayload {
  payload?: { algo?: AlgoKey; full?: string; value?: number };
}

export function MetricsBar({ reports, metric, formatY }: Props) {
  const data = reports.map((r) => ({
    algo: ALGO_SHORT[r.algo] ?? r.algo,
    full: ALGO_NAMES[r.algo] ?? r.algo,
    key: r.algo,
    value: r[metric],
  }));

  const formatter = formatY ?? ((n: number) => n.toFixed(3));

  return (
    <div className="h-72 w-full animate-fade-in">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" vertical={false} />
          <XAxis
            dataKey="algo"
            stroke="var(--fg-subtle)"
            tick={{ fontSize: 11, fontFamily: "var(--font-jetbrains-mono)" }}
            axisLine={{ stroke: "var(--border)" }}
            tickLine={false}
          />
          <YAxis
            stroke="var(--fg-subtle)"
            tick={{ fontSize: 11, fontFamily: "var(--font-jetbrains-mono)" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatter}
            width={60}
          />
          <Tooltip
            cursor={{ fill: "var(--accent-soft)" }}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const p = (payload[0] as TooltipPayload).payload;
              if (!p) return null;
              return (
                <div className="rounded-md border border-border bg-surface px-3 py-2 shadow-md">
                  <div className="text-xs font-medium text-fg">{p.full}</div>
                  <div className="mt-1 font-mono text-xs tabular text-accent-fg">
                    {typeof p.value === "number" ? formatter(p.value) : ""}
                  </div>
                </div>
              );
            }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={650}>
            {data.map((d) => (
              <Cell key={d.key} fill={ALGO_TINT[d.key as AlgoKey] ?? "var(--accent)"} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
