import { notFound } from "next/navigation";
import type { Domain } from "@/lib/types";
import { EvaluationView } from "@/components/EvaluationView";

export default async function EvaluationPage({
  params,
}: {
  params: Promise<{ domain: string }>;
}) {
  const { domain } = await params;
  if (domain !== "movies" && domain !== "news") notFound();
  return <EvaluationView domain={domain as Domain} />;
}
