"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

type Company = { id: string; name: string; website?: string | null; verification_status: string };

export default function CompaniesPage() {
  const [rows, setRows] = useState<Company[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function load() {
    try {
      setRows(await api<Company[]>("/admin/companies"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load companies");
    }
  }
  useEffect(() => {
    void load();
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;
  if (rows.length === 0) return <EmptyState title="No companies" description="Companies appear when recruiters register." />;
  return (
    <div className="space-y-3">
      {rows.map((c) => (
        <div key={c.id} className="flex items-center justify-between rounded-xl border bg-white p-4">
          <div>
            <p className="font-medium">{c.name}</p>
            <Badge tone={statusTone(c.verification_status)}>{c.verification_status}</Badge>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={() => api(`/admin/companies/${c.id}/verify?status=verified`, { method: "POST" }).then(() => { toast.success("Verified"); return load(); })}>
              Verify
            </Button>
            <Button size="sm" variant="outline" onClick={() => api(`/admin/companies/${c.id}/verify?status=rejected`, { method: "POST" }).then(() => { toast.success("Rejected"); return load(); })}>
              Reject
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
