"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { MatchPanel } from "@/components/match-panel";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { Job, MatchResult } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api<Job>(`/jobs/${params.id}`),
      api<{ match: MatchResult }>(`/matches/jobs/${params.id}/me`).catch(() => null),
    ])
      .then(([j, m]) => {
        setJob(j);
        setMatch(m?.match ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load job"));
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!job) return <Skeleton className="h-64" />;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            {job.title} · {job.company_name}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="whitespace-pre-wrap">{job.description}</p>
          {job.responsibilities ? <p className="whitespace-pre-wrap">{job.responsibilities}</p> : null}
          <p>Required: {job.required_skills.join(", ") || "None listed"}</p>
          <p>Preferred: {job.preferred_skills.join(", ") || "None listed"}</p>
          <Textarea placeholder="Optional cover note" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="flex gap-2">
            <Button
              onClick={async () => {
                try {
                  await api("/applications", { method: "POST", body: JSON.stringify({ job_id: job.id, cover_note: note || null }) });
                  toast.success("Application submitted");
                } catch (err) {
                  toast.error(err instanceof Error ? err.message : "Could not apply");
                }
              }}
            >
              Apply
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                await api(`/students/me/saved-jobs/${job.id}`, { method: "POST" });
                toast.success("Saved");
              }}
            >
              Save job
            </Button>
            <Button variant="ghost" asChild>
              <Link href={`/student/matches/${job.id}`}>Full match explanation</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
      {match ? <MatchPanel match={match} /> : <p className="text-sm text-slate-500">Match score will appear after your profile and resume are available.</p>}
    </div>
  );
}
