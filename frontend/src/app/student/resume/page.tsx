"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, apiBlob } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";

type Resume = {
  id: string;
  original_filename: string;
  size_bytes: number;
  status: string;
  is_active: boolean;
  error_message?: string | null;
  created_at: string;
  extraction?: {
    char_count: number;
    extracted_skills: { name: string; slug: string }[];
    completeness: { score?: number };
    extraction_notes?: string | null;
    uncertain_fields: string[];
    has_raw_text: boolean;
  } | null;
};

export default function ResumePage() {
  const [rows, setRows] = useState<Resume[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function load() {
    try {
      setRows(await api<Resume[]>("/resumes"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load resumes");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!rows) return <Skeleton className="h-48" />;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Upload resume (PDF)</CardTitle>
        </CardHeader>
        <CardContent>
          <input
            type="file"
            accept="application/pdf,.pdf"
            disabled={uploading}
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const data = new FormData();
              data.append("file", file);
              setUploading(true);
              try {
                await api("/resumes", { method: "POST", body: data });
                toast.success("Resume stored and processed");
                await load();
              } catch (err) {
                toast.error(err instanceof Error ? err.message : "Upload failed");
              } finally {
                setUploading(false);
                e.target.value = "";
              }
            }}
          />
          <p className="mt-2 text-xs text-slate-500">
            Success is reported only after storage and database persistence. Scanned PDFs without text will be marked
            no_text; OCR is optional and off unless configured.
          </p>
        </CardContent>
      </Card>
      {rows.length === 0 ? (
        <EmptyState title="No resumes" description="Upload a text-based PDF to extract skills and enable matching." />
      ) : (
        rows.map((r) => (
          <Card key={r.id}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>
                {r.original_filename} {r.is_active ? "(active)" : ""}
              </CardTitle>
              <Badge tone={statusTone(r.status)}>{r.status}</Badge>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>
                {formatDate(r.created_at)} · {(r.size_bytes / 1024).toFixed(1)} KB
              </p>
              {r.error_message ? <p className="text-amber-700">{r.error_message}</p> : null}
              {r.extraction ? (
                <>
                  <p>Extracted characters: {r.extraction.char_count}</p>
                  <p>Completeness: {r.extraction.completeness?.score ?? 0}</p>
                  <p>{r.extraction.extraction_notes}</p>
                  <div className="flex flex-wrap gap-1">
                    {r.extraction.extracted_skills.map((s) => (
                      <Badge key={s.slug}>{s.name}</Badge>
                    ))}
                  </div>
                </>
              ) : null}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    const blob = await apiBlob(`/resumes/${r.id}/file`);
                    const url = URL.createObjectURL(blob);
                    window.open(url, "_blank");
                  }}
                >
                  Download
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={async () => {
                    await api(`/resumes/${r.id}`, { method: "DELETE" });
                    await load();
                  }}
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
