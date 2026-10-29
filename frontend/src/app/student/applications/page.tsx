"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Application } from "@/lib/types";
import { Badge, statusTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";

export default function ApplicationsPage() {
  const [rows, setRows] = useState<Application[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setRows(await api<Application[]>("/applications/me"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load applications");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-48" />;

  return (
    <div className="space-y-4">
      {rows.length === 0 ? (
        <EmptyState title="No applications" description="Submitted applications are stored in PostgreSQL and listed here." />
      ) : (
        rows.map((app) => (
          <Card key={app.id}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>
                {app.job_title} · {app.company_name}
              </CardTitle>
              <Badge tone={statusTone(app.status)}>{app.status}</Badge>
            </CardHeader>
            <CardContent className="text-sm">
              <p>Submitted {formatDate(app.submitted_at)}</p>
              <ol className="mt-2 list-decimal pl-5">
                {(app.history || []).map((h, i) => (
                  <li key={i}>
                    {h.from_status || "new"} → {h.to_status} · {formatDate(h.created_at)}
                  </li>
                ))}
              </ol>
              {["withdrawn", "selected", "rejected"].includes(app.status) ? null : (
                <Button
                  className="mt-3"
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      await api(`/applications/${app.id}/withdraw`, { method: "POST" });
                      toast.success("Withdrawn");
                      await load();
                    } catch (err) {
                      toast.error(err instanceof Error ? err.message : "Cannot withdraw");
                    }
                  }}
                >
                  Withdraw
                </Button>
              )}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
