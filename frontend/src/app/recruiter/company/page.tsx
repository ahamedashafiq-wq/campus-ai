"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, Skeleton } from "@/components/ui/skeleton";

type Company = {
  id: string;
  name: string;
  website?: string | null;
  description?: string | null;
  industry?: string | null;
  verification_status: string;
};

export default function CompanyPage() {
  const [company, setCompany] = useState<Company | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<{ companies: Company[] }>("/recruiters/me")
      .then((res) => setCompany(res.companies[0] || null))
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load company"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!company) return <Skeleton className="h-48" />;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Company profile <Badge tone={statusTone(company.verification_status)}>{company.verification_status}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input value={company.name} onChange={(e) => setCompany({ ...company, name: e.target.value })} />
        <Input value={company.website || ""} onChange={(e) => setCompany({ ...company, website: e.target.value })} />
        <Input value={company.industry || ""} onChange={(e) => setCompany({ ...company, industry: e.target.value })} />
        <Textarea value={company.description || ""} onChange={(e) => setCompany({ ...company, description: e.target.value })} />
        <Button
          onClick={async () => {
            await api(`/recruiters/me/company/${company.id}`, { method: "PATCH", body: JSON.stringify(company) });
            toast.success("Company updated");
          }}
        >
          Save
        </Button>
      </CardContent>
    </Card>
  );
}
