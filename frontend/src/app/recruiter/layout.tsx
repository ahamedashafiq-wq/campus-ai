"use client";

import { AppShell } from "@/components/layout/app-shell";
import { RequireRole } from "@/lib/auth";

const nav = [
  { href: "/recruiter", label: "Dashboard" },
  { href: "/recruiter/company", label: "Company" },
  { href: "/recruiter/jobs", label: "Jobs" },
  { href: "/recruiter/jobs/new", label: "New job" },
  { href: "/recruiter/interviews", label: "Interviews" },
];

export default function RecruiterLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireRole roles={["recruiter"]}>
      <AppShell title="Recruiter" nav={nav}>
        {children}
      </AppShell>
    </RequireRole>
  );
}
