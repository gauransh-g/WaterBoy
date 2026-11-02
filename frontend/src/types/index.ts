export interface Citation {
  chunk_id: string;
  source_doc: string;
  title: string;
  section?: string;
  state?: string;
  district?: string;
  year?: string;
  relevance_score: number;
  excerpt: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "bot";
  text: string;
  citations?: Citation[];
  confidenceScore?: number;
  hasSufficientEvidence?: boolean;
  intent?: string;
  latencyMs?: number;
  timestamp: string;
}

export interface ChatResponse {
  query: string;
  answer: string;
  citations: Citation[];
  confidence_score: number;
  has_sufficient_evidence: boolean;
  query_intent: string;
  execution_time_ms: number;
  model_used: string;
  state_context?: string;
  district_context?: string;
}

export interface StateSummary {
  state: string;
  total_units: number;
  safe_units: number;
  semi_critical_units: number;
  critical_units: number;
  over_exploited_units: number;
  saline_units: number;
  avg_stage_of_extraction: number;
  total_annual_recharge_ham: number;
  total_annual_extraction_ham: number;
}

export interface GroundwaterOverview {
  assessment_year: string;
  total_states_covered: number;
  total_assessment_units: number;
  national_stage_of_extraction_avg: number;
  category_breakdown: Record<string, number>;
  top_overexploited_states: Array<{ state: string; over_exploited_units: number }>;
  dataset_source: string;
}

export interface YearlyTrend {
  year: string;
  total_units: number;
  avg_stage_of_extraction: number;
  total_recharge_ham: number;
  total_extraction_ham: number;
  safe_units: number;
  over_exploited_units: number;
}

export interface AssessmentUnitData {
  state: string;
  district: string;
  location_name: string;
  category: string;
  stage_of_extraction: number;
  total_recharge_ham: number;
  total_extraction_ham: number;
  availability_for_future_use_ham: number;
  rainfall_mm?: number;
  geology?: string;
  water_table_trend?: string;
}

export interface TestCaseResult {
  question: string;
  expected_topics: string[];
  retrieved_chunk_ids: string[];
  retrieval_hit: boolean;
  faithfulness_score: number;
  has_citations: boolean;
  refusal_correctness: boolean;
  latency_ms: number;
  status: string;
}

export interface BenchmarkSummary {
  total_tests: number;
  passed_tests: number;
  retrieval_precision_at_k: number;
  retrieval_recall_at_k: number;
  faithfulness_score_avg: number;
  citation_rate: number;
  unsupported_query_refusal_accuracy: number;
  avg_latency_ms: number;
  test_results: TestCaseResult[];
}

export interface BackendHealth {
  status: string;
  version: string;
  embedding_model: string;
  total_indexed_chunks: number;
  total_assessment_units: number;
  states_covered: number;
}
