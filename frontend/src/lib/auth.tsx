"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, ApiRequestError } from "./api";
import type { Role, User } from "./types";

type AuthState = {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await api<User>("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch {
      /* still clear local session */
    }
    setUser(null);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(() => ({ user, loading, refresh, logout }), [user, loading, refresh, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function RequireRole({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (!roles.includes(user.role)) {
      if (user.role === "student") router.replace("/student");
      else if (user.role === "recruiter") router.replace("/recruiter");
      else router.replace("/admin");
    }
  }, [loading, user, roles, router, pathname]);

  if (loading || !user || !roles.includes(user.role)) {
    return <div className="p-8 text-sm text-slate-500">Checking your session…</div>;
  }
  return <>{children}</>;
}

export function homeFor(role: Role) {
  if (role === "recruiter") return "/recruiter";
  if (role === "admin") return "/admin";
  return "/student";
}

export function isUnauthorized(err: unknown) {
  return err instanceof ApiRequestError && err.status === 401;
}
