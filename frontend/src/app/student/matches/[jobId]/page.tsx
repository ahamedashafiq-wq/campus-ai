"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { MatchPanel } from "@/components/match-panel";
import { ErrorState, Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { Job, MatchResult } from "@/lib/types";

export default function MatchPage() {
  const params = useParams<{ jobId: string }>();
  const [data, setData] = useState<{ job: Job; match: MatchResult } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ job: Job; match: MatchResult }>(`/matches/jobs/${params.jobId}/me`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load match"));
  }, [params.jobId]);
  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-64" />;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">
        {data.job.title} match explanation
      </h1>
      <MatchPanel match={data.match} />
    </div>
  );
}
