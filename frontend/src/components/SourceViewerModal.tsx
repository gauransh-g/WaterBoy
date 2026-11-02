import React from "react";
import { X, ExternalLink, BookOpen, MapPin, Award } from "lucide-react";
import { Citation } from "../types";

interface SourceViewerModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const SourceViewerModal: React.FC<SourceViewerModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in-50 zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-sky-50 text-sky-600 border border-sky-100">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-base leading-tight">
                {citation.title}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">{citation.source_doc}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-[11px] text-slate-500 block font-semibold">Relevance</span>
              <span className="text-sm font-bold text-sky-600 flex items-center gap-1 mt-0.5">
                <Award className="w-3.5 h-3.5" />
                {(citation.relevance_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-[11px] text-slate-500 block font-semibold">Section</span>
              <span className="text-xs font-semibold text-slate-700 mt-0.5 block truncate">
                {citation.section || "General"}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-[11px] text-slate-500 block font-semibold">Geography</span>
              <span className="text-xs font-semibold text-slate-700 mt-0.5 flex items-center gap-1 truncate">
                <MapPin className="w-3.5 h-3.5 text-sky-500" />
                {citation.state || "National"}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <span className="text-[11px] text-slate-500 block font-semibold">Assessment Cycle</span>
              <span className="text-xs font-semibold text-sky-700 mt-0.5 block">
                {citation.year || "2023-2024"}
              </span>
            </div>
          </div>

          {/* Excerpt */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-700">Verifiable Ground-Truth Excerpt</label>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs sm:text-sm leading-relaxed text-slate-800 font-mono whitespace-pre-wrap">
              {citation.excerpt}
            </div>
          </div>

          {/* Chunk Identifier */}
          <div className="text-xs text-slate-500 flex items-center justify-between pt-2">
            <span>Indexed Chunk ID: <code className="text-sky-600 font-mono font-medium">{citation.chunk_id}</code></span>
            <span className="flex items-center gap-1 text-slate-500">
              <ExternalLink className="w-3.5 h-3.5 text-sky-500" />
              Central Ground Water Board (CGWB)
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-sm font-semibold text-slate-700 transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
