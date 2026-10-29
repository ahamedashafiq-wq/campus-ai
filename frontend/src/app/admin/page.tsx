"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

type Analytics = {
  users_by_role: Record<string, number>;
  applications_by_status: Record<string, number>;
  jobs_by_status: Record<string, number>;
  students_by_department: { department: string; count: number }[];
  top_skills: { skill: string; count: number }[];
  totals: { users: number; jobs: number; applications: number; companies: number };
};

export default function AdminDashboard() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Analytics>("/admin/analytics")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load analytics"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!data) return <Skeleton className="h-64" />;
  const appChart = Object.entries(data.applications_by_status).map(([status, count]) => ({ status, count }));
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        {Object.entries(data.totals).map(([k, v]) => (
          <Card key={k}>
            <CardHeader>
              <CardTitle className="capitalize">{k}</CardTitle>
            </CardHeader>
            <CardContent className="text-3xl font-semibold">{v}</CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Applications by stage</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          {appChart.every((r) => r.count === 0) ? (
            <EmptyState title="No applications" description="Charts stay empty until real applications exist." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={appChart}>
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
          <CardTitle>Skills demand (student-confirmed/extracted)</CardTitle>
        </CardHeader>
        <CardContent>
          {data.top_skills.length === 0 ? (
            <EmptyState title="No skill records" description="Skills appear after resume extraction or student confirmation." />
          ) : (
            <ul className="text-sm">
              {data.top_skills.map((s) => (
                <li key={s.skill}>
                  {s.skill}: {s.count}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      <a className="text-sm text-teal-700 underline" href="/api/v1/admin/export/applications.csv">
        Export applications CSV
      </a>
    </div>
  );
}
