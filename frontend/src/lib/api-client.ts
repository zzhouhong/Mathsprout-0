/**
 * API client for communicating with the FastAPI backend.
 *
 * Usage:
 *   import { api } from "@/lib/api-client";
 *   const children = await api.children.list();
 */

// 空字符串 = 同源相对路径，由 Next.js rewrites 代理到后端
// 本地开发时如需直连后端，设置 NEXT_PUBLIC_API_URL=http://localhost:8000
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// ─── Auth Token Management ──────────────────────────────────────────

let _authToken: string | null = null;

export function setAuthToken(token: string | null) {
  _authToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem("auth_token", token);
    } else {
      localStorage.removeItem("auth_token");
    }
  }
}

export function getAuthToken(): string | null {
  if (_authToken) return _authToken;
  if (typeof window !== "undefined") {
    _authToken = localStorage.getItem("auth_token");
  }
  return _authToken;
}

/**
 * Fetch wrapper that auto-injects the Bearer token.
 * Use this for direct API calls outside of the `api` object.
 */
export async function authFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

// ─── Fetch wrapper ──────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets it with boundary)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    let errBody: Record<string, unknown> = {};
    try {
      errBody = JSON.parse(errText);
    } catch {
      // Not JSON — use raw text as detail
    }
    // Extract the most informative error message from known fields
    const detail =
      (errBody.detail as string) ||
      (errBody.message as string) ||
      (errBody.error as string) ||
      (Array.isArray(errBody.errors) && (errBody.errors as Array<{ msg?: string; message?: string }>)
        .map((e) => e.msg || e.message || "").filter(Boolean).join("; ")) ||
      (errText && errText.slice(0, 200)) ||
      `请求失败 (HTTP ${res.status})`;
    const error = new Error(detail) as Error & { status: number; errors?: unknown[]; rawBody?: string };
    error.status = res.status;
    error.errors = (errBody.validation_errors as unknown[]) || (errBody.errors as unknown[]);
    error.rawBody = errText || undefined;
    throw error;
  }

  return res.json();
}

// ─── Types ──────────────────────────────────────────────────────────

export interface VisionResult {
  worksheet_type: string;
  age_group_hint?: string;
  problems: Array<{
    id: string;
    type: string;
    child_answer?: string;
    correct_answer: string;
    is_correct: boolean;
    confidence: number;
    handwriting_quality: string;
    has_erasure: boolean;
    erasure_pattern: string;
    strategy_indicators?: string;
  }>;
  observations: {
    number_formation_issues: string[];
    attention_indicators: string;
    task_completion_context: string;
    overall_pck_notes?: string;
  };
  dimension_scores_preliminary?: Record<string, unknown>;
  _meta?: {
    model: string;
    usage: { input_tokens: number; output_tokens: number };
  };
}

export interface SubDimensionScore {
  sub_dimension: string;
  name: string;
  score: number;
  max_score: number;
  assessed: boolean;
  correct: number;
  total: number;
  indicator?: string;
  why_this_matters?: string;
}

export interface DimensionAssessment {
  dimension: string;
  display_name: string;
  score: number;
  level: string;
  level_name: string;
  level_emoji: string;
  pck_stage: string;
  sub_skills: Array<{ name: string; score: number; max_score: number }>;
  sub_dimensions: SubDimensionScore[];
  error_patterns: string[];
  age_benchmark_comparison: string;
  age_milestones: string;
  recommendations: string;
  score_details: { correct: number; total: number; strategy_level: string | null };
  reasoning_chain?: { summary: string; steps?: Record<string, unknown> };
}

export interface DimensionProblemDetail {
  id: string;
  type: string;
  type_name: string;
  child_answer: string;
  correct_answer: string;
  is_correct: boolean;
  handwriting_quality: string;
  strategy: string;
}

export interface DimensionProblemGroup {
  display_name: string;
  score: number;
  level: string;
  level_name: string;
  correct_count: number;
  total_count: number;
  problems: DimensionProblemDetail[];
  dimension_analysis: string;
}

export interface AssessmentResult {
  child_name: string;
  age_group: string;
  age_display: string;
  assessment: DimensionAssessment[];
  dimension_problems?: Record<string, DimensionProblemGroup>;
  observations: VisionResult["observations"];
  overall_summary: string;
}

export interface RadarChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    fill: boolean;
    backgroundColor: string;
    borderColor: string;
    pointBackgroundColor: string[];
    pointRadius: number;
  }>;
  age_expectation: {
    label: string;
    data: number[];
    borderColor: string;
    borderDash: number[];
    pointRadius: number;
  };
}

export interface CoreExperienceTarget {
  sub_dimension: string;
  name: string;
  dimension: string;
  dimension_name: string;
  source: "assessed" | "pointed";
  indicator: string;
  why_this_matters: string;
  evidence_examples: string[];
  teaching_tips: string;
  // present only when source === "assessed"
  level?: string;
  level_name?: string;
  level_emoji?: string;
  score?: number;
  correct?: number;
  total?: number;
}

export interface CoreExperienceSupport {
  dimension_name: string;
  source: string;
  strategy: string;
  observation_points: string[];
  materials: string;
  level?: string;
  level_name?: string;
  level_emoji?: string;
  score?: number;
}

export interface TeachingSuggestion {
  current_stage: string;
  level: string;
  recommendations: string;
  next_stage_goal: string;
  classroom_activities: string;
  materials_suggestion: string;
  comparison_to_last?: string | null;
}

export interface ChildMemoryCard {
  remembered: boolean;
  last_seen: string;
  session_count: number;
  summary: string;
  weak_then: Array<{ dimension: string; display_name: string; score: number }>;
  weak_now: Array<{ dimension: string; display_name: string; score: number; level: string }>;
  improving: Array<{
    dimension: string; display_name: string; prior_score: number;
    current_score: number; delta: number;
    resolved_errors: string[]; persisted_errors: string[];
  }>;
  still_struggling: Array<{
    dimension: string; display_name: string; prior_score: number;
    current_score: number; delta: number;
    resolved_errors: string[]; persisted_errors: string[];
  }>;
}

export interface TeacherReport {
  child_name: string;
  age_group: string;
  generated_at: string;
  dimensions: DimensionAssessment[];
  radar_chart_data: RadarChartData;
  pck_analysis: string;
  typical_errors_diagnosis: string[];
  teaching_suggestions: Record<string, TeachingSuggestion>;
  core_experience_analysis: {
    learning_objective: string;
    targets: CoreExperienceTarget[];
    summary: string;
  };
  core_experience_support: Record<string, CoreExperienceSupport>;
  teaching_reflection_questions: string[];
  child_memory_card?: ChildMemoryCard | null;
  overall_summary: string;
  report_type: "teacher";
  report_id?: number;
}

export interface ParentReport {
  child_name: string;
  age_group: string;
  generated_at: string;
  overall_summary: string;
  strengths: Array<{
    area: string;
    emoji: string;
    description: string;
    parent_observation_tip: string;
  }>;
  growing_areas: Array<{
    area: string;
    emoji: string;
    description: string;
    parent_observation_tip: string;
  }>;
  family_activities: Array<{
    title: string;
    materials: string;
    steps: string;
    why: string;
  }>;
  learning_quality_notes: string;
  parent_tips: string;
  parent_memory_card?: { remembered: boolean; session_count: number; summary: string; progressed_areas: string[] } | null;
  report_type: "parent";
  report_id?: number;
}

export interface ProgressEvent {
  step: string;
  status: string;
  message: string;
  progress_pct: number;
  data?: Record<string, unknown>;
}

export interface BatchEvent {
  type: "batch_start" | "file_start" | "file_progress" | "file_complete" | "file_error" | "batch_complete";
  index?: number;
  total?: number;
  filename?: string;
  step?: string;
  message?: string;
  error?: string;
  succeeded?: number;
  failed?: number;
  result?: {
    filename: string;
    assessment: AssessmentResult;
    reports: { teacher: TeacherReport; parent: ParentReport };
  };
  results?: Array<{
    filename: string;
    assessment?: AssessmentResult;
    reports?: { teacher: TeacherReport; parent: ParentReport };
    error?: string;
  }>;
}

export interface ChildRecord {
  id: number;
  name: string;
  age_group: string;
  class_name: string | null;
  birth_date: string | null;
  parent_access_code: string;
  notes: string | null;
  created_at: string;
}

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  role: "teacher" | "admin" | "parent";
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface GrowthTrajectory {
  child_name: string;
  age_group: string;
  has_data: boolean;
  assessment_count: number;
  date_range: { first: string; latest: string };
  trajectories: Array<{
    dimension: string;
    display_name: string;
    has_data: boolean;
    first_score?: number;
    latest_score?: number;
    delta?: number;
    trend?: string;
    trend_emoji?: string;
    trend_text?: string;
    level_sequence?: string;
    chart_points?: Array<{ x: string; y: number; level: string }>;
    assessment_count?: number;
  }>;
  overall_growth_summary: string;
}

interface DemoAnalysisResponse {
  vision: VisionResult;
  assessment: AssessmentResult;
  reports: {
    teacher: TeacherReport;
    parent: ParentReport;
  };
  evaluation_trace?: Record<string, unknown>;
  meta: { model: string; usage: Record<string, number> };
}

// ─── Teacher Confirmation Types ─────────────────────────────────────

/** A problem entry shown for teacher review — child_answer is editable. */
export interface ProblemForReview {
  id: string;
  type: string;
  child_answer: string;
  correct_answer: string;
  is_correct: boolean;
  confidence: number;
  handwriting_quality: string;
  has_erasure: boolean;
  erasure_pattern: string;
  strategy_indicators?: string;
}

export interface ConfirmAnswersRequest {
  child_name: string;
  age_group: string;
  problems: ProblemForReview[];
  observations?: Record<string, unknown>;
  child_id?: number | null;
}

export interface ConfirmAnswersResponse {
  assessment: AssessmentResult;
  reports: {
    teacher: TeacherReport;
    parent: ParentReport;
  };
}

export interface RecognizeResponse {
  vision: VisionResult;
  meta?: Record<string, unknown>;
}

// ─── API object ─────────────────────────────────────────────────────

export const api = {
  // ── Auth ─────────────────────────────────────────────────────────

  auth: {
    async login(email: string, password: string): Promise<LoginResponse> {
      const res = await request<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setAuthToken(res.access_token);
      return res;
    },

    async parentAccess(accessCode: string, childId?: number): Promise<LoginResponse> {
      const res = await request<LoginResponse>("/api/v1/auth/parent", {
        method: "POST",
        body: JSON.stringify({ access_code: accessCode, child_id: childId }),
      });
      setAuthToken(res.access_token);
      return res;
    },

    async me() {
      return request<{ authenticated: boolean; user: Record<string, unknown> }>(
        "/api/v1/auth/me"
      );
    },

    async verify() {
      return request<{ valid: boolean }>("/api/v1/auth/verify");
    },

    logout() {
      setAuthToken(null);
    },

    isAuthenticated(): boolean {
      return getAuthToken() !== null;
    },
  },

  // ── Children ─────────────────────────────────────────────────────

  children: {
    async list(params?: { age_group?: string; class_name?: string; search?: string }) {
      const searchParams = new URLSearchParams();
      if (params?.age_group) searchParams.set("age_group", params.age_group);
      if (params?.class_name) searchParams.set("class_name", params.class_name);
      if (params?.search) searchParams.set("search", params.search);
      const qs = searchParams.toString();
      return request<{ count: number; children: ChildRecord[] }>(
        `/api/v1/children${qs ? `?${qs}` : ""}`
      );
    },

    async get(id: number) {
      return request<ChildRecord>(`/api/v1/children/${id}`);
    },

    async create(data: { name: string; age_group: string; class_name?: string; birth_date?: string; notes?: string }) {
      return request<ChildRecord>("/api/v1/children", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    async update(id: number, data: { name: string; age_group: string; class_name?: string; birth_date?: string; notes?: string }) {
      return request<ChildRecord>(`/api/v1/children/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
    },

    async delete(id: number) {
      return request<{ status: string }>(`/api/v1/children/${id}`, {
        method: "DELETE",
      });
    },

    async stats(id: number) {
      return request<{
        child_id: number;
        name: string;
        worksheet_count: number;
        last_assessment: string | null;
      }>(`/api/v1/children/${id}/stats`);
    },

    async reports(id: number) {
      return request<{
        child: { id: number; name: string; age_group: string; class_name: string | null };
        reports: Array<{
          report_id: number;
          type: string;
          generated_at: string;
          summary: string;
          dimensions: Array<{ name: string; score: number; level: string }>;
        }>;
        recent_assessments: Array<{
          dimension: string;
          score: number;
          level: string;
          assessed_at: string;
        }>;
        worksheet_count: number;
      }>(`/api/v1/children/${id}/reports`);
    },

    async importCSV(file: File) {
      const formData = new FormData();
      formData.append("file", file);
      return request<{
        status: string;
        total: number;
        imported: number;
        skipped: number;
        errors: Array<{ row: string; reason: string }>;
        imported_ids: number[];
      }>("/api/v1/children/import", {
        method: "POST",
        body: formData,
      });
    },

    async classSummary() {
      return request<{
        total_classes: number;
        total_children: number;
        classes: Array<{
          class_name: string;
          total: number;
          age_groups: { small: number; middle: number; large: number };
        }>;
      }>("/api/v1/children/class-summary");
    },
  },

  // ── Worksheets ──────────────────────────────────────────────────

  worksheets: {
    /** B5: fetch auto-recommended difficulty for a child from their assessment history. */
    async recommendDifficulty(childId: number) {
      const params = new URLSearchParams({ child_id: String(childId) });
      return request<{
        child_id: number;
        child_name: string;
        has_memory: boolean;
        last_accuracy: number | null;
        session_count: number;
        level: number;
        reason: string;
        weak_dimensions: Array<{ dimension: string; display_name: string; score: number }>;
      }>(`/api/v1/worksheets/recommend-difficulty?${params}`);
    },

    async uploadAndAnalyze(file: File, ageGroup: string, childName: string, childId?: number) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("age_group", ageGroup);
      formData.append("child_name", childName);
      if (childId != null) formData.append("child_id", String(childId));

      return request<DemoAnalysisResponse>("/api/v1/worksheets/demo", {
        method: "POST",
        body: formData,
      });
    },

    async analyzeWithStream(
      file: File,
      ageGroup: string,
      childName: string,
      onProgress: (event: ProgressEvent) => void,
      onComplete: (data: DemoAnalysisResponse) => void,
      onError: (error: Error) => void
    ): Promise<void> {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("age_group", ageGroup);
      formData.append("child_name", childName);

      const headers: Record<string, string> = {};
      const token = getAuthToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/v1/worksheets/0/analyze-stream`, {
        method: "POST",
        body: formData,
        headers,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "请求失败" }));
        onError(new Error(err.detail || `HTTP ${res.status}`));
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        onError(new Error("浏览器不支持流式读取"));
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const event: ProgressEvent = JSON.parse(line.slice(6));
                onProgress(event);

                if (event.step === "complete" && event.status === "completed") {
                  const fullData = await api.worksheets.uploadAndAnalyze(file, ageGroup, childName);
                  onComplete(fullData);
                }
              } catch {
                // Skip malformed events
              }
            }
          }
        }
      } catch (err) {
        onError(err instanceof Error ? err : new Error("流式读取中断"));
      } finally {
        reader.releaseLock();
      }
    },

    /** Batch analyze multiple worksheets with SSE streaming. */
    async batchAnalyzeStream(
      files: File[],
      ageGroup: string,
      childName: string,
      onBatchEvent: (event: BatchEvent) => void,
      onError: (error: Error) => void
    ): Promise<void> {
      const formData = new FormData();
      for (const f of files) {
        formData.append("files", f);
      }
      formData.append("age_group", ageGroup);
      formData.append("child_name", childName);

      const headers: Record<string, string> = {};
      const token = getAuthToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/v1/worksheets/batch/analyze-stream`, {
        method: "POST",
        body: formData,
        headers,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "请求失败" }));
        onError(new Error(err.detail || `HTTP ${res.status}`));
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) { onError(new Error("浏览器不支持流式读取")); return; }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const event: BatchEvent = JSON.parse(line.slice(6));
                onBatchEvent(event);
              } catch { /* skip malformed */ }
            }
          }
        }
      } catch (err) {
        onError(err instanceof Error ? err : new Error("流式读取中断"));
      } finally {
        reader.releaseLock();
      }
    },

    /** Phase 1: Recognize only — returns vision result for teacher review. */
    async recognize(file: File, ageGroup: string, childName: string) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("age_group", ageGroup);
      formData.append("child_name", childName);
      return request<RecognizeResponse>("/api/v1/worksheets/recognize", {
        method: "POST",
        body: formData,
      });
    },

    /** Phase 2: Confirm corrected answers — runs assessment + reports. */
    async confirm(data: ConfirmAnswersRequest) {
      return request<ConfirmAnswersResponse>("/api/v1/worksheets/confirm", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },

    /** Fetch evaluation trace for a real analysis. */
    async traceByAnalysis(analysisId: number) {
      return request<any>(`/api/v1/analysis/${analysisId}/evaluation-trace`);
    },

    /** Fetch demo evaluation trace. */
    async traceDemo(ageGroup: string, childName: string) {
      const params = new URLSearchParams({ age_group: ageGroup, child_name: childName });
      return request<any>(`/api/v1/analysis/evaluation-trace?${params}`);
    },
  },

  // ── Analysis (Demo) ──────────────────────────────────────────────

  analysis: {
    async demo(ageGroup: string, childName: string) {
      const params = new URLSearchParams({ age_group: ageGroup, child_name: childName });
      return request<AssessmentResult>(`/api/v1/analysis/demo-assessment?${params}`);
    },
  },

  // ── Dashboard ─────────────────────────────────────────────────────

  dashboard: {
    async childTrajectory(childId: number) {
      return request<{
        child_name: string;
        age_group: string;
        class_name: string | null;
        dimensions: Record<string, Array<{ date: string | null; score: number; level: string; pck_stage: string | null }>>;
        chart_data: Array<Record<string, number | string>>;
        latest_scores: Record<string, { date: string | null; score: number; level: string; pck_stage: string | null }>;
        trends: Record<string, string>;
        error_evolution: Array<{
          error: string; first_seen: string; last_seen: string;
          count: number; dates: string[]; status: "resolved" | "recurring" | "new";
        }>;
        assessment_count: number;
      }>(`/api/v1/dashboard/child/${childId}/trajectory`);
    },

    async classOverview(className: string) {
      return request<{
        class_name: string;
        total_children: number;
        dimensions: Array<{
          dimension: string;
          average_score: number;
          level_distribution: Record<string, number>;
        }>;
        top_strengths: string[];
        common_needs: string[];
      }>(`/api/v1/dashboard/class/${encodeURIComponent(className)}/overview`);
    },

    async semesterCompare(className: string) {
      return request<{
        comparison: Array<{
          dimension: string;
          current_semester: number;
          previous_semester: number;
          delta: number;
          trend: string;
        }>;
      }>(`/api/v1/dashboard/class/${encodeURIComponent(className)}/semester-compare`);
    },

    exportClassURL(className: string) {
      return `/api/v1/dashboard/export/class/${encodeURIComponent(className)}`;
    },

    exportChildURL(childId: number) {
      return `/api/v1/dashboard/export/child/${childId}`;
    },
  },

  // ── Reports ─────────────────────────────────────────────────────

  reports: {
    async generateTeacher(assessmentData: Record<string, unknown>, childName: string, ageGroup: string) {
      const params = new URLSearchParams({ child_name: childName, age_group: ageGroup });
      return request<TeacherReport>(`/api/v1/reports/generate/teacher?${params}`, {
        method: "POST",
        body: JSON.stringify(assessmentData),
      });
    },

    async generateParent(assessmentData: Record<string, unknown>, childName: string, ageGroup: string) {
      const params = new URLSearchParams({ child_name: childName, age_group: ageGroup });
      return request<ParentReport>(`/api/v1/reports/generate/parent?${params}`, {
        method: "POST",
        body: JSON.stringify(assessmentData),
      });
    },

    async getTeacher(id: number) {
      return request<TeacherReport>(`/api/v1/reports/teacher/${id}`);
    },

    async getParent(id: number) {
      return request<ParentReport>(`/api/v1/reports/parent/${id}`);
    },

    async getHistory(childName: string, type?: "teacher" | "parent") {
      const params = new URLSearchParams();
      if (type) params.set("report_type", type);
      const qs = params.toString();
      return request<{ child_name: string; count: number; reports: Array<Record<string, unknown>> }>(
        `/api/v1/reports/history/${childName}${qs ? `?${qs}` : ""}`
      );
    },

    async demoTeacher(ageGroup = "middle", childName = "小明") {
      const params = new URLSearchParams({ age_group: ageGroup, child_name: childName });
      return request<TeacherReport>(`/api/v1/reports/demo/teacher?${params}`);
    },

    async demoParent(ageGroup = "middle", childName = "小明") {
      const params = new URLSearchParams({ age_group: ageGroup, child_name: childName });
      return request<ParentReport>(`/api/v1/reports/demo/parent?${params}`);
    },

    /** Download a report as PDF. Triggers browser download. */
    async downloadPdf(reportId: number, type: "teacher" | "parent"): Promise<void> {
      const url = `${API_BASE}/api/v1/reports/${reportId}/pdf/${type}`;
      const headers: Record<string, string> = {};
      if (_authToken) {
        headers["Authorization"] = `Bearer ${_authToken}`;
      }
      const res = await fetch(url, { headers });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "PDF 下载失败" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") || "";
      const filenameMatch = disposition.match(/filename="?([^";\n]+)"?/);
      const filename = filenameMatch?.[1] || `report_${reportId}.pdf`;

      // Trigger browser download
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    },
  },

  // ── Tracking ────────────────────────────────────────────────────

  tracking: {
    async trajectory(childName: string, assessments: AssessmentResult[], ageGroup: string) {
      const params = new URLSearchParams({ age_group: ageGroup });
      return request<GrowthTrajectory>(`/api/v1/tracking/trajectory/${childName}?${params}`, {
        method: "POST",
        body: JSON.stringify(assessments),
      });
    },

    async compare(current: AssessmentResult, previous: AssessmentResult | null, childName: string) {
      return request<Record<string, unknown>>(`/api/v1/tracking/compare/${childName}`, {
        method: "POST",
        body: JSON.stringify({ current, previous }),
      });
    },

    async classAnalysis(childrenData: AssessmentResult[], className = "本班") {
      const params = new URLSearchParams({ class_name: className });
      return request<Record<string, unknown>>(`/api/v1/tracking/class-analysis?${params}`, {
        method: "POST",
        body: JSON.stringify(childrenData),
      });
    },

    async demoTrajectory(ageGroup = "middle", childName = "小明") {
      const params = new URLSearchParams({ age_group: ageGroup, child_name: childName });
      return request<GrowthTrajectory>(`/api/v1/tracking/demo/trajectory?${params}`);
    },
  },

  // ── Health ──────────────────────────────────────────────────────

  async health() {
    return request<{ status: string; version: string; database: string }>("/api/health");
  },

  async stats() {
    return request<Record<string, unknown>>("/api/stats");
  },
};

// ─── Legacy exports (backward compatibility) ───────────────────────

export const uploadAndAnalyze = api.worksheets.uploadAndAnalyze;
export const analyzeWithProgress = api.worksheets.analyzeWithStream;
export const getDemoAssessment = api.analysis.demo;
export const getDemoTeacherReport = api.reports.demoTeacher;
export const getDemoParentReport = api.reports.demoParent;
export const healthCheck = api.health;
