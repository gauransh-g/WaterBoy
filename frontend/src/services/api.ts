import {
  ChatResponse,
  GroundwaterOverview,
  StateSummary,
  AssessmentUnitData,
  BenchmarkSummary,
  BackendHealth,
  YearlyTrend
} from "../types";

const API_BASE = "http://127.0.0.1:8000/api";

export async function fetchHealth(): Promise<BackendHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Backend unhealthy");
  return res.json();
}

export async function sendChatQuery(
  query: string,
  topK: number = 4,
  filterState?: string,
  filterCategory?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      top_k: topK,
      filter_state: filterState || undefined,
      filter_category: filterCategory || undefined
    })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to process chat query");
  }
  return res.json();
}

export async function fetchGroundwaterOverview(year?: string): Promise<GroundwaterOverview> {
  const url = year && year !== "all" 
    ? `${API_BASE}/groundwater/summary?year=${encodeURIComponent(year)}`
    : `${API_BASE}/groundwater/summary`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch groundwater overview");
  return res.json();
}

export async function fetchStateSummaries(year?: string): Promise<StateSummary[]> {
  const url = year && year !== "all"
    ? `${API_BASE}/groundwater/states?year=${encodeURIComponent(year)}`
    : `${API_BASE}/groundwater/states`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch state summaries");
  return res.json();
}

export async function fetchGroundwaterTrends(state?: string): Promise<YearlyTrend[]> {
  const url = state && state.toLowerCase() !== "all states"
    ? `${API_BASE}/groundwater/trends?state=${encodeURIComponent(state)}`
    : `${API_BASE}/groundwater/trends`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch groundwater multi-year trends");
  return res.json();
}

export async function fetchDistrictUnits(
  state: string,
  district: string,
  year?: string
): Promise<AssessmentUnitData[]> {
  let url = `${API_BASE}/groundwater/district/${encodeURIComponent(state)}/${encodeURIComponent(district)}`;
  if (year && year !== "all") {
    url += `?year=${encodeURIComponent(year)}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch district units");
  return res.json();
}

export async function runEvaluationBenchmark(): Promise<BenchmarkSummary> {
  const res = await fetch(`${API_BASE}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  if (!res.ok) throw new Error("Failed to run evaluation benchmark");
  return res.json();
}
