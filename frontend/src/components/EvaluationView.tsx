import React, { useState, useEffect } from "react";
import { Activity, Play, CheckCircle, XCircle, Clock, ShieldCheck, FileText, Award } from "lucide-react";
import { BenchmarkSummary } from "../types";
import { runEvaluationBenchmark } from "../services/api";

export const EvaluationView: React.FC = () => {
  const [benchmark, setBenchmark] = useState<BenchmarkSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunBenchmark = async () => {
    try {
      setRunning(true);
      setError(null);
      const data = await runEvaluationBenchmark();
      setBenchmark(data);
    } catch (err: any) {
      setError(err.message || "Failed to execute benchmark");
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    // Run benchmark initially on view load
    handleRunBenchmark();
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header and Trigger */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-600" />
            Groundwater AI Evaluation & Accuracy Benchmark
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Empirical validation across Precision@k, Faithfulness, Citation Attributions, and Out-of-Domain Refusal Accuracy.
          </p>
        </div>
        <button
          onClick={handleRunBenchmark}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-sm font-semibold transition shadow-md shadow-sky-600/20 cursor-pointer"
        >
          {running ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Executing Evaluation Suite...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run Live Benchmark</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {/* Metrics Grid */}
      {benchmark && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-white border border-slate-200/80 p-4 rounded-2xl shadow-sm">
              <span className="text-[11px] text-slate-500 font-semibold block">Benchmark Score</span>
              <span className="text-2xl font-bold text-sky-600 mt-1 block">
                {benchmark.passed_tests}/{benchmark.total_tests}
              </span>
              <span className="text-[10px] text-slate-400">
                {((benchmark.passed_tests / benchmark.total_tests) * 100).toFixed(0)}% Passed
              </span>
            </div>

            <div className="bg-white border border-slate-200/80 p-4 rounded-2xl shadow-sm">
              <span className="text-[11px] text-slate-500 font-semibold block">Retrieval Precision</span>
              <span className="text-2xl font-bold text-sky-600 mt-1 block">
                {(benchmark.retrieval_precision_at_k * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400">Precision@k (k=4)</span>
            </div>

            <div className="bg-white border border-slate-200/80 p-4 rounded-2xl shadow-sm">
              <span className="text-[11px] text-slate-500 font-semibold block">Faithfulness</span>
              <span className="text-2xl font-bold text-sky-700 mt-1 block">
                {(benchmark.faithfulness_score_avg * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-400">Evidence grounded</span>
            </div>

            <div className="bg-white border border-slate-200/80 p-4 rounded-2xl shadow-sm">
              <span className="text-[11px] text-slate-500 font-semibold block">Citation Rate</span>
              <span className="text-2xl font-bold text-sky-600 mt-1 block">
                {(benchmark.citation_rate * 100).toFixed(0)}%
              </span>
              <span className="text-[10px] text-slate-400">Verifiable sources</span>
            </div>

            <div className="bg-white border border-slate-200/80 p-4 rounded-2xl shadow-sm">
              <span className="text-[11px] text-slate-500 font-semibold block">Refusal Accuracy</span>
              <span className="text-2xl font-bold text-emerald-600 mt-1 block">
                {(benchmark.unsupported_query_refusal_accuracy * 100).toFixed(0)}%
              </span>
              <span className="text-[10px] text-slate-400">Anti-hallucination</span>
            </div>

            <div className="bg-white border border-slate-200/80 p-4 rounded-2xl shadow-sm">
              <span className="text-[11px] text-slate-500 font-semibold block">Avg Latency</span>
              <span className="text-2xl font-bold text-slate-800 mt-1 block font-mono">
                {benchmark.avg_latency_ms.toFixed(1)} <span className="text-xs font-normal text-slate-400">ms</span>
              </span>
              <span className="text-[10px] text-slate-400">End-to-end</span>
            </div>
          </div>

          {/* Test Cases Table */}
          <div className="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">Gold-Standard Test Suite Cases</h3>
              <span className="text-xs text-sky-700 font-medium bg-sky-50 px-2.5 py-1 rounded-lg border border-sky-100">
                Groundwater Domain QA
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-semibold">
                  <tr>
                    <th className="p-3 pl-5">Status</th>
                    <th className="p-3">Inquiry Question</th>
                    <th className="p-3">Retrieved Chunks</th>
                    <th className="p-3">Faithfulness</th>
                    <th className="p-3">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {benchmark.test_results.map((res, i) => (
                    <tr key={i} className="hover:bg-slate-50/70 transition">
                      <td className="p-3 pl-5">
                        {res.status === "PASSED" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle className="w-3 h-3" />
                            Passed
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            <XCircle className="w-3 h-3" />
                            Failed
                          </span>
                        )}
                      </td>
                      <td className="p-3 font-medium text-slate-800 max-w-md">{res.question}</td>
                      <td className="p-3 font-mono text-slate-500">
                        {res.retrieved_chunk_ids.length > 0
                          ? `${res.retrieved_chunk_ids.length} chunks`
                          : "None (Safely Refused)"}
                      </td>
                      <td className="p-3">
                        <span className="font-mono text-sky-600 font-bold">
                          {(res.faithfulness_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="p-3 font-mono text-slate-500">{res.latency_ms.toFixed(1)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
