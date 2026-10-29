"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Badge, statusTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, Skeleton } from "@/components/ui/skeleton";

export default function RecruiterJobPage() {
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Job>(`/jobs/${params.id}`)
      .then(setJob)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load job"));
  }, [params.id]);
  if (error) return <ErrorState message={error} />;
  if (!job) return <Skeleton className="h-48" />;

  async function act(path: string) {
    const updated = await api<Job>(path, { method: "POST" });
    setJob(updated);
    toast.success(`Job ${updated.status}`);
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>{job.title}</CardTitle>
        <Badge tone={statusTone(job.status)}>{job.status}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea
          value={job.description}
          onChange={(e) => setJob({ ...job, description: e.target.value })}
          onBlur={async () => {
            const updated = await api<Job>(`/jobs/${job.id}`, { method: "PATCH", body: JSON.stringify({ description: job.description }) });
            setJob(updated);
          }}
        />
        <p className="text-sm">Required: {job.required_skills.join(", ")}</p>
        <p className="text-sm">Preferred: {job.preferred_skills.join(", ")}</p>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => act(`/jobs/${job.id}/publish`)}>Publish</Button>
          <Button variant="outline" onClick={() => act(`/jobs/${job.id}/close`)}>
            Close
          </Button>
          <Button variant="outline" onClick={() => act(`/jobs/${job.id}/archive`)}>
            Archive
          </Button>
          <Button variant="secondary" asChild>
            <Link href={`/recruiter/jobs/${job.id}/candidates`}>Review candidates</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
