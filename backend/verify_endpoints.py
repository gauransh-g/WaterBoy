"""
Verification script for all WaterBoy backend APIs and Evaluation Benchmark.
"""

import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.rag.vector_store import FaissVectorStore
from app.rag.pipeline import RagPipeline
from app.api.routes_chat import set_pipeline
from app.data.groundwater_db import GroundwaterDatabase
from app.evaluation.benchmark import BenchmarkEvaluator, GOLD_STANDARD_TEST_CASES
from app.models.schemas import ChatRequest, SearchRequest

print("=" * 70)
print("WATERBOY GROUNDWATER INTELLIGENCE PLATFORM - ENDPOINT VERIFICATION")
print("=" * 70)

# 1. Load Vector Store
print("\n[1/5] Loading Persistent Vector Store...")
store = FaissVectorStore.load(Path(__file__).parent / "data_store" / "vector_index")
print(f"-> Total Indexed Knowledge Chunks: {store.total_count}")

# 2. Initialize RAG Pipeline
print("\n[2/5] Initializing RAG Orchestration Pipeline...")
pipeline = RagPipeline(vector_store=store)
set_pipeline(pipeline)
print("-> RAG Pipeline successfully initialized.")

# 3. Test Structured Database
print("\n[3/5] Verifying CGWB Structured Groundwater Database...")
db = GroundwaterDatabase.get_instance()
overview = db.get_national_overview()
print(f"-> Assessment Year: {overview.assessment_year}")
print(f"-> Total Assessment Units: {overview.total_assessment_units}")
print(f"-> Total States Covered: {overview.total_states_covered}")
print(f"-> Average Stage of Extraction: {overview.national_stage_of_extraction_avg}%")
print(f"-> Category Breakdown: {overview.category_breakdown}")
print(f"-> Top Over-Exploited States: {overview.top_overexploited_states}")

state_summaries = db.get_state_summaries()
print(f"-> Retrieved summaries for {len(state_summaries)} states.")
for s in state_summaries[:4]:
    print(f"   * {s.state}: {s.total_units} units, avg extraction: {s.avg_stage_of_extraction}%, {s.over_exploited_units} over-exploited")

# 4. Test RAG Chat and Search Queries
print("\n[4/5] Testing RAG Chat and Search Queries...")

# Query 1: Conceptual / Methodology
q1 = "What is the formula to calculate the Stage of Ground Water Extraction according to CGWB GEC-2015?"
res1 = pipeline.answer_query(ChatRequest(query=q1, top_k=3))
print(f"\n--- Inquiry 1: {q1} ---")
print(f"Confidence: {res1.confidence_score} | Latency: {res1.execution_time_ms} ms | Model: {res1.model_used}")
print(f"Answer:\n{res1.answer}")
print(f"Citations ({len(res1.citations)}):")
for c in res1.citations:
    print(f"  [{c.relevance_score}] {c.title} ({c.source_doc})")

# Query 2: Policy Scheme
q2 = "Which states are covered under the Atal Bhujal Yojana and what are its objectives?"
res2 = pipeline.answer_query(ChatRequest(query=q2, top_k=3))
print(f"\n--- Inquiry 2: {q2} ---")
print(f"Confidence: {res2.confidence_score} | Latency: {res2.execution_time_ms} ms")
print(f"Answer:\n{res2.answer}")
print(f"Citations ({len(res2.citations)}):")
for c in res2.citations:
    print(f"  [{c.relevance_score}] {c.title} ({c.source_doc})")

# Query 3: State Ground Truth Query
q3 = "What is the groundwater extraction status in Delhi and what category are the assessment units?"
res3 = pipeline.answer_query(ChatRequest(query=q3, top_k=3))
print(f"\n--- Inquiry 3: {q3} ---")
print(f"Confidence: {res3.confidence_score} | Latency: {res3.execution_time_ms} ms")
print(f"Answer:\n{res3.answer}")

# Query 4: Out-of-Scope / Unsupported Refusal Query
q4 = "What was the stock price of Apple on NASDAQ yesterday?"
res4 = pipeline.answer_query(ChatRequest(query=q4, top_k=3))
print(f"\n--- Inquiry 4 (Out of scope refusal): {q4} ---")
print(f"Has Evidence: {res4.has_sufficient_evidence} | Confidence: {res4.confidence_score}")
print(f"Refusal Response: {res4.answer}")

# 5. Execute Full Evaluation Benchmark
print("\n[5/5] Running Gold-Standard Groundwater Benchmark Suite (10 Test Cases)...")
evaluator = BenchmarkEvaluator(pipeline)
bench = evaluator.run_benchmark(GOLD_STANDARD_TEST_CASES)

print("\n" + "=" * 70)
print("BENCHMARK EVALUATION RESULTS")
print("=" * 70)
print(f"Total Tests Run: {bench.total_tests}")
print(f"Passed Tests: {bench.passed_tests} / {bench.total_tests} ({(bench.passed_tests / bench.total_tests) * 100:.1f}%)")
print(f"Retrieval Precision@k: {bench.retrieval_precision_at_k * 100:.1f}%")
print(f"Retrieval Recall@k: {bench.retrieval_recall_at_k * 100:.1f}%")
print(f"Faithfulness Score: {bench.faithfulness_score_avg * 100:.1f}%")
print(f"Citation Rate: {bench.citation_rate * 100:.1f}%")
print(f"Unsupported Query Refusal Accuracy: {bench.unsupported_query_refusal_accuracy * 100:.1f}%")
print(f"Average Response Latency: {bench.avg_latency_ms:.2f} ms")
print("=" * 70)

for r in bench.test_results:
    print(f"[{r.status}] {r.question[:65]}... (Latency: {r.latency_ms:.1f}ms, Faithfulness: {r.faithfulness_score})")

# Save benchmark results to JSON
results_path = Path(__file__).parent / "data_store" / "benchmark_results.json"
results_path.parent.mkdir(parents=True, exist_ok=True)
with open(results_path, "w", encoding="utf-8") as f:
    json.dump(bench.model_dump(), f, indent=2)

print(f"\nSaved benchmark results to {results_path}")

