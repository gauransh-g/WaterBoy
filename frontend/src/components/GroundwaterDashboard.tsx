import React, { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  AreaChart, Area, CartesianGrid, Legend
} from "recharts";
import { Database, AlertTriangle, ShieldCheck, Layers, MapPin, Search, Calendar, TrendingUp } from "lucide-react";
import { GroundwaterOverview, StateSummary, AssessmentUnitData, YearlyTrend } from "../types";
import { fetchGroundwaterOverview, fetchStateSummaries, fetchDistrictUnits, fetchGroundwaterTrends } from "../services/api";

const CATEGORY_COLORS: Record<string, string> = {
  Safe: "#0ea5e9", // Sky blue for safe/healthy
  "Semi Critical": "#f59e0b",
  Critical: "#f97316",
  "Over Exploited": "#ef4444",
  Salinity: "#8b5cf6",
  Unspecified: "#94a3b8"
};

const ASSESSMENT_YEARS = [
  { label: "All Assessment Cycles (2021–2025 & Decadal)", value: "" },
  { label: "Assessment Cycle 2024–2025 (Latest)", value: "2024-2025" },
  { label: "Assessment Cycle 2023–2024", value: "2023-2024" },
  { label: "Assessment Cycle 2022–2023", value: "2022-2023" },
  { label: "Assessment Cycle 2021–2022", value: "2021-2022" },
];

export const GroundwaterDashboard: React.FC = () => {
  const [overview, setOverview] = useState<GroundwaterOverview | null>(null);
  const [states, setStates] = useState<StateSummary[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedState, setSelectedState] = useState<string>("Delhi");
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);
  const [districtUnits, setDistrictUnits] = useState<AssessmentUnitData[]>([]);
  const [yearlyTrends, setYearlyTrends] = useState<YearlyTrend[]>([]);
  const [trendLoading, setTrendLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [ovData, stData] = await Promise.all([
          fetchGroundwaterOverview(selectedYear || undefined),
          fetchStateSummaries(selectedYear || undefined)
        ]);
        setOverview(ovData);
        setStates(stData);
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedYear]);

  // Load trends whenever selectedState changes
  useEffect(() => {
    async function loadTrends() {
      if (!selectedState) return;
      try {
        setTrendLoading(true);
        const trends = await fetchGroundwaterTrends(selectedState);
        setYearlyTrends(trends);
      } catch (err) {
        console.error("Failed to load historical trends:", err);
      } finally {
        setTrendLoading(false);
      }
    }
    loadTrends();
  }, [selectedState]);

  const handleStateClick = async (stateName: string) => {
    setSelectedState(stateName);
    setSelectedDistrict(null);
    setDistrictUnits([]);
  };

  const handleDistrictDrilldown = async (stateName: string, districtName: string) => {
    setSelectedDistrict(districtName);
    try {
      const units = await fetchDistrictUnits(stateName, districtName);
      setDistrictUnits(units);
    } catch (err) {
      console.error("Failed to load district data:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <div className="text-center space-y-3">
          <div className="w-9 h-9 border-3 border-sky-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-medium text-slate-500">Loading Central Ground Water Board (CGWB) Multi-Year Datasets...</p>
        </div>
      </div>
    );
  }

  const chartData = overview?.category_breakdown
    ? Object.entries(overview.category_breakdown).map(([name, count]) => ({
        name,
        count
      }))
    : [];

  // Guarantee alphabetical ordering of all States and Union Territories
  const sortedStates = [...states].sort((a, b) => a.state.localeCompare(b.state));

  const filteredStates = sortedStates.filter((s) =>
    s.state.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      {/* Header with Year Selector Filter */}
      <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-pulse"></span>
            National Groundwater Intelligence & Multi-Year Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Dynamic Groundwater Resource Assessment Reports published by Central Ground Water Board (CGWB) & INGRES.
          </p>
        </div>

        {/* Year Filter Dropdown */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
          <Calendar className="w-4 h-4 text-sky-600" />
          <span className="text-xs font-semibold text-slate-600">Cycle:</span>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="bg-transparent text-xs font-semibold text-sky-700 outline-none cursor-pointer pr-2"
          >
            {ASSESSMENT_YEARS.map((yr) => (
              <option key={yr.value} value={yr.value}>
                {yr.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm hover:border-sky-200 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-600">Assessed Units</span>
            <div className="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center text-sky-600">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-slate-900">
            {overview?.total_assessment_units || 0}
          </div>
          <p className="text-xs text-sky-700/80 font-medium mt-1">Across {overview?.total_states_covered || 0} States & UTs</p>
        </div>

        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm hover:border-sky-200 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-600">Safe Category</span>
            <div className="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center text-sky-500">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-sky-600">
            {overview?.category_breakdown?.["Safe"] || 0}
          </div>
          <p className="text-xs text-slate-500 mt-1">Extraction &lt; 70% of recharge</p>
        </div>

        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm hover:border-rose-200 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-600">Over-Exploited</span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center text-rose-500">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-rose-600">
            {overview?.category_breakdown?.["Over Exploited"] || 0}
          </div>
          <p className="text-xs text-slate-500 mt-1">Draft exceeds natural replenishment</p>
        </div>

        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm hover:border-amber-200 transition">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold text-slate-600">Critical & Semi-Crit</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-500">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-amber-600">
            {(overview?.category_breakdown?.["Semi Critical"] || 0) +
              (overview?.category_breakdown?.["Critical"] || 0)}
          </div>
          <p className="text-xs text-slate-500 mt-1">Intensive monitoring required</p>
        </div>
      </div>

      {/* Multi-Year Historical Trend Analysis (Key Feature) */}
      <div className="bg-white border border-slate-200/80 p-6 rounded-2xl shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-sky-600" />
              <h3 className="text-base font-bold text-slate-800">
                Multi-Year Trend Analysis (2021–2025): <span className="text-sky-600">{selectedState}</span>
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Historical progression of groundwater extraction rates and recharge across consecutive assessment cycles.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Select State:</span>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-xs font-semibold text-sky-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500 cursor-pointer"
            >
              {sortedStates.map((st) => (
                <option key={st.state} value={st.state}>
                  {st.state}
                </option>
              ))}
            </select>
          </div>
        </div>

        {trendLoading ? (
          <div className="h-60 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : yearlyTrends.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
            <div className="lg:col-span-2 h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={yearlyTrends} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorSoe" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="year" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} domain={[0, 'auto']} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "10px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}
                    formatter={(val: any, name: string) => [
                      name === "avg_stage_of_extraction" ? `${val}%` : `${val} Ham`,
                      name === "avg_stage_of_extraction" ? "Avg Extraction Stage" : "Total Recharge"
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="avg_stage_of_extraction"
                    name="avg_stage_of_extraction"
                    stroke="#0ea5e9"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#colorSoe)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-3 flex flex-col justify-center bg-sky-50/50 p-4 rounded-xl border border-sky-100">
              <h4 className="text-xs font-bold text-sky-800 uppercase tracking-wider">
                Multi-Year Trajectory Summary
              </h4>
              {yearlyTrends.map((trend) => (
                <div key={trend.year} className="flex items-center justify-between p-2.5 bg-white rounded-lg border border-slate-200/80 shadow-xs">
                  <div>
                    <span className="text-xs font-bold text-slate-800">{trend.year}</span>
                    <p className="text-[11px] text-slate-500">{trend.total_units} Assessed Units</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-bold ${trend.avg_stage_of_extraction > 100 ? "text-rose-600" : trend.avg_stage_of_extraction > 70 ? "text-amber-600" : "text-sky-600"}`}>
                      {trend.avg_stage_of_extraction}% SOE
                    </span>
                    <p className="text-[10px] text-slate-400 font-mono">
                      {trend.over_exploited_units} Over-Exploited
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-500 py-6 text-center">
            No historical trend data recorded for {selectedState}.
          </p>
        )}
      </div>

      {/* Visual Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Distribution Bar */}
        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm">
          <h3 className="text-sm font-bold text-slate-800 mb-0.5">
            Groundwater Development Category Distribution
          </h3>
          <p className="text-xs text-slate-500 mb-4">Official CGWB Classification Breakdown</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "10px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.name] || "#0ea5e9"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Over-Exploited States */}
        <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-sm">
          <h3 className="text-sm font-bold text-slate-800 mb-0.5">
            Top Groundwater-Stressed States
          </h3>
          <p className="text-xs text-slate-500 mb-4">Ranked by count of Over-Exploited assessment blocks</p>
          <div className="space-y-2.5">
            {overview?.top_overexploited_states.map((st, i) => (
              <div
                key={i}
                onClick={() => handleStateClick(st.state)}
                className={`flex items-center justify-between p-3 rounded-xl border transition cursor-pointer ${
                  selectedState === st.state
                    ? "bg-sky-50 border-sky-300"
                    : "bg-slate-50/70 border-slate-200/70 hover:bg-slate-100/60"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-md bg-rose-100 text-rose-700 text-xs font-bold flex items-center justify-center font-mono">
                    #{i + 1}
                  </span>
                  <span className="text-sm font-semibold text-slate-800">{st.state}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-semibold">
                    {st.over_exploited_units} Over-Exploited Blocks
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* State Assessment Explorer Table */}
      <div className="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-800">State Groundwater Assessment Explorer</h3>
            <p className="text-xs text-slate-500">Select any state to display its multi-year trend and indicators</p>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Indian State..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-xs text-slate-800 rounded-xl pl-9 pr-4 py-2 focus:outline-none focus:border-sky-500 focus:bg-white transition"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-semibold">
              <tr>
                <th className="p-3.5 pl-5">State</th>
                <th className="p-3.5">Assessed Units</th>
                <th className="p-3.5">Safe</th>
                <th className="p-3.5">Semi-Crit</th>
                <th className="p-3.5">Critical</th>
                <th className="p-3.5">Over-Exploited</th>
                <th className="p-3.5">Avg Stage of Extraction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStates.map((st) => (
                <tr
                  key={st.state}
                  onClick={() => handleStateClick(st.state)}
                  className={`cursor-pointer transition ${
                    selectedState === st.state
                      ? "bg-sky-50/80 border-l-4 border-sky-500"
                      : "hover:bg-slate-50/60"
                  }`}
                >
                  <td className="p-3.5 pl-5 font-semibold text-slate-800 flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-sky-600" />
                    {st.state}
                  </td>
                  <td className="p-3.5 text-slate-700 font-mono font-medium">{st.total_units}</td>
                  <td className="p-3.5 text-sky-700 font-mono font-medium">{st.safe_units}</td>
                  <td className="p-3.5 text-amber-600 font-mono font-medium">{st.semi_critical_units}</td>
                  <td className="p-3.5 text-orange-600 font-mono font-medium">{st.critical_units}</td>
                  <td className="p-3.5 text-rose-600 font-mono font-bold">{st.over_exploited_units}</td>
                  <td className="p-3.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-800 font-medium">{st.avg_stage_of_extraction}%</span>
                      <div className="w-20 bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                        <div
                          className={`h-full ${
                            st.avg_stage_of_extraction > 100
                              ? "bg-rose-500"
                              : st.avg_stage_of_extraction > 70
                              ? "bg-amber-500"
                              : "bg-sky-500"
                          }`}
                          style={{ width: `${Math.min(100, Math.max(5, st.avg_stage_of_extraction))}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
