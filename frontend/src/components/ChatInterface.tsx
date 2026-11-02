import React, { useState, useRef, useEffect } from "react";
import { Send, Droplet, BookOpen, AlertCircle, Sparkles, Clock, ShieldCheck, MapPin, Calendar } from "lucide-react";
import { ChatMessage, Citation } from "../types";
import { sendChatQuery } from "../services/api";

interface ChatInterfaceProps {
  onViewSource: (citation: Citation) => void;
}

const SAMPLE_PROMPTS = [
  "What is the 10-year trend of groundwater recharge and extraction in India (2015–2025)?",
  "How has groundwater extraction changed in Punjab, Rajasthan, and Haryana across 2021 to 2025?",
  "What is the formula to calculate the Stage of Ground Water Extraction under GEC-2015?",
  "Show the multi-year groundwater trend for Delhi and its over-exploited units.",
  "Which states are covered under the Atal Bhujal Yojana and what are its objectives?",
  "What artificial recharge structures are recommended for hard rock basalt aquifers?",
  "What are the BIS drinking water standard limits for Arsenic and Fluoride?"
];

const STATES = [
  "All States",
  "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
  "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli", "Daman and Diu",
  "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
  "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
  "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamilnadu",
  "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
];

const WELCOME_TEXT = `Welcome to WaterBoy Intelligence — India's Unified Groundwater AI & Analytics Platform.

Powered by authoritative records from the Central Ground Water Board (CGWB), Ministry of Jal Shakti, and INGRES, I deliver data-grounded intelligence across all 38 States and Union Territories, spanning decadal historical trends (2015 to 2025) and multi-year dynamic resource assessments.

🔍 What you can explore with me:
• Multi-Year Trajectories: Compare annual recharge, extraction draft, and Stage of Extraction (%) trends across 2021–2025 and decadal records.
• State & District Diagnostics: Inquire about over-exploited blocks, critical water stress, and aquifer dynamics for any region in India.
• Hydrogeology & Water Quality: BIS 10500:2012 standards, fluoride, arsenic, salinity, and depth-to-water levels.
• Conservation & Policy: Guidelines on Atal Bhujal Yojana, NAQUIM, artificial recharge structures, and rainwater harvesting.

Every response is backed by verifiable citations directly linked to official records. How can I assist your groundwater research today?`;

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ onViewSource }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "bot",
      text: WELCOME_TEXT,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedState, setSelectedState] = useState("All States");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const queryText = (customQuery || input).trim();
    if (!queryText || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const stateFilter = selectedState !== "All States" ? selectedState : undefined;
      const response = await sendChatQuery(queryText, 4, stateFilter);

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: response.answer,
        citations: response.citations,
        confidenceScore: response.confidence_score,
        latencyMs: response.execution_time_ms,
        hasSufficientEvidence: response.has_sufficient_evidence,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: "bot",
        text: "I encountered a communication issue connecting to the groundwater intelligence service. Please ensure the backend server is running.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 flex flex-col h-[calc(100vh-4rem)]">
      {/* Top Banner Filter */}
      <div className="bg-white border border-slate-200/80 p-3.5 rounded-2xl shadow-xs mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-pulse"></span>
          <span className="text-xs font-bold text-slate-800">Unified Groundwater Intelligence</span>
          <span className="text-slate-300">|</span>
          <span className="text-xs text-slate-500">All 38 States & UTs • Decadal & Multi-Year Datasets</span>
        </div>

        <div className="flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-sky-600" />
          <span className="text-xs font-semibold text-slate-600">Focus State:</span>
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-xs font-semibold text-sky-700 rounded-lg px-2.5 py-1 focus:outline-none focus:border-sky-500 cursor-pointer max-w-[200px]"
          >
            {STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 pb-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4.5 sm:p-5 shadow-xs transition-all ${msg.sender === "user"
                  ? "bg-sky-500 text-white rounded-tr-xs"
                  : "bg-white border border-slate-200/80 text-slate-800 rounded-tl-xs"
                }`}
            >
              {/* Header inside Bot Message */}
              {msg.sender === "bot" && (
                <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-sky-50 flex items-center justify-center text-sky-600 border border-sky-100">
                      <Droplet className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold text-sky-700">WaterBoy Intelligence</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    {msg.latencyMs !== undefined && (
                      <span className="flex items-center gap-1 font-mono">
                        <Clock className="w-3 h-3 text-sky-500" />
                        {msg.latencyMs.toFixed(0)} ms
                      </span>
                    )}
                    <span>{msg.timestamp}</span>
                  </div>
                </div>
              )}

              {/* Message Content */}
              <div className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans">
                {msg.text}
              </div>

              {/* Citations Panel */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                      <BookOpen className="w-3 h-3 text-sky-500" />
                      Verifiable CGWB Evidence ({msg.citations.length})
                    </span>
                    {msg.confidenceScore !== undefined && (
                      <span className="text-[11px] font-semibold text-sky-600 bg-sky-50 px-2 py-0.5 rounded-full border border-sky-100">
                        {(msg.confidenceScore * 100).toFixed(0)}% Grounding Confidence
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {msg.citations.map((cite, idx) => (
                      <button
                        key={idx}
                        onClick={() => onViewSource(cite)}
                        className="text-left p-2.5 rounded-xl bg-slate-50 hover:bg-sky-50/70 border border-slate-200/80 hover:border-sky-300 transition group flex flex-col justify-between"
                      >
                        <div className="flex items-center justify-between w-full mb-1">
                          <span className="text-[11px] font-bold text-slate-700 truncate group-hover:text-sky-700">
                            [{idx + 1}] {cite.title}
                          </span>
                          <span className="text-[10px] font-mono font-semibold text-sky-600 ml-1">
                            {(cite.relevance_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-2 leading-tight">
                          {cite.excerpt}
                        </p>
                        <span className="text-[10px] text-sky-600/80 font-medium mt-1">
                          Click to view source data &rarr;
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-xs p-4 shadow-xs flex items-center space-x-3">
              <div className="w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs font-medium text-slate-500">
                Searching 1,664 CGWB multi-year knowledge chunks & synthesizing grounded response...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Pill Row */}
      {messages.length <= 2 && (
        <div className="py-2 overflow-x-auto no-scrollbar flex items-center gap-2">
          <span className="text-xs text-sky-700 font-semibold whitespace-nowrap flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-sky-500" /> Try Asking:
          </span>
          {SAMPLE_PROMPTS.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSubmit(undefined, p)}
              className="text-xs bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 border border-slate-200 hover:border-sky-300 rounded-full px-3 py-1.5 whitespace-nowrap transition shadow-2xs font-medium cursor-pointer"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="pt-2">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about multi-year extraction trends, state water tables, or artificial recharge..."
            disabled={loading}
            className="w-full bg-white border border-slate-200 text-sm text-slate-800 rounded-2xl pl-4 pr-12 py-3.5 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 shadow-sm placeholder:text-slate-400 transition"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2.5 p-2 rounded-xl bg-sky-500 hover:bg-sky-600 disabled:opacity-40 text-white transition shadow-xs cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
