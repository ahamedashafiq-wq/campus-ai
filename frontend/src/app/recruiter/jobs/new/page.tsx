"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function NewJobPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    description: "",
    responsibilities: "",
    location: "",
    employment_type: "",
    required_skills: "",
    preferred_skills: "",
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create job</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <Textarea placeholder="Description (at least 20 characters)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <Textarea placeholder="Responsibilities" value={form.responsibilities} onChange={(e) => setForm({ ...form, responsibilities: e.target.value })} />
        <Input placeholder="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
        <Input placeholder="Employment type" value={form.employment_type} onChange={(e) => setForm({ ...form, employment_type: e.target.value })} />
        <Input placeholder="Required skills, comma-separated" value={form.required_skills} onChange={(e) => setForm({ ...form, required_skills: e.target.value })} />
        <Input placeholder="Preferred skills, comma-separated" value={form.preferred_skills} onChange={(e) => setForm({ ...form, preferred_skills: e.target.value })} />
        <Button
          disabled={form.title.length < 2 || form.description.length < 20}
          title={form.description.length < 20 ? "Description must be at least 20 characters" : undefined}
          onClick={async () => {
            try {
              const job = await api<Job>("/jobs", {
                method: "POST",
                body: JSON.stringify({
                  ...form,
                  required_skills: form.required_skills.split(",").map((s) => s.trim()).filter(Boolean),
                  preferred_skills: form.preferred_skills.split(",").map((s) => s.trim()).filter(Boolean),
                }),
              });
              toast.success("Draft created");
              router.push(`/recruiter/jobs/${job.id}`);
            } catch (err) {
              toast.error(err instanceof Error ? err.message : "Could not create job");
            }
          }}
        >
          Save draft
        </Button>
      </CardContent>
    </Card>
  );
}
