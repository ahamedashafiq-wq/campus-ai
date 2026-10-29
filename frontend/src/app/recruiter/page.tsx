"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

type Dash = {
  companies: { id: string; name: string; verification_status: string }[];
  jobs: Job[];
  job_count: number;
  application_count: number;
};

export default function RecruiterDashboard() {
  const [data, setData] = useState<Dash | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Dash>("/recruiters/me/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load dashboard"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-64" />;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Jobs</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{data.job_count}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Applications</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{data.application_count}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Company verification</CardTitle>
          </CardHeader>
          <CardContent>
            {data.companies.map((c) => (
              <p key={c.id}>
                {c.name} <Badge tone={statusTone(c.verification_status)}>{c.verification_status}</Badge>
              </p>
            ))}
          </CardContent>
        </Card>
      </div>
      {data.jobs.length === 0 ? (
        <EmptyState title="No jobs yet" description="Create a job, then publish it before students can apply." />
      ) : (
        data.jobs.map((job) => (
          <Link key={job.id} href={`/recruiter/jobs/${job.id}`} className="flex items-center justify-between rounded-xl border bg-white p-4">
            <div>
              <p className="font-medium">{job.title}</p>
              <p className="text-sm text-slate-500">{job.applicant_count ?? 0} applicants</p>
            </div>
            <Badge tone={statusTone(job.status)}>{job.status}</Badge>
          </Link>
        ))
      )}
    </div>
  );
}
