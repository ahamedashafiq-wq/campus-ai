export type Role = "student" | "recruiter" | "admin";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  email_verified: boolean;
};

export type Job = {
  id: string;
  company_id: string;
  company_name: string;
  title: string;
  description: string;
  responsibilities?: string | null;
  location?: string | null;
  employment_type?: string | null;
  min_cgpa?: number | null;
  min_graduation_year?: number | null;
  max_graduation_year?: number | null;
  min_experience_years?: number | null;
  education_requirement?: string | null;
  application_deadline?: string | null;
  status: "draft" | "published" | "closed" | "archived";
  required_skills: string[];
  preferred_skills: string[];
  created_at: string;
  applicant_count?: number;
};

export type MatchResult = {
  overall_score: number;
  required_coverage: number;
  preferred_coverage: number;
  semantic_score: number;
  evidence_score: number;
  matching_method: string;
  semantic_note?: string;
  matched_required_skills: string[];
  matched_preferred_skills: string[];
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  relevant_resume_evidence: string[];
  skills_needing_stronger_evidence: string[];
  unknown_requirements: string[];
  eligibility: string;
  eligibility_reasons: string[];
  improvement_recommendations: string[];
  disclaimer?: string;
  gap?: {
    missing_required_skills: string[];
    missing_preferred_skills: string[];
    skills_needing_stronger_project_evidence: string[];
    unknown_requirements: string[];
    learning_priorities: string[];
    verified_vs_advice: { verified: string; advice: string };
  };
};

export type Application = {
  id: string;
  job_id: string;
  student_id: string;
  status: string;
  cover_note?: string | null;
  submitted_at: string;
  job_title?: string | null;
  company_name?: string | null;
  student_name?: string | null;
  history?: { from_status: string | null; to_status: string; note?: string | null; created_at: string }[];
  match?: MatchResult | null;
};

export type ApiError = { error?: string; code?: string; detail?: string };
