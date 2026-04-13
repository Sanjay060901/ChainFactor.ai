"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useInvoiceId } from "@/hooks/useInvoiceId";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function AuditTrailClient({ params }: { params: { id: string } }) {
  const invoiceId = useInvoiceId(params.id);
  const [agents, setAgents] = useState<any[]>([]);
  const [totalDuration, setTotalDuration] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditTrail(invoiceId).then((data: any) => {
      if (data.agents && Array.isArray(data.agents)) {
        setAgents(data.agents);
        setTotalDuration(data.total_duration_ms || 0);
      } else {
        // Fallback: flat array of steps
        const steps = data.traces || data.steps || (Array.isArray(data) ? data : []);
        if (steps.length > 0) {
          setAgents([{ name: "Invoice Processing Agent", model: "sonnet-4.6", steps }]);
        }
      }
      setLoading(false);
    }).catch(() => {
      setAgents([]);
      setLoading(false);
    });
  }, [invoiceId]);

  return (
    <div>
      <Link href={`/invoices/${invoiceId}`} className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
        ← Back to Invoice
      </Link>

      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="mt-4 section-title">
        Audit Trail — Agent Reasoning Chain
      </motion.h1>

      {loading ? (
        <div className="mt-8 flex justify-center">
          <span className="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
        </div>
      ) : agents.length === 0 ? (
        <div className="mt-8 glass-card p-8 text-center">
          <p className="text-3xl">📋</p>
          <p className="mt-2 text-sm text-slate-500">No audit trail available yet. Process the invoice to generate agent traces.</p>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-6 space-y-6">
          {totalDuration > 0 && (
            <div className="glass-card p-4 text-center">
              <span className="text-xs text-slate-500">Total Pipeline Duration:</span>
              <span className="ml-2 text-sm font-medium text-slate-300">{(totalDuration / 1000).toFixed(1)}s</span>
            </div>
          )}

          {agents.map((agent: any, agentIdx: number) => {
            const isUnderwriting = agent.name?.toLowerCase().includes("underwriting");
            const colorClass = isUnderwriting ? "indigo" : "blue";
            const steps = agent.steps || [];

            return (
              <div key={agent.name || agentIdx}>
                {agentIdx > 0 && (
                  <div className="my-6 flex items-center gap-2">
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
                    <div className="flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5">
                      <span className="text-xs">🔄</span>
                      <span className="text-xs font-medium text-blue-400">HANDOFF → {agent.name}</span>
                    </div>
                    <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
                  </div>
                )}

                <div className="glass-card p-6">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-${colorClass}-500/20 border border-${colorClass}-500/30 text-lg`}>🤖</div>
                    <div>
                      <h2 className="font-semibold text-slate-200">{agent.name}</h2>
                      <p className="text-xs text-slate-500">{agent.model || "Sonnet 4.6"} · {steps.length} steps{agent.duration_ms ? ` · ${(agent.duration_ms / 1000).toFixed(1)}s` : ""}</p>
                    </div>
                  </div>

                  <div className="mt-4 space-y-2">
                    {steps.map((s: any, i: number) => (
                      <motion.div
                        key={s.step_number || i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 + i * 0.04 }}
                        className={`rounded-lg border border-${colorClass}-500/10 bg-slate-800/30 p-3`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-slate-200">
                            <span className={`text-${colorClass}-400`}>Step {s.step_number || i + 1}:</span> {s.tool_name || s.name}
                          </span>
                          <div className="flex items-center gap-2">
                            {s.status && <span className={`text-[10px] ${s.status === "success" ? "text-emerald-400" : "text-red-400"}`}>{s.status}</span>}
                            {(s.duration_ms || s.duration) && (
                              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                                {s.duration_ms ? `${(s.duration_ms / 1000).toFixed(1)}s` : `${s.duration}s`}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="mt-1 text-xs">
                          {s.input_summary && <span className="text-slate-500">Input: <span className="text-slate-400">{s.input_summary}</span></span>}
                          {s.input && !s.input_summary && <span className="text-slate-500">Input: <span className="text-slate-400">{typeof s.input === "string" ? s.input : JSON.stringify(s.input).slice(0, 100)}</span></span>}
                          {s.output_summary && (
                            <span className="ml-3 text-slate-500">Output: <span className="text-emerald-400">{s.output_summary}</span></span>
                          )}
                          {s.output && !s.output_summary && (
                            <span className="ml-3 text-slate-500">Output: <span className="text-emerald-400">
                              {typeof s.output === "string" ? s.output : JSON.stringify(s.output).slice(0, 120)}
                            </span></span>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
}
