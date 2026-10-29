"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ErrorState, Skeleton } from "@/components/ui/skeleton";

type Profile = {
  full_name: string;
  email: string;
  department?: string | null;
  degree?: string | null;
  graduation_year?: number | null;
  cgpa?: number | null;
  headline?: string | null;
  bio?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  experience_summary?: string | null;
};

type Skill = { id: string; skill_name: string; confirmed: boolean; source: string; category: string };

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [newSkill, setNewSkill] = useState("");

  useEffect(() => {
    Promise.all([api<Profile>("/students/me"), api<Skill[]>("/students/me/skills")])
      .then(([p, s]) => {
        setProfile(p);
        setSkills(s);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load profile"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!profile) return <Skeleton className="h-64" />;

  async function save() {
    const updated = await api<Profile>("/students/me", { method: "PATCH", body: JSON.stringify(profile) });
    setProfile(updated);
    toast.success("Profile saved");
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Student profile</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {(
            [
              ["full_name", "Full name"],
              ["department", "Department"],
              ["degree", "Degree"],
              ["graduation_year", "Graduation year"],
              ["cgpa", "CGPA"],
              ["headline", "Headline"],
              ["github_url", "GitHub"],
              ["linkedin_url", "LinkedIn"],
              ["portfolio_url", "Portfolio"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="text-sm">
              <span className="mb-1 block text-slate-600">{label}</span>
              <Input
                value={profile[key] ?? ""}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    [key]: key === "graduation_year" || key === "cgpa" ? Number(e.target.value) || null : e.target.value,
                  })
                }
              />
            </label>
          ))}
          <label className="text-sm md:col-span-2">
            <span className="mb-1 block text-slate-600">Experience summary</span>
            <Textarea value={profile.experience_summary ?? ""} onChange={(e) => setProfile({ ...profile, experience_summary: e.target.value })} />
          </label>
          <div className="md:col-span-2">
            <Button onClick={() => void save()}>Save profile</Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Skills</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-3 text-xs text-slate-500">
            Extracted skills stay labeled until you confirm them. Confirming does not invent qualifications.
          </p>
          <div className="flex flex-wrap gap-2">
            {skills.map((s) => (
              <button
                key={s.id}
                className="rounded-full border px-3 py-1 text-xs"
                onClick={async () => {
                  const next = await api<Skill[]>("/students/me/skills", {
                    method: "POST",
                    body: JSON.stringify([{ name: s.skill_name, confirmed: !s.confirmed }]),
                  });
                  setSkills(next);
                }}
              >
                {s.skill_name} <Badge>{s.confirmed ? "confirmed" : s.source}</Badge>
              </button>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <Input placeholder="Add a skill you actually have" value={newSkill} onChange={(e) => setNewSkill(e.target.value)} />
            <Button
              onClick={async () => {
                if (!newSkill.trim()) return;
                const next = await api<Skill[]>("/students/me/skills", {
                  method: "POST",
                  body: JSON.stringify([{ name: newSkill, confirmed: true }]),
                });
                setSkills(next);
                setNewSkill("");
              }}
            >
              Add
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
