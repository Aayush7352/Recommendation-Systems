"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ServiceInfo } from "@/lib/types";
import { cn } from "@/lib/cn";

type Status = "loading" | "online" | "offline";

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("loading");
  const [info, setInfo] = useState<ServiceInfo | null>(null);

  useEffect(() => {
    let alive = true;
    const ping = async () => {
      const { data, error } = await api.getService();
      if (!alive) return;
      if (error || !data) {
        setStatus("offline");
        setInfo(null);
      } else {
        setStatus("online");
        setInfo(data);
      }
    };
    void ping();
    const id = setInterval(ping, 15_000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const dotColor =
    status === "online" ? "bg-success" : status === "offline" ? "bg-danger" : "bg-fg-subtle";

  return (
    <div className="group relative flex items-center gap-2 rounded-md border border-border bg-bg-elevated px-2.5 py-1.5 text-xs">
      <span className="relative flex h-2 w-2">
        {status === "online" && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/40" />
        )}
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", dotColor)} />
      </span>
      <span className="hidden font-mono text-[11px] uppercase tracking-wider text-fg-muted sm:inline">
        {status === "online" ? "API" : status === "offline" ? "API offline" : "…"}
      </span>
      {info && (
        <div className="pointer-events-none absolute right-0 top-full z-50 mt-2 w-72 -translate-y-1 rounded-lg border border-border bg-surface p-3 text-left opacity-0 shadow-md transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100">
          <div className="mb-2 flex items-center justify-between border-b border-border pb-2">
            <span className="text-xs font-semibold text-fg">{info.service}</span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-success">online</span>
          </div>
          <ul className="space-y-1.5 text-xs">
            {info.domains.map((d) => (
              <li key={d} className="flex items-center justify-between">
                <span className="text-fg-muted">{d}</span>
                <span
                  className={cn(
                    "font-mono text-[10px] uppercase tracking-wider",
                    info.loaded[d] ? "text-success" : "text-warning",
                  )}
                >
                  {info.loaded[d] ? "loaded" : "not loaded"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
