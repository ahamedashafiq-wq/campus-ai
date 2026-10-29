"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import type { Job, MatchResult } from "@/lib/types";
import { Badge, statusTone } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";
import { formatDate, scoreColor } from "@/lib/utils";

type Dashboard = {
  profile: { full_name: string; department?: string | null };
  skills: { name: string; confirmed: boolean; source: string }[];
  resume: { id: string | null; status: string | null; completeness: { score?: number }; error_message?: string | null };
  recommendations: { job: Job; match: MatchResult }[];
  applications_count: number;
  upcoming_interviews: { id: string; scheduled_at: string; location_or_link?: string | null }[];
  application_status_counts: Record<string, number>;
};

export default function StudentDashboard() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Dashboard>("/students/me/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Dashboard unavailable"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-64" />;

  const chart = Object.entries(data.application_status_counts).map(([status, count]) => ({ status, count }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Hello, {data.profile.full_name}</h1>
        <p className="text-slate-500">{data.profile.department || "Add your department in Profile"}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Resume</CardTitle>
          </CardHeader>
          <CardContent>
            {data.resume.id ? (
              <>
                <Badge tone={statusTone(data.resume.status || "")}>{data.resume.status}</Badge>
                <p className="mt-2 text-sm">Completeness: {data.resume.completeness?.score ?? 0} / 100</p>
                {data.resume.error_message ? <p className="text-sm text-amber-700">{data.resume.error_message}</p> : null}
              </>
            ) : (
              <p className="text-sm text-slate-500">No resume uploaded yet.</p>
            )}
            <Link className="mt-2 inline-block text-sm text-teal-700 underline" href="/student/resume">
              Manage resume
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Applications</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{data.applications_count}</p>
            <Link className="text-sm text-teal-700 underline" href="/student/applications">
              View timeline
            </Link>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Confirmed skills</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-1">
            {data.skills.filter((s) => s.confirmed).length === 0 ? (
              <p className="text-sm text-slate-500">Confirm extracted skills on your profile.</p>
            ) : (
              data.skills
                .filter((s) => s.confirmed)
                .map((s) => <Badge key={s.name}>{s.name}</Badge>)
            )}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Application stages</CardTitle>
        </CardHeader>
        <CardContent className="h-56">
          {chart.length === 0 ? (
            <EmptyState title="No applications yet" description="Published jobs you apply to will appear in this chart." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <XAxis dataKey="status" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#0f766e" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Recommended jobs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.recommendations.length === 0 ? (
            <EmptyState
              title="No published jobs to score"
              description="When recruiters publish roles, match scores are calculated from your skills and resume text."
            />
          ) : (
            data.recommendations.map((item) => (
              <Link
                key={item.job.id}
                href={`/student/jobs/${item.job.id}`}
                className="flex items-center justify-between rounded-md border border-slate-200 p-3 hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium">{item.job.title}</p>
                  <p className="text-sm text-slate-500">{item.job.company_name}</p>
                </div>
                <p className={`text-lg font-semibold ${scoreColor(item.match.overall_score)}`}>
                  {item.match.overall_score.toFixed(0)}
                </p>
              </Link>
            ))
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Upcoming interviews</CardTitle>
        </CardHeader>
        <CardContent>
          {data.upcoming_interviews.length === 0 ? (
            <EmptyState title="No interviews scheduled" description="When a recruiter books a time, it will show here." />
          ) : (
            <ul className="space-y-2 text-sm">
              {data.upcoming_interviews.map((i) => (
                <li key={i.id}>
                  {formatDate(i.scheduled_at)} {i.location_or_link ? `· ${i.location_or_link}` : ""}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
