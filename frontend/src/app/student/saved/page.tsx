"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

export default function SavedJobsPage() {
  const [rows, setRows] = useState<{ job_id: string; job: Job | null }[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setRows(await api("/students/me/saved-jobs"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load saved jobs");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;

  return (
    <div className="space-y-3">
      {rows.length === 0 ? (
        <EmptyState title="No saved jobs" description="Save a published role from the job details page." />
      ) : (
        rows.map((r) => (
          <div key={r.job_id} className="flex items-center justify-between rounded-xl border bg-white p-4">
            <Link href={`/student/jobs/${r.job_id}`} className="font-medium">
              {r.job?.title || r.job_id}
            </Link>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                await api(`/students/me/saved-jobs/${r.job_id}`, { method: "DELETE" });
                await load();
              }}
            >
              Remove
            </Button>
          </div>
        ))
      )}
    </div>
  );
}
