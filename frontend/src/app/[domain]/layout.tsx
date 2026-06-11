import Link from "next/link";
import { notFound } from "next/navigation";
import type { Domain } from "@/lib/types";
import { DomainTabs } from "@/components/DomainTabs";

const DOMAIN_LABEL: Record<Domain, { name: string; source: string }> = {
  movies: { name: "Movies", source: "MovieLens-100K" },
  news: { name: "News", source: "Microsoft MIND-small" },
};

export default async function DomainLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ domain: string }>;
}) {
  const { domain } = await params;
  if (domain !== "movies" && domain !== "news") notFound();
  const meta = DOMAIN_LABEL[domain as Domain];

  return (
    <div className="flex flex-col gap-8 py-6">
      <div className="flex flex-col gap-3">
        <Link
          href="/"
          className="w-fit font-mono text-[11px] uppercase tracking-wider text-fg-subtle hover:text-fg-muted"
        >
          ← Lab
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-fg-subtle">
              {meta.source}
            </span>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-fg">
              {meta.name}
            </h1>
          </div>
          <DomainTabs domain={domain as Domain} />
        </div>
      </div>
      {children}
    </div>
  );
}
