import type { MatchResult } from "@/lib/types";
import { scoreColor } from "@/lib/utils";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export function MatchPanel({ match }: { match: MatchResult }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Match score</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className={`text-3xl font-semibold ${scoreColor(match.overall_score)}`}>{match.overall_score.toFixed(1)}</p>
          <p>
            Method: <Badge>{match.matching_method}</Badge>
          </p>
          {match.semantic_note ? <p className="text-slate-500">{match.semantic_note}</p> : null}
          <ul className="grid grid-cols-2 gap-2 text-slate-700">
            <li>Required coverage: {match.required_coverage}</li>
            <li>Preferred coverage: {match.preferred_coverage}</li>
            <li>Semantic: {match.semantic_score}</li>
            <li>Evidence: {match.evidence_score}</li>
          </ul>
          <p>
            Eligibility: <Badge>{match.eligibility}</Badge>
          </p>
          <ul className="list-disc pl-5 text-slate-600">
            {match.eligibility_reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          {match.disclaimer ? <p className="text-xs text-slate-500">{match.disclaimer}</p> : null}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Skill gap</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <SkillList label="Matched required" items={match.matched_required_skills} />
          <SkillList label="Missing required" items={match.missing_required_skills} />
          <SkillList label="Matched preferred" items={match.matched_preferred_skills} />
          <SkillList label="Missing preferred" items={match.missing_preferred_skills} />
          <SkillList label="Evidence found" items={match.relevant_resume_evidence} />
          <SkillList label="Needs stronger evidence" items={match.skills_needing_stronger_evidence} />
          <SkillList label="Unknown requirements" items={match.unknown_requirements} />
        </CardContent>
      </Card>
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Learning priorities</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-2 text-xs text-slate-500">
            {match.gap?.verified_vs_advice.verified} {match.gap?.verified_vs_advice.advice}
          </p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {(match.gap?.learning_priorities || match.improvement_recommendations).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function SkillList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="font-medium text-slate-800">{label}</p>
      {items.length === 0 ? (
        <p className="text-slate-500">None</p>
      ) : (
        <div className="mt-1 flex flex-wrap gap-1">
          {items.map((s) => (
            <Badge key={s}>{s}</Badge>
          ))}
        </div>
      )}
    </div>
  );
}
