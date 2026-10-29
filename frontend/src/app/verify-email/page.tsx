"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

function Verify() {
  const params = useSearchParams();
  const [message, setMessage] = useState("Verifying…");
  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setMessage("Missing verification token.");
      return;
    }
    api(`/auth/verify-email?token=${encodeURIComponent(token)}`, { method: "POST" })
      .then(() => setMessage("Email verified. You can continue using the platform."))
      .catch((err) => setMessage(err instanceof Error ? err.message : "Verification failed"));
  }, [params]);
  return <p className="p-8 text-sm text-slate-700">{message}</p>;
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <Verify />
    </Suspense>
  );
}
