"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Domain } from "@/lib/types";
import { cn } from "@/lib/cn";

const SECTIONS = [
  { slug: "", label: "Overview" },
  { slug: "users", label: "Browse Users" },
  { slug: "compare", label: "Compare" },
  { slug: "evaluation", label: "Evaluation" },
];

export function DomainTabs({ domain }: { domain: Domain }) {
  const pathname = usePathname() ?? "";
  const base = `/${domain}`;

  return (
    <nav className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-bg-elevated p-1">
      {SECTIONS.map((s) => {
        const href = s.slug ? `${base}/${s.slug}` : base;
        const isActive = s.slug
          ? pathname.startsWith(href)
          : pathname === base;
        return (
          <Link
            key={s.slug || "overview"}
            href={href}
            className={cn(
              "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
              isActive
                ? "bg-surface text-fg shadow-sm"
                : "text-fg-muted hover:text-fg",
            )}
          >
            {s.label}
          </Link>
        );
      })}
    </nav>
  );
}
