"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { homeFor, useAuth } from "@/lib/auth";
import type { User } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { refresh } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

  async function onSubmit(values: z.infer<typeof schema>) {
    setError(null);
    try {
      const user = await api<User>("/auth/login", { method: "POST", body: JSON.stringify(values) });
      await refresh();
      toast.success("Signed in");
      router.push(params.get("next") || homeFor(user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to CampusMatch AI</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" autoComplete="current-password" {...form.register("password")} />
            </div>
            {error ? <p className="text-sm text-rose-700">{error}</p> : null}
            <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 text-sm text-slate-600">
            <Link className="underline" href="/forgot-password">
              Forgot password
            </Link>
            {" · "}
            <Link className="underline" href="/register">
              Create an account
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
