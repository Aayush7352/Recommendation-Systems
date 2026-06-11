import { notFound } from "next/navigation";
import type { Domain } from "@/lib/types";
import { CompareView } from "@/components/CompareView";

export default async function ComparePage({
  params,
  searchParams,
}: {
  params: Promise<{ domain: string }>;
  searchParams: Promise<{ user_id?: string }>;
}) {
  const { domain } = await params;
  const { user_id } = await searchParams;
  if (domain !== "movies" && domain !== "news") notFound();
  return <CompareView domain={domain as Domain} initialUserId={user_id ?? null} />;
}
