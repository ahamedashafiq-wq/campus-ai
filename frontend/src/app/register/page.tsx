"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { homeFor, useAuth } from "@/lib/auth";
import type { User } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const studentSchema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
  department: z.string().optional(),
  degree: z.string().optional(),
  graduation_year: z.string().optional(),
});

const recruiterSchema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
  company_name: z.string().min(2),
  company_website: z.string().optional(),
  title: z.string().optional(),
});

function RegisterForm() {
  const params = useSearchParams();
  const initial = params.get("role") === "recruiter" ? "recruiter" : "student";
  const [role, setRole] = useState<"student" | "recruiter">(initial);
  const router = useRouter();
  const { refresh } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const schema = useMemo(() => (role === "student" ? studentSchema : recruiterSchema), [role]);
  const form = useForm({ resolver: zodResolver(schema) });

  async function onSubmit(values: Record<string, string>) {
    setError(null);
    try {
      const path = role === "student" ? "/auth/register/student" : "/auth/register/recruiter";
      const body =
        role === "student"
          ? {
              ...values,
              graduation_year: values.graduation_year ? Number(values.graduation_year) : undefined,
            }
          : values;
      const user = await api<User>(path, { method: "POST", body: JSON.stringify(body) });
      await refresh();
      toast.success("Account created");
      router.push(homeFor(user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Create a CampusMatch AI account</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex gap-2">
            <Button type="button" variant={role === "student" ? "default" : "outline"} onClick={() => setRole("student")}>
              Student
            </Button>
            <Button
              type="button"
              variant={role === "recruiter" ? "default" : "outline"}
              onClick={() => setRole("recruiter")}
            >
              Recruiter
            </Button>
          </div>
          <p className="mb-4 text-xs text-slate-500">Administrator accounts cannot be created here.</p>
          <form className="space-y-3" onSubmit={form.handleSubmit(onSubmit)}>
            <Field form={form} name="full_name" label="Full name" />
            <Field form={form} name="email" label="Email" type="email" />
            <Field form={form} name="password" label="Password" type="password" />
            {role === "student" ? (
              <>
                <Field form={form} name="department" label="Department" />
                <Field form={form} name="degree" label="Degree" />
                <Field form={form} name="graduation_year" label="Graduation year" />
              </>
            ) : (
              <>
                <Field form={form} name="company_name" label="Company name" />
                <Field form={form} name="company_website" label="Company website" />
                <Field form={form} name="title" label="Your title" />
              </>
            )}
            {error ? <p className="text-sm text-rose-700">{error}</p> : null}
            <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? "Creating…" : "Create account"}
            </Button>
          </form>
          <p className="mt-4 text-sm">
            Already registered?{" "}
            <Link className="underline" href="/login">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({
  form,
  name,
  label,
  type = "text",
}: {
  form: { register: (name: string) => object };
  name: string;
  label: string;
  type?: string;
}) {
  return (
    <div>
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} type={type} {...form.register(name)} />
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}
