"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DEMO_AUDIT_TRACES } from "@/lib/demo-data";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function AuditTrailClient({ params }: { params: { id: string } }) {
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditTrail(params.id).then((data: any) => {
      setTraces(data.traces || data.steps || (Array.isArray(data) ? data : []));
      setLoading(false);
    }).catch(() => {
      setTraces(DEMO_AUDIT_TRACES);
      setLoading(false);
    });
  }, [params.id]);

  const invoiceSteps = traces.filter((t: any) => (t.step_number || t.step) <= 10);
  const underwritingSteps = traces.filter((t: any) => (t.step_number || t.step) > 10);

  return (
    <div>
      <Link href={`/invoices/${params.id}`} className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
        ← Back to Invoice
      </Link>

      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="mt-4 section-title">
        Audit Trail — Agent Reasoning Chain
      </motion.h1>

      {loading ? (
        <div className="mt-8 flex justify-center">
          <span className="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
        </div>
      ) : traces.length === 0 ? (
        <div className="mt-8 glass-card p-8 text-center">
          <p className="text-3xl">📋</p>
          <p className="mt-2 text-sm text-slate-500">No audit trail available yet. Process the invoice to generate agent traces.</p>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-6 glass-card p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/20 border border-blue-500/30 text-lg">🤖</div>
            <div>
              <h2 className="font-semibold text-slate-200">Invoice Processing Agent</h2>
              <p className="text-xs text-slate-500">Sonnet 4.6 · {invoiceSteps.length} steps</p>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            {invoiceSteps.map((s: any, i: number) => (
              <motion.div
                key={s.step_number || s.step || i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.04 }}
                className="rounded-lg border border-blue-500/10 bg-slate-800/30 p-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-200">
                    <span className="text-blue-400">Step {s.step_number || s.step}:</span> {s.tool_name || s.name}
                  </span>
                  {s.duration && <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">{s.duration}s</span>}
                </div>
                <div className="mt-1 text-xs">
                  {s.input && <span className="text-slate-500">Input: <span className="text-slate-400">{typeof s.input === "string" ? s.input : JSON.stringify(s.input).slice(0, 100)}</span></span>}
                  {s.output && (
                    <span className="ml-3 text-slate-500">Output: <span className="text-emerald-400">
                      {typeof s.output === "string" ? s.output : JSON.stringify(s.output).slice(0, 120)}
                    </span></span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>

          {underwritingSteps.length > 0 && (
            <>
              <div className="my-6 flex items-center gap-2">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
                <div className="flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5">
                  <span className="text-xs">🔄</span>
                  <span className="text-xs font-medium text-blue-400">HANDOFF → Underwriting Agent</span>
                </div>
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
              </div>

              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-lg">🤖</div>
                <div>
                  <h2 className="font-semibold text-slate-200">Underwriting Agent</h2>
                  <p className="text-xs text-slate-500">Sonnet 4.6 · {underwritingSteps.length} steps</p>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                {underwritingSteps.map((s: any, i: number) => (
                  <motion.div
                    key={s.step_number || s.step || i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + i * 0.05 }}
                    className="rounded-lg border border-indigo-500/10 bg-slate-800/30 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-200">
                        <span className="text-indigo-400">Step {s.step_number || s.step}:</span> {s.tool_name || s.name}
                      </span>
                      {s.duration && <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">{s.duration}s</span>}
                    </div>
                    {s.output && (
                      <p className="mt-1 text-xs text-emerald-400">
                        {typeof s.output === "string" ? s.output : JSON.stringify(s.output).slice(0, 120)}
                      </p>
                    )}
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </motion.div>
      )}
    </div>
  );
}
