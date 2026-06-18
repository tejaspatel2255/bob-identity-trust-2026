"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getRiskEvents, reviewRiskEvent } from "../../lib/api";
import { RiskEvent } from "../../lib/types";
import { 
  ArrowLeft,
  ChevronLeft, 
  ChevronRight, 
  Filter,
  CheckCircle,
  XCircle,
  Eye,
  ShieldAlert
} from "lucide-react";

export default function LiveFeed() {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<RiskEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" } | null>(null);
  
  // Filters
  const [filterAction, setFilterAction] = useState<string>("ALL");
  const [filterType, setFilterType] = useState<string>("ALL");

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const showToast = (message: string, type: "error" | "success" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await getRiskEvents();
      setEvents(data);
    } catch (err: any) {
      showToast(err.message || "Failed to load events", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  // Filter application
  useEffect(() => {
    let result = events;

    if (filterAction !== "ALL") {
      result = result.filter((e) => e.action === filterAction);
    }

    if (filterType !== "ALL") {
      result = result.filter((e) => e.entity_type === filterType);
    }

    setFilteredEvents(result);
    setCurrentPage(1); // Reset to page 1 on filter
  }, [events, filterAction, filterType]);

  // Handle Review Actions
  const handleReview = async (id: string, outcome: "FALSE_POSITIVE" | "CONFIRMED_FRAUD") => {
    try {
      await reviewRiskEvent(id, { reviewed: true, review_outcome: outcome });
      
      // Update local state to show review status instantly
      setEvents((prev) =>
        prev.map((e) =>
          e.id === id || e.entity_id === id
            ? { ...e, reviewed: true, review_outcome: outcome }
            : e
        )
      );

      showToast(`Incident mark cataloged as: ${outcome.replace(/_/g, " ")}`, "success");
    } catch (err: any) {
      showToast(err.message || "Review submission failed", "error");
    }
  };

  // Pagination bounds
  const totalPages = Math.ceil(filteredEvents.length / itemsPerPage) || 1;
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredEvents.slice(indexOfFirstItem, indexOfLastItem);

  return (
    <div className="p-8 pb-12 min-h-screen">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link
          href="/dashboard"
          className="flex h-9 w-9 items-center justify-center rounded border border-soc-border bg-soc-surface text-soc-textSecondary hover:border-soc-cyan hover:text-soc-cyan transition-all"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <span className="font-mono text-[10px] text-soc-textSecondary uppercase tracking-widest font-semibold">
            SEC Ops Archives
          </span>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-soc-textPrimary">
            Complete Risk Events Log
          </h1>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center gap-4 rounded-lg border border-soc-border bg-soc-surface p-4 mb-6">
        <div className="flex items-center gap-2 text-soc-textSecondary text-xs font-semibold uppercase tracking-wider mr-auto">
          <Filter className="h-3.5 w-3.5" />
          Filter Operations
        </div>

        {/* Action Type Filter Buttons (No html form tags) */}
        <div className="flex gap-2 text-[10px]">
          {["ALL", "HARD_BLOCK", "STEP_UP_AUTH", "SILENT_PASS"].map((act) => (
            <button
              key={act}
              onClick={() => setFilterAction(act)}
              className={`rounded px-3 py-1.5 border font-bold uppercase tracking-wider transition-all ${
                filterAction === act
                  ? "border-soc-cyan bg-soc-cyan/15 text-soc-cyan"
                  : "border-soc-border bg-soc-bg text-soc-textSecondary hover:text-soc-textPrimary"
              }`}
            >
              {act === "ALL" ? "All Actions" : act.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {/* Entity Type Filter Buttons */}
        <div className="flex gap-2 text-[10px]">
          {["ALL", "CUSTOMER_SESSION", "EMPLOYEE_ACCESS"].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`rounded px-3 py-1.5 border font-bold uppercase tracking-wider transition-all ${
                filterType === t
                  ? "border-soc-cyan bg-soc-cyan/15 text-soc-cyan"
                  : "border-soc-border bg-soc-bg text-soc-textSecondary hover:text-soc-textPrimary"
              }`}
            >
              {t === "ALL" ? "All Types" : t === "EMPLOYEE_ACCESS" ? "Staff" : "Customer"}
            </button>
          ))}
        </div>
      </div>

      {/* Main Table */}
      <div className="rounded-lg border border-soc-border bg-soc-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-soc-border bg-soc-bg/50 text-[10px] uppercase font-bold tracking-wider text-soc-textSecondary">
                <th className="p-4">Time</th>
                <th className="p-4">Entity ID</th>
                <th className="p-4">Type</th>
                <th className="p-4 text-center">Score</th>
                <th className="p-4">Action</th>
                <th className="p-4">Compliance Explanation</th>
                <th className="p-4">AI Model</th>
                <th className="p-4 text-center">Actions / Status</th>
              </tr>
            </thead>
            
            <tbody className="divide-y divide-soc-border/40 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={8} className="p-12 text-center text-soc-textSecondary">
                    <div className="flex flex-col items-center gap-2">
                      <span className="h-6 w-6 animate-spin rounded-full border-2 border-soc-cyan border-t-transparent"></span>
                      <span>Querying DB Archives...</span>
                    </div>
                  </td>
                </tr>
              ) : currentItems.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-12 text-center text-soc-textSecondary font-mono uppercase tracking-widest text-[10px]">
                    No matching compliance incidents found.
                  </td>
                </tr>
              ) : (
                currentItems.map((ev) => {
                  // Style levels
                  const score = ev.risk_score;
                  let scoreClass = "bg-soc-green/10 text-soc-green border-soc-green/30";
                  if (score >= 66) scoreClass = "bg-soc-red/10 text-soc-red border-soc-red/30 font-bold";
                  else if (score >= 31) scoreClass = "bg-soc-amber/10 text-soc-amber border-soc-amber/30";

                  // Action Badge
                  let actionClass = "text-soc-green";
                  if (ev.action === "HARD_BLOCK" || score >= 66) actionClass = "text-soc-red font-bold";
                  else if (ev.action === "STEP_UP_AUTH" || score >= 31) actionClass = "text-soc-amber";

                  return (
                    <tr key={ev.id} className="hover:bg-soc-bg/25 transition-colors">
                      {/* Timestamp */}
                      <td className="p-4 font-mono text-[11px] text-soc-textSecondary whitespace-nowrap">
                        {new Date(ev.timestamp).toLocaleString("en-IN")}
                      </td>

                      {/* Entity ID */}
                      <td className="p-4 font-mono font-bold text-soc-textPrimary">
                        <Link href={`/cases/${ev.id}`} className="hover:text-soc-cyan hover:underline">
                          {ev.entity_id}
                        </Link>
                      </td>

                      {/* Entity Type */}
                      <td className="p-4 uppercase tracking-wider font-semibold text-[10px]">
                        <span className={ev.entity_type === "EMPLOYEE_ACCESS" ? "text-soc-purple" : "text-soc-cyan"}>
                          {ev.entity_type === "EMPLOYEE_ACCESS" ? "Staff" : "Customer"}
                        </span>
                      </td>

                      {/* Risk Score Pill */}
                      <td className="p-4 text-center">
                        <span className={`inline-block rounded border px-2 py-0.5 font-mono text-[11px] ${scoreClass}`}>
                          {score.toFixed(1)}%
                        </span>
                      </td>

                      {/* Action Pill */}
                      <td className="p-4 font-semibold tracking-wide">
                        <span className={actionClass}>
                          {ev.action ? ev.action.replace(/_/g, " ") : "SILENT PASS"}
                        </span>
                      </td>

                      {/* Truncated Explanation */}
                      <td className="p-4 max-w-xs truncate text-soc-textSecondary" title={ev.explanation}>
                        {ev.explanation}
                      </td>

                      {/* Provider name */}
                      <td className="p-4 font-mono text-[10px] text-soc-textSecondary">
                        {ev.provider_used === "template" ? "offline template" : ev.provider_used}
                      </td>

                      {/* Review Actions column */}
                      <td className="p-4">
                        <div className="flex items-center justify-center gap-2">
                          {ev.reviewed ? (
                            <span className={`rounded border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
                              ev.review_outcome === "CONFIRMED_FRAUD" 
                                ? "bg-soc-red/10 text-soc-red border-soc-red/30" 
                                : "bg-soc-green/10 text-soc-green border-soc-green/30"
                            }`}>
                              {ev.review_outcome === "CONFIRMED_FRAUD" ? "FRAUD CONFIRMED" : "CLEARED"}
                            </span>
                          ) : (
                            <>
                              <button
                                onClick={() => handleReview(ev.id, "FALSE_POSITIVE")}
                                className="flex items-center gap-1 rounded border border-soc-green/30 hover:border-soc-green bg-soc-green/5 hover:bg-soc-green/15 px-2 py-1 text-[9px] font-bold uppercase tracking-wider text-soc-green transition-all"
                              >
                                <CheckCircle className="h-3 w-3" />
                                Clear
                              </button>
                              <button
                                onClick={() => handleReview(ev.id, "CONFIRMED_FRAUD")}
                                className="flex items-center gap-1 rounded border border-soc-red/30 hover:border-soc-red bg-soc-red/5 hover:bg-soc-red/15 px-2 py-1 text-[9px] font-bold uppercase tracking-wider text-soc-red transition-all"
                              >
                                <XCircle className="h-3 w-3" />
                                Confirm
                              </button>
                            </>
                          )}
                          
                          {/* Case File icon link */}
                          <Link
                            href={`/cases/${ev.id}`}
                            className="flex h-6 w-6 items-center justify-center rounded border border-soc-border bg-soc-bg text-soc-textSecondary hover:border-soc-cyan hover:text-soc-cyan transition-all"
                            title="Open Case File"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center justify-between border-t border-soc-border bg-soc-bg/30 p-4">
          <span className="text-xs text-soc-textSecondary">
            Showing <span className="font-mono text-soc-textPrimary">{filteredEvents.length === 0 ? 0 : indexOfFirstItem + 1}</span> to{" "}
            <span className="font-mono text-soc-textPrimary">{Math.min(indexOfLastItem, filteredEvents.length)}</span> of{" "}
            <span className="font-mono text-soc-textPrimary">{filteredEvents.length}</span> records
          </span>

          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1 || loading}
              className="flex h-8 w-8 items-center justify-center rounded border border-soc-border bg-soc-surface text-soc-textSecondary hover:border-soc-cyan hover:text-soc-cyan disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="flex items-center px-3 font-mono text-xs font-semibold text-soc-textPrimary">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || loading}
              className="flex h-8 w-8 items-center justify-center rounded border border-soc-border bg-soc-surface text-soc-textSecondary hover:border-soc-cyan hover:text-soc-cyan disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Styled Success/Error Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 rounded border p-4 shadow-2xl transition-all duration-300 max-w-sm ${
          toast.type === "error"
            ? "border-soc-red bg-soc-surface text-soc-red glow-red"
            : "border-soc-cyan bg-soc-surface text-soc-cyan glow-cyan"
        }`}>
          <div className="flex gap-3 items-start">
            <ShieldAlert className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-display text-xs font-bold uppercase tracking-wider">
                {toast.type === "error" ? "SOC Operations Alert" : "System Notification"}
              </h4>
              <p className="text-xs text-soc-textPrimary mt-1 font-medium">
                {toast.message}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
