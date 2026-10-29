import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function backendBase() {
  return process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

async function proxy(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const target = `${backendBase()}/api/v1/${path.join("/")}${req.nextUrl.search}`;
  const headers = new Headers();
  const cookie = req.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);
  const csrf = req.headers.get("x-csrf-token");
  if (csrf) headers.set("x-csrf-token", csrf);
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const authorization = req.headers.get("authorization");
  if (authorization) headers.set("authorization", authorization);

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };
  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = await req.arrayBuffer();
  }

  const upstream = await fetch(target, init);
  const body = await upstream.arrayBuffer();
  const out = new NextResponse(body, { status: upstream.status });
  const pass = ["content-type", "content-disposition", "x-content-type-options", "cache-control"];
  for (const key of pass) {
    const value = upstream.headers.get(key);
    if (value) out.headers.set(key, value);
  }
  const setCookies =
    typeof upstream.headers.getSetCookie === "function" ? upstream.headers.getSetCookie() : [];
  for (const cookieValue of setCookies) {
    out.headers.append("set-cookie", cookieValue);
  }
  return out;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
