"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";

type Row = { id: string; action: string; resource_type: string; resource_id?: string | null; created_at: string };

export default function AuditPage() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Row[]>("/admin/audit")
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load audit log"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;
  if (rows.length === 0) return <EmptyState title="No audit events" description="Authentication and recruitment actions write audit records." />;
  return (
    <div className="overflow-x-auto rounded-xl border bg-white">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b bg-slate-50">
            <th className="p-3">When</th>
            <th>Action</th>
            <th>Resource</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-b">
              <td className="p-3">{formatDate(r.created_at)}</td>
              <td>{r.action}</td>
              <td>
                {r.resource_type} {r.resource_id}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
