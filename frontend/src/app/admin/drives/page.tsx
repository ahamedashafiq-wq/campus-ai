"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";

type Drive = { id: string; title: string; description?: string | null; is_active: boolean };

export default function DrivesPage() {
  const [rows, setRows] = useState<Drive[] | null>(null);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  async function load() {
    try {
      setRows(await api<Drive[]>("/admin/drives"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load drives");
    }
  }
  useEffect(() => {
    void load();
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-40" />;
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input placeholder="Drive title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Button
          disabled={!title.trim()}
          onClick={async () => {
            await api("/admin/drives", { method: "POST", body: JSON.stringify({ title }) });
            setTitle("");
            toast.success("Drive created");
            await load();
          }}
        >
          Create
        </Button>
      </div>
      {rows.length === 0 ? (
        <EmptyState title="No placement drives" description="Create a drive to group campus hiring activity." />
      ) : (
        rows.map((d) => (
          <div key={d.id} className="rounded-xl border bg-white p-4">
            <p className="font-medium">{d.title}</p>
            <p className="text-sm text-slate-500">{d.is_active ? "active" : "inactive"}</p>
          </div>
        ))
      )}
    </div>
  );
}
