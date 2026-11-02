"""
Reproducible Evaluation Benchmark for WaterBoy.
Evaluates Precision@k, Recall@k, Faithfulness, Citation Correctness,
Latency, and Unsupported-Question Refusal Accuracy.
"""

import time
import logging
from typing import List, Dict, Any
from app.rag.pipeline import RagPipeline
from app.models.schemas import ChatRequest, BenchmarkSummary, TestCaseResult

logger = logging.getLogger("waterboy.benchmark")

# 10 Grounded Benchmark Test Cases
GOLD_STANDARD_TEST_CASES = [
    {
        "id": "TC-01",
        "question": "What is the formula to calculate the Stage of Ground Water Extraction according to CGWB GEC-2015?",
        "expected_topics": ["total annual ground water draft", "extractable", "resource", "100", "formula"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "01_cgwb_resource_estimation_methodology.md"
    },
    {
        "id": "TC-02",
        "question": "What are the criteria for an assessment unit to be categorized as Over-Exploited by CGWB?",
        "expected_topics": ["over-exploited", "100", "decline", "extraction"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "01_cgwb_resource_estimation_methodology.md"
    },
    {
        "id": "TC-03",
        "question": "Which states are covered under the Atal Bhujal Yojana and what is its funding structure?",
        "expected_topics": ["gujarat", "haryana", "world bank", "central sector"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "02_atal_bhujal_yojana_guidelines.md"
    },
    {
        "id": "TC-04",
        "question": "What artificial recharge structures are recommended for hard rock basaltic and crystalline terrains?",
        "expected_topics": ["check dam", "percolation tank", "subsurface dyke", "recharge shaft"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "03_artificial_recharge_and_rainwater_harvesting.md"
    },
    {
        "id": "TC-05",
        "question": "What is the BIS IS 10500:2012 acceptable limit for Arsenic and Fluoride in drinking water?",
        "expected_topics": ["0.01", "10 ppb", "1.0", "1.5", "arsenic", "fluoride"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "04_groundwater_quality_and_contamination_standards.md"
    },
    {
        "id": "TC-06",
        "question": "What is the India Ground Water Resource Estimation System (INGRES) and who co-developed it?",
        "expected_topics": ["ingres", "cgwb", "iit hyderabad", "gec-2015", "web-gis", "dwlr"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "05_ingres_portal_and_digital_groundwater_monitoring.md"
    },
    {
        "id": "TC-07",
        "question": "What is the groundwater extraction status and category in Delhi assessment units?",
        "expected_topics": ["delhi", "stage", "extraction", "cgwb"],
        "expected_state": "Delhi",
        "is_supported": True,
        "expected_citation_doc": "CGWB"
    },
    {
        "id": "TC-08",
        "question": "How do Digital Water Level Recorders (DWLR) support real-time groundwater monitoring?",
        "expected_topics": ["dwlr", "telemetry", "piezometer", "hydrostatic pressure", "real-time"],
        "expected_state": None,
        "is_supported": True,
        "expected_citation_doc": "05_ingres_portal_and_digital_groundwater_monitoring.md"
    },
    {
        "id": "TC-09",
        "question": "What was the stock price of Apple or Tesla on the NASDAQ exchange yesterday?",
        "expected_topics": [],
        "expected_state": None,
        "is_supported": False,
        "expected_citation_doc": None
    },
    {
        "id": "TC-10",
        "question": "Who won the FIFA Football World Cup final in 1998 and what was the score?",
        "expected_topics": [],
        "expected_state": None,
        "is_supported": False,
        "expected_citation_doc": None
    }
]


class BenchmarkEvaluator:
    def __init__(self, pipeline: RagPipeline):
        self.pipeline = pipeline

    def run_benchmark(self, test_cases: List[Dict[str, Any]] = GOLD_STANDARD_TEST_CASES) -> BenchmarkSummary:
        """Run all test cases and compile quantitative metrics."""
        results: List[TestCaseResult] = []
        retrieval_hits = 0
        total_faithfulness = 0.0
        supported_count = 0
        citation_count = 0
        unsupported_count = 0
        refusal_hits = 0
        total_latency = 0.0

        for tc in test_cases:
            q = tc["question"]
            is_supported = tc["is_supported"]
            req = ChatRequest(query=q, top_k=4)
            
            res = self.pipeline.answer_query(req)
            total_latency += res.execution_time_ms

            if is_supported:
                supported_count += 1
                answer_lower = res.answer.lower()
                
                # Check topic recall
                matched_topics = [t for t in tc["expected_topics"] if t.lower() in answer_lower]
                topic_recall = len(matched_topics) / max(len(tc["expected_topics"]), 1)
                
                # Retrieval hit check (expected source doc present in citations)
                ret_hit = False
                exp_doc = tc.get("expected_citation_doc")
                if exp_doc:
                    ret_hit = any(exp_doc.lower() in c.source_doc.lower() for c in res.citations)
                else:
                    ret_hit = len(res.citations) > 0

                if ret_hit:
                    retrieval_hits += 1

                has_cites = len(res.citations) > 0 and bool(res.citations)
                if has_cites:
                    citation_count += 1

                # Faithfulness score: ratio of topic overlap + attribution confidence
                faithfulness = round(min(1.0, 0.5 * topic_recall + 0.5 * res.confidence_score), 2)
                total_faithfulness += faithfulness

                status = "PASSED" if (ret_hit and topic_recall >= 0.4) else "FAILED"
                results.append(TestCaseResult(
                    question=q,
                    expected_topics=tc["expected_topics"],
                    retrieved_chunk_ids=[c.chunk_id for c in res.citations],
                    retrieval_hit=ret_hit,
                    faithfulness_score=faithfulness,
                    has_citations=has_cites,
                    refusal_correctness=True,
                    latency_ms=res.execution_time_ms,
                    status=status
                ))
            else:
                # Unsupported query handling test
                unsupported_count += 1
                correctly_refused = (not res.has_sufficient_evidence) or ("not contain sufficient" in res.answer.lower())
                if correctly_refused:
                    refusal_hits += 1

                status = "PASSED" if correctly_refused else "FAILED"
                results.append(TestCaseResult(
                    question=q,
                    expected_topics=[],
                    retrieved_chunk_ids=[c.chunk_id for c in res.citations],
                    retrieval_hit=len(res.citations) == 0,
                    faithfulness_score=1.0 if correctly_refused else 0.0,
                    has_citations=len(res.citations) > 0,
                    refusal_correctness=correctly_refused,
                    latency_ms=res.execution_time_ms,
                    status=status
                ))

        total_tests = len(test_cases)
        passed_count = sum(1 for r in results if r.status == "PASSED")
        
        prec_at_k = round(retrieval_hits / max(supported_count, 1), 3)
        rec_at_k = round(retrieval_hits / max(supported_count, 1), 3)
        avg_faith = round(total_faithfulness / max(supported_count, 1), 3)
        cite_rate = round(citation_count / max(supported_count, 1), 3)
        refusal_acc = round(refusal_hits / max(unsupported_count, 1), 3)
        avg_latency = round(total_latency / total_tests, 2)

        return BenchmarkSummary(
            total_tests=total_tests,
            passed_tests=passed_count,
            retrieval_precision_at_k=prec_at_k,
            retrieval_recall_at_k=rec_at_k,
            faithfulness_score_avg=avg_faith,
            citation_rate=cite_rate,
            unsupported_query_refusal_accuracy=refusal_acc,
            avg_latency_ms=avg_latency,
            test_results=results
        )
