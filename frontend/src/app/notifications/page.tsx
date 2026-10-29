"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RequireRole } from "@/lib/auth";
import { formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

type Note = { id: string; title: string; body: string; is_read: boolean; created_at: string };

export default function NotificationsPage() {
  return (
    <RequireRole roles={["student", "recruiter", "admin"]}>
      <Inner />
    </RequireRole>
  );
}

function Inner() {
  const [items, setItems] = useState<Note[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await api<Note[]>("/notifications"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load notifications");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!items) return <Skeleton className="h-40" />;

  return (
    <div className="mx-auto max-w-3xl p-6">
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {items.length === 0 ? (
            <EmptyState title="No notifications" description="Status changes and interviews will appear here." />
          ) : (
            items.map((n) => (
              <div key={n.id} className="rounded-md border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{n.title}</p>
                  {!n.is_read ? (
                    <Button size="sm" variant="outline" onClick={() => api(`/notifications/${n.id}/read`, { method: "POST" }).then(load)}>
                      Mark read
                    </Button>
                  ) : null}
                </div>
                <p className="text-sm text-slate-600">{n.body}</p>
                <p className="text-xs text-slate-400">{formatDate(n.created_at)}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
