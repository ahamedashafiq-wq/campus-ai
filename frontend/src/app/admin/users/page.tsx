"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

type Row = { id: string; email: string; full_name: string; role: string; is_active: boolean; email_verified: boolean };

export default function UsersPage() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function load() {
    try {
      setRows(await api<Row[]>("/admin/users"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load users");
    }
  }
  useEffect(() => {
    void load();
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;
  if (rows.length === 0) return <EmptyState title="No users" description="Register students and recruiters, then bootstrap an administrator from the CLI." />;
  return (
    <div className="overflow-x-auto rounded-xl border bg-white">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b bg-slate-50">
            <th className="p-3">Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((u) => (
            <tr key={u.id} className="border-b">
              <td className="p-3">{u.full_name}</td>
              <td>{u.email}</td>
              <td>
                <Badge>{u.role}</Badge>
              </td>
              <td>{u.is_active ? "active" : "disabled"}</td>
              <td>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    await api(`/admin/users/${u.id}/active?active=${!u.is_active}`, { method: "POST" });
                    toast.success("Updated");
                    await load();
                  }}
                >
                  {u.is_active ? "Disable" : "Enable"}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
