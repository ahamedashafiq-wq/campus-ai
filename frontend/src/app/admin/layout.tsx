"use client";

import { AppShell } from "@/components/layout/app-shell";
import { RequireRole } from "@/lib/auth";

const nav = [
  { href: "/admin", label: "Analytics" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/companies", label: "Companies" },
  { href: "/admin/jobs", label: "Jobs" },
  { href: "/admin/drives", label: "Placement drives" },
  { href: "/admin/audit", label: "Audit log" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireRole roles={["admin"]}>
      <AppShell title="Administrator" nav={nav}>
        {children}
      </AppShell>
    </RequireRole>
  );
}
