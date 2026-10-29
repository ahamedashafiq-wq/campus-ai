"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Badge, statusTone } from "@/components/ui/badge";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

export default function RecruiterJobsPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ jobs: Job[] }>("/recruiters/me/dashboard")
      .then((res) => setJobs(res.jobs))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load jobs"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!jobs) return <Skeleton className="h-40" />;
  if (jobs.length === 0) return <EmptyState title="No jobs" description="Create a job from the New job page." />;
  return (
    <div className="space-y-3">
      {jobs.map((job) => (
        <Link key={job.id} href={`/recruiter/jobs/${job.id}`} className="flex items-center justify-between rounded-xl border bg-white p-4">
          <div>
            <p className="font-medium">{job.title}</p>
            <p className="text-sm text-slate-500">{job.applicant_count ?? 0} applicants</p>
          </div>
          <Badge tone={statusTone(job.status)}>{job.status}</Badge>
        </Link>
      ))}
    </div>
  );
}
