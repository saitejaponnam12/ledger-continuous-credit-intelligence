/**
 * LEDGER — API Client
 * Typed axios wrapper with JWT auth, error handling.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Inject JWT token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ledger_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 — redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ledger_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// ── Typed API calls ──────────────────────────────────────────

export interface LoginResponse {
  access_token: string
  user_id: string
  display_name: string
  role: string
}

export interface Application {
  application_id: string
  status: string
  customer: {
    id: string
    display_name: string
    persona_tag: string | null
    age: number | null
    city: string | null
  }
  latest_risk_score: RiskScore | null
  latest_decision: Decision | null
  created_at: string
  updated_at: string
}

export interface RiskScore {
  risk_probability: number
  risk_band: string
  confidence: number
  computed_at: string
  model_version: string
}

export interface Decision {
  pathway: string
  exposure_limit: number | null
  monitoring_period_days: number | null
  rationale_summary: string
  decided_at: string
}

export interface TrajectoryPoint {
  computed_at: string
  risk_probability: number
  confidence: number
  risk_band: string
  triggered_by: string
  financial_twin: {
    financial_stability: number
    income_reliability: number
    payment_discipline: number
    liquidity: number
    volatility: number
  }
}

export interface PathwayDecision {
  pathway: string
  label: string
  exposure_limit: number | null
  monitoring_period_days: number | null
  confidence: number
  rationale_summary: string
  uncertainty_note: string
  evidence_required: string | null
  human_review_required: boolean
  policy_version: string
  model_version: string
  decided_at: string
  color: string
  primary_risk_drivers: string[]
  primary_strength_drivers: string[]
  risk_probability: number
}

export interface ShapEntry {
  feature: string
  label: string
  contribution: number
}

export interface AnalyzeResponse {
  application_id: string
  risk_probability: number
  risk_band: string
  confidence: number
  pathway: PathwayDecision
  financial_twin: {
    financial_stability: number
    income_reliability: number
    payment_discipline: number
    liquidity: number
    volatility: number
    exposure_capacity: number
  }
  shap_ranked: {
    positive: ShapEntry[]
    negative: ShapEntry[]
  }
  next_best_evidence: Array<{
    evidence: string
    rationale: string
    expected_uncertainty_reduction: number
    estimation_method: string
  }>
  feature_warnings: string[]
}

export interface CopilotResponse {
  response: string
  citations: Array<{ chunk_id: string; title: string; similarity: number }>
  tools_called: string[]
  llm_provider: string
  is_mock: boolean
  latency_ms: number
  interaction_id: string
  disclaimer: string
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
}

export const applicationsApi = {
  create: (data: { customer_name: string; customer_age?: number; customer_city?: string; consent_given: boolean }) =>
    api.post<{ application_id: string }>('/applications', data),
  get: (id: string) => api.get<Application>(`/applications/${id}`),
  analyze: (id: string, overrides?: Record<string, number>) =>
    api.post<AnalyzeResponse>(`/applications/${id}/analyze`, { override_features: overrides }),
  getRiskTrajectory: (id: string) => api.get(`/applications/${id}/risk`),
  getExplanation: (id: string) => api.get(`/applications/${id}/explanation`),
  getNextBestEvidence: (id: string) => api.get(`/applications/${id}/next-best-evidence`),
  counterfactual: (id: string, overrides: Record<string, number>) =>
    api.post(`/applications/${id}/counterfactual`, { feature_overrides: overrides }),
  getAudit: (id: string) => api.get(`/applications/${id}/audit`),
  getEvidenceNetwork: (id: string) => api.get(`/applications/${id}/evidence-network`),
  getAnomalySignals: (id: string) => api.get(`/applications/${id}/anomaly-signals`),
  uploadDocument: (id: string, formData?: FormData, sampleName?: string) =>
    api.post(`/applications/${id}/documents/upload${sampleName ? `?sample_name=${encodeURIComponent(sampleName)}` : ''}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getDocuments: (id: string) => api.get(`/applications/${id}/documents`),
  incorporateDocument: (id: string, documentId: string) =>
    api.post(`/applications/${id}/documents/${documentId}/incorporate`),
}

export const eventsApi = {
  simulate: (data: {
    customer_id: string
    application_id: string
    event_type: string
    amount?: number
    category?: string
    merchant?: string
    direction?: string
    description?: string
  }) => api.post('/events/simulate', data),
}

export const copilotApi = {
  query: (query: string, application_id?: string) =>
    api.post<CopilotResponse>('/copilot/query', { query, application_id }),
}

export const demoApi = {
  scenarios: () => api.get('/demo/scenarios'),
  reset: (scenario: string) => api.post(`/demo/reset/${scenario}`),
  status: () => api.get('/demo/status'),
  seedAll: () => api.post('/demo/seed-all'),
}
