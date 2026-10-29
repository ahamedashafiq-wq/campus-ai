import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value?: string | null) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
}

export function scoreColor(score: number) {
  if (score >= 75) return "text-emerald-700";
  if (score >= 50) return "text-amber-700";
  return "text-rose-700";
}
