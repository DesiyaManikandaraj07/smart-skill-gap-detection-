const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("ssg_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseError(res: Response): Promise<string> {
  const err = await res.json().catch(() => ({ detail: res.statusText }));
  const detail = err.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(", ");
  }
  return "Request failed";
}

export type User = {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  is_active: boolean;
};

export type RoleSummary = {
  id: string;
  title: string;
  category: string;
  skill_count: number;
  summary: string;
  min_experience_years?: number | null;
  min_cgpa?: number | null;
};

export type SampleJD = {
  id: string;
  title: string;
  category: string;
  description: string;
  required_skills: string[];
  min_experience_years?: number | null;
  min_cgpa?: number | null;
  degree_required?: boolean;
  locations?: string[];
  experience_level?: string | null;
  company?: string | null;
  source?: string | null;
  source_url?: string | null;
};

export type JobFeedItem = {
  id: string;
  title: string;
  company: string;
  category: string;
  experience_level: string;
  summary: string;
  description: string;
  required_skills: string[];
  min_experience_years?: number | null;
  min_cgpa?: number | null;
  degree_required?: boolean;
  locations: string[];
  source: string;
  source_url: string;
  posted_at: string;
  salary: string;
};

export type SkillImpact = {
  skill: string;
  impact_pct: number;
  demand_rank: number;
  demand_frequency: number;
};

export type RoadmapItem = {
  skill: string;
  weeks: number;
  projects: string[];
  courses: string[];
  certs: string[];
  rationale: string;
};

export type ExplanationItem = {
  feature: string;
  contribution: number;
  direction: string;
};

export type GateResult = {
  key: string;
  label: string;
  passed: boolean;
  required: string;
  observed: string;
  severity: string;
  advice: string;
};

export type CoachingSummary = {
  headline: string;
  verdict: string;
  strengths: string[];
  improvements: string[];
  critical_blockers: string[];
  effective_note: string;
  gates: GateResult[];
  eligible: boolean;
};

export type AnalyzeResponse = {
  id?: number | null;
  candidate_name: string;
  role_id?: string | null;
  role_title?: string | null;
  selection_likelihood_pct: number;
  effective_selection_pct: number;
  confidence: number;
  eligible: boolean;
  matched_skills: string[];
  missing_skills: string[];
  weak_skills: string[];
  required_skills: string[];
  learn_next: SkillImpact[];
  roadmap: RoadmapItem[];
  explanations: ExplanationItem[];
  profile: {
    skills: string[];
    education: string[];
    projects: string[];
    internships: string[];
    certifications: string[];
    experience_years: number;
    cgpa?: number | null;
    locations?: string[];
    raw_text_chars: number;
  };
  job_skills: string[];
  summary?: CoachingSummary | null;
  disclaimer: string;
};

export type WhatIfResponse = {
  selection_likelihood_pct: number;
  effective_selection_pct: number;
  previous_pct?: number | null;
  delta_pct: number;
  matched_skills: string[];
  missing_skills: string[];
  explanations: ExplanationItem[];
  note?: string;
};

export type AdminStats = {
  users_total: number;
  analyses_total: number;
  analyses_today: number;
  avg_selection_pct: number;
  ineligible_rate: number;
  model_name: string;
  model_metrics: Record<string, unknown>;
};

export async function register(email: string, password: string, full_name: string) {
  const res = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ access_token: string; user: User }>;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{ access_token: string; user: User }>;
}

export async function fetchMe(): Promise<User> {
  const res = await fetch(`${API_URL}/api/v1/auth/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchRoles(): Promise<RoleSummary[]> {
  const res = await fetch(`${API_URL}/api/v1/roles`);
  if (!res.ok) throw new Error("Failed to load roles");
  return res.json();
}

export async function fetchJobFeed(opts?: {
  level?: string;
  source?: string;
  refresh?: boolean;
}): Promise<JobFeedItem[]> {
  const params = new URLSearchParams();
  params.set("level", opts?.level || "all");
  params.set("source", opts?.source || "all");
  if (opts?.refresh) params.set("refresh", "true");
  const res = await fetch(`${API_URL}/api/v1/jobs/feed?${params.toString()}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchJobDetail(jobId: string): Promise<SampleJD> {
  const res = await fetch(`${API_URL}/api/v1/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchSampleJd(roleId: string): Promise<SampleJD> {
  const res = await fetch(`${API_URL}/api/v1/roles/${roleId}`);
  if (!res.ok) throw new Error("Failed to load sample JD");
  return res.json();
}

export async function analyzeResume(form: FormData): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/api/v1/analyze`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function runWhatIf(body: Record<string, unknown>): Promise<WhatIfResponse> {
  const res = await fetch(`${API_URL}/api/v1/what-if`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchAdminStats(): Promise<AdminStats> {
  const res = await fetch(`${API_URL}/api/v1/admin/stats`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchAdminUsers(): Promise<User[]> {
  const res = await fetch(`${API_URL}/api/v1/admin/users`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchAdminAnalyses() {
  const res = await fetch(`${API_URL}/api/v1/admin/analyses`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function toggleUserActive(userId: number): Promise<User> {
  const res = await fetch(`${API_URL}/api/v1/admin/users/${userId}/toggle-active`, {
    method: "PATCH",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
