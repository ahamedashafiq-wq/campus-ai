"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function ResetForm() {
  const params = useSearchParams();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const token = params.get("token") || "";

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Choose a new password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input type="password" placeholder="New password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button
            disabled={!token || password.length < 8}
            title={!token ? "A reset token is required" : password.length < 8 ? "Password must be at least 8 characters" : undefined}
            onClick={async () => {
              try {
                await api("/auth/password/reset/confirm", {
                  method: "POST",
                  body: JSON.stringify({ token, new_password: password }),
                });
                setMessage("Password reset complete. You can sign in.");
              } catch (err) {
                setMessage(err instanceof Error ? err.message : "Reset failed");
              }
            }}
          >
            Update password
          </Button>
          {message ? <p className="text-sm text-slate-600">{message}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetForm />
    </Suspense>
  );
}
