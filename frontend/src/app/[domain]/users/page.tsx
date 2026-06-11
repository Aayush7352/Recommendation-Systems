import { notFound } from "next/navigation";
import type { Domain } from "@/lib/types";
import { UsersBrowser } from "@/components/UsersBrowser";

export default async function UsersPage({
  params,
}: {
  params: Promise<{ domain: string }>;
}) {
  const { domain } = await params;
  if (domain !== "movies" && domain !== "news") notFound();
  return <UsersBrowser domain={domain as Domain} />;
}
