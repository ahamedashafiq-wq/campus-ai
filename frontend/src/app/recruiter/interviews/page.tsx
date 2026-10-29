"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/badge";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";

type Interview = { id: string; application_id: string; scheduled_at: string; location_or_link?: string | null; status: string };

export default function InterviewsPage() {
  const [rows, setRows] = useState<Interview[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Interview[]>("/interviews")
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load interviews"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;
  if (rows.length === 0) return <EmptyState title="No interviews" description="Schedule interviews from a job's candidate list." />;
  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.id} className="rounded-xl border bg-white p-4">
          <div className="flex items-center justify-between">
            <p className="font-medium">{formatDate(row.scheduled_at)}</p>
            <Badge tone={statusTone(row.status)}>{row.status}</Badge>
          </div>
          <p className="text-sm text-slate-500">{row.location_or_link || "No location provided"}</p>
        </div>
      ))}
    </div>
  );
}
