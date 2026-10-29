"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Badge, statusTone } from "@/components/ui/badge";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

export default function AdminJobsPage() {
  const [rows, setRows] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ items: Job[] }>("/admin/jobs")
      .then((res) => setRows(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load jobs"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;
  if (rows.length === 0) return <EmptyState title="No jobs" description="Job oversight stays empty until recruiters create postings." />;
  return (
    <div className="space-y-3">
      {rows.map((job) => (
        <div key={job.id} className="rounded-xl border bg-white p-4">
          <div className="flex items-center justify-between">
            <p className="font-medium">
              {job.title} · {job.company_name}
            </p>
            <Badge tone={statusTone(job.status)}>{job.status}</Badge>
          </div>
        </div>
      ))}
    </div>
  );
}
