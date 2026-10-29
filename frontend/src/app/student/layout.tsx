"use client";

import { AppShell } from "@/components/layout/app-shell";
import { RequireRole } from "@/lib/auth";

const nav = [
  { href: "/student", label: "Dashboard" },
  { href: "/student/profile", label: "Profile" },
  { href: "/student/resume", label: "Resume" },
  { href: "/student/jobs", label: "Jobs" },
  { href: "/student/applications", label: "Applications" },
  { href: "/student/saved", label: "Saved jobs" },
];

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireRole roles={["student"]}>
      <AppShell title="Student" nav={nav}>
        {children}
      </AppShell>
    </RequireRole>
  );
}
