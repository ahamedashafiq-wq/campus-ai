"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<string | null>(null);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Reset password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input type="email" placeholder="Account email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Button
            onClick={async () => {
              const res = await api<{ accepted: boolean; email_configured: boolean }>("/auth/password/reset/request", {
                method: "POST",
                body: JSON.stringify({ email }),
              });
              setResult(
                res.email_configured
                  ? "If that account exists, a reset email was sent."
                  : "Request accepted. Email delivery is not configured on this server, so no message was sent.",
              );
            }}
          >
            Request reset
          </Button>
          {result ? <p className="text-sm text-slate-600">{result}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
