"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, GraduationCap, LogOut, Menu } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { Button } from "../ui/button";
import { cn } from "@/lib/utils";

type NavItem = { href: string; label: string };

export function AppShell({ title, nav, children }: { title: string; nav: NavItem[]; children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <button className="md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Toggle navigation">
              <Menu className="h-5 w-5" />
            </button>
            <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
              <GraduationCap className="h-5 w-5 text-teal-700" />
              CampusMatch AI
            </Link>
            <span className="hidden text-sm text-slate-500 sm:inline">{title}</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Link href="/notifications" className="text-slate-600 hover:text-slate-900" aria-label="Notifications">
              <Bell className="h-4 w-4" />
            </Link>
            <span className="hidden text-slate-600 sm:inline">{user?.full_name}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={async () => {
                await logout();
                router.push("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </header>
      <div className="mx-auto flex max-w-7xl">
        <aside
          className={cn(
            "w-56 shrink-0 border-r border-slate-200 bg-white p-3 md:block",
            open ? "block" : "hidden md:block",
          )}
        >
          <nav className="flex flex-col gap-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-3 py-2 text-sm",
                  pathname === item.href ? "bg-teal-50 font-medium text-teal-800" : "text-slate-600 hover:bg-slate-50",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
