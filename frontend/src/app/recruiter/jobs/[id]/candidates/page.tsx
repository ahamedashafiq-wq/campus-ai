"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { MatchPanel } from "@/components/match-panel";
import { Badge, statusTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { Application, MatchResult } from "@/lib/types";

const recruiterStatuses = ["under_review", "shortlisted", "interview_scheduled", "selected", "rejected"];

export default function CandidatesPage() {
  const params = useParams<{ id: string }>();
  const [rows, setRows] = useState<Application[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [when, setWhen] = useState("");

  async function load() {
    try {
      setRows(await api<Application[]>(`/applications/jobs/${params.id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load applicants");
    }
  }

  useEffect(() => {
    void load();
  }, [params.id]);

  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-48" />;
  if (rows.length === 0) {
    return <EmptyState title="No applicants" description="Applications submitted to this job will appear here with match explanations." />;
  }

  return (
    <div className="space-y-4">
      {rows.map((app) => (
        <Card key={app.id}>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>{app.student_name || app.student_id}</CardTitle>
            <Badge tone={statusTone(app.status)}>{app.status}</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {app.match ? <MatchPanel match={app.match as MatchResult} /> : <p className="text-sm text-slate-500">No stored match yet.</p>}
            <div className="flex flex-wrap gap-2">
              {recruiterStatuses.map((status) => (
                <Button
                  key={status}
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    try {
                      await api(`/applications/${app.id}/status`, { method: "POST", body: JSON.stringify({ status }) });
                      toast.success(`Moved to ${status}`);
                      await load();
                    } catch (err) {
                      toast.error(err instanceof Error ? err.message : "Invalid transition");
                    }
                  }}
                >
                  {status}
                </Button>
              ))}
            </div>
            <div className="flex gap-2">
              <Input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
              <Button
                size="sm"
                disabled={!when}
                title={!when ? "Choose a date and time" : undefined}
                onClick={async () => {
                  await api("/interviews", {
                    method: "POST",
                    body: JSON.stringify({ application_id: app.id, scheduled_at: new Date(when).toISOString() }),
                  });
                  toast.success("Interview scheduled");
                  await load();
                }}
              >
                Schedule interview
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
