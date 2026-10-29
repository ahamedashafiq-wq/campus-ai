import Link from "next/link";
import { GraduationCap } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2 font-semibold">
          <GraduationCap className="h-6 w-6 text-teal-400" />
          CampusMatch AI
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link href="/register">Create account</Link>
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-20">
        <p className="text-sm uppercase tracking-wide text-teal-300">Campus placement platform</p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight md:text-5xl">
          Match students to jobs using real resumes, real job requirements, and explainable scores.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-slate-300">
          CampusMatch AI extracts skills from uploaded PDFs, compares them with published roles, and stores every
          application in PostgreSQL. Recruiters review evidence. Administrators oversee placement activity. Scores are
          heuristics, not hiring decisions.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/register">Register as a student</Link>
          </Button>
          <Button asChild size="lg" variant="secondary">
            <Link href="/register?role=recruiter">Register as a recruiter</Link>
          </Button>
        </div>
        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {[
            {
              title: "Real resume processing",
              body: "PDFs are stored privately, validated, and extracted with PyMuPDF. Scanned files are reported clearly.",
            },
            {
              title: "Explainable matching",
              body: "Required skills, preferred skills, semantic similarity, and project evidence are scored separately.",
            },
            {
              title: "Recruitment workflow",
              body: "Applications, interviews, and status history persist in the database with role-based access control.",
            },
          ].map((item) => (
            <div key={item.title} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <h2 className="font-semibold">{item.title}</h2>
              <p className="mt-2 text-sm text-slate-400">{item.body}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
