import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  default: "bg-slate-100 text-slate-700",
  success: "bg-emerald-50 text-emerald-800",
  warning: "bg-amber-50 text-amber-800",
  danger: "bg-rose-50 text-rose-800",
  info: "bg-teal-50 text-teal-800",
};

export function Badge({
  className,
  tone = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: keyof typeof tones }) {
  return (
    <span
      className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", tones[tone], className)}
      {...props}
    />
  );
}

export function statusTone(status: string): keyof typeof tones {
  if (["published", "selected", "verified", "processed", "eligible"].includes(status)) return "success";
  if (["rejected", "failed", "ineligible", "closed"].includes(status)) return "danger";
  if (["draft", "pending", "under_review", "processing", "unknown", "no_text"].includes(status)) return "warning";
  if (["shortlisted", "interview_scheduled", "applied"].includes(status)) return "info";
  return "default";
}
