"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Badge, statusTone } from "@/components/ui/badge";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

export default function JobsPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      api<{ items: Job[] }>(`/jobs?q=${encodeURIComponent(q)}`)
        .then((res) => setItems(res.items))
        .catch((err) => setError(err instanceof Error ? err.message : "Unable to load jobs"));
    }, 200);
    return () => clearTimeout(handle);
  }, [q]);

  if (error) return <ErrorState message={error} />;
  if (!items) return <Skeleton className="h-48" />;

  return (
    <div className="space-y-4">
      <Input placeholder="Search published jobs" value={q} onChange={(e) => setQ(e.target.value)} />
      {items.length === 0 ? (
        <EmptyState title="No published jobs" description="When recruiters publish roles, they will appear here." />
      ) : (
        items.map((job) => (
          <Link key={job.id} href={`/student/jobs/${job.id}`} className="block rounded-xl border border-slate-200 bg-white p-4 hover:border-teal-300">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">{job.title}</h2>
              <Badge tone={statusTone(job.status)}>{job.status}</Badge>
            </div>
            <p className="text-sm text-slate-500">
              {job.company_name} · {job.location || "Location not specified"}
            </p>
            <p className="mt-2 line-clamp-2 text-sm text-slate-600">{job.description}</p>
          </Link>
        ))
      )}
    </div>
  );
}
