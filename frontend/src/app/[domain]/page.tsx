import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { ALGO_NAMES, type AlgoKey, type Domain } from "@/lib/types";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/Card";
import { StatTile } from "@/components/StatTile";
import { ErrorState } from "@/components/ErrorState";
import { formatNumber } from "@/lib/cn";

export default async function DomainOverview({
  params,
}: {
  params: Promise<{ domain: string }>;
}) {
  const { domain } = await params;
  if (domain !== "movies" && domain !== "news") notFound();
  const d = domain as Domain;

  const [{ data: info, error: infoErr }, { data: users }] = await Promise.all([
    api.getDomainInfo(d),
    api.getUsers(d, 5),
  ]);

  if (infoErr || !info) {
    return (
      <ErrorState
        title="Could not load domain info"
        description={infoErr ?? "Unknown error"}
        hint="Ensure the FastAPI backend is running on http://localhost:8080 and that this domain has been trained."
      />
    );
  }

  const interactionsPerUser = info.n_users > 0 ? info.n_interactions / info.n_users : 0;
  const sparsity =
    info.n_users > 0 && info.n_items > 0
      ? 1 - info.n_interactions / (info.n_users * info.n_items)
      : 0;

  return (
    <div className="grid gap-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Users" value={formatNumber(info.n_users)} hint="distinct user IDs" />
        <StatTile label="Items" value={formatNumber(info.n_items)} hint={d === "movies" ? "films in catalog" : "articles in catalog"} />
        <StatTile label="Interactions" value={formatNumber(info.n_interactions)} hint={`avg ${interactionsPerUser.toFixed(1)} per user`} />
        <StatTile label="Sparsity" value={`${(sparsity * 100).toFixed(2)}%`} hint="of user-item matrix is empty" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Available algorithms</CardTitle>
            <p className="text-xs text-fg-muted">{info.algos.length} models trained for this domain</p>
          </CardHeader>
          <CardBody className="grid gap-px overflow-hidden rounded-lg border border-border bg-border p-0 sm:grid-cols-2">
            {info.algos.map((a) => (
              <div
                key={a}
                className="flex items-center justify-between bg-surface px-4 py-3"
              >
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-fg">
                    {ALGO_NAMES[a as AlgoKey] ?? a}
                  </span>
                  <span className="font-mono text-[11px] text-fg-subtle">{a}</span>
                </div>
                <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-success">
                  ready
                </span>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Jump in</CardTitle>
            <p className="text-xs text-fg-muted">Quick actions</p>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <Link
              href={`/${d}/users`}
              className="flex items-center justify-between rounded-lg border border-border bg-bg-elevated p-3 transition-colors hover:border-border-strong"
            >
              <div className="flex flex-col">
                <span className="text-sm font-medium text-fg">Browse users</span>
                <span className="text-[11px] text-fg-muted">Pick a user and inspect their history</span>
              </div>
              <span className="font-mono text-[11px] text-accent-fg">→</span>
            </Link>
            <Link
              href={users && users[0] ? `/${d}/compare?user_id=${encodeURIComponent(String(users[0].user_id))}` : `/${d}/compare`}
              className="flex items-center justify-between rounded-lg border border-border bg-bg-elevated p-3 transition-colors hover:border-border-strong"
            >
              <div className="flex flex-col">
                <span className="text-sm font-medium text-fg">Compare algorithms</span>
                <span className="text-[11px] text-fg-muted">
                  {users && users[0]
                    ? `Sample with user ${String(users[0].user_id)}`
                    : "Side-by-side reclists"}
                </span>
              </div>
              <span className="font-mono text-[11px] text-accent-fg">→</span>
            </Link>
            <Link
              href={`/${d}/evaluation`}
              className="flex items-center justify-between rounded-lg border border-border bg-bg-elevated p-3 transition-colors hover:border-border-strong"
            >
              <div className="flex flex-col">
                <span className="text-sm font-medium text-fg">Offline evaluation</span>
                <span className="text-[11px] text-fg-muted">Precision · Recall · NDCG · more</span>
              </div>
              <span className="font-mono text-[11px] text-accent-fg">→</span>
            </Link>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
