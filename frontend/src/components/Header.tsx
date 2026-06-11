"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "./ThemeProvider";
import { BackendStatus } from "./BackendStatus";
import { cn } from "@/lib/cn";

const NAV_DOMAINS = [
  { slug: "movies", label: "Movies", source: "MovieLens-100K" },
  { slug: "news", label: "News", source: "MIND-small" },
] as const;

export function Header() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();
  const activeDomain = pathname?.split("/")[1];

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 w-full max-w-[1400px] items-center justify-between gap-6 px-6 lg:px-10">
        <div className="flex items-center gap-8">
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="relative h-6 w-6">
              <div className="absolute inset-0 rounded-md bg-accent/15 transition-transform duration-300 group-hover:scale-110" />
              <div className="absolute inset-[3px] rounded-sm border border-accent/60 bg-accent/30" />
              <div className="absolute inset-[6px] rounded-[2px] bg-accent" />
            </div>
            <span className="flex items-baseline gap-1.5">
              <span className="text-[15px] font-semibold tracking-tight text-fg">RecSys</span>
              <span className="text-[15px] font-light tracking-tight text-fg-muted">Lab</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {NAV_DOMAINS.map((d) => {
              const isActive = activeDomain === d.slug;
              return (
                <Link
                  key={d.slug}
                  href={`/${d.slug}`}
                  className={cn(
                    "relative rounded-md px-3 py-1.5 text-sm transition-colors",
                    isActive
                      ? "text-fg"
                      : "text-fg-muted hover:text-fg",
                  )}
                >
                  {d.label}
                  {isActive && (
                    <span className="absolute inset-x-3 -bottom-[13px] h-[2px] rounded-full bg-accent" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <BackendStatus />
          <button
            type="button"
            onClick={toggle}
            aria-label="Toggle theme"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-bg-elevated text-fg-muted transition-colors hover:border-border-strong hover:text-fg"
          >
            <span className="text-[11px] font-mono uppercase tracking-wider">
              {theme === "dark" ? "Lt" : "Dk"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}
