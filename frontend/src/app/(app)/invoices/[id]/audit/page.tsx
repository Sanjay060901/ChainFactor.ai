"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const auditSteps = [
  { step: 1, name: "extract_invoice", time: "3.2s", input: "invoice_march_2026.pdf (1.2 MB)", output: "23 fields extracted, 2 line items", confidence: "98.2%" },
  { step: 2, name: "validate_fields", time: "1.1s", input: "23 extracted fields", output: "All fields valid (23/23)", confidence: null },
  { step: 3, name: "validate_gst_compliance", time: "0.8s", input: "2 HSN codes, 18% rate", output: "GST COMPLIANT", confidence: null },
  { step: 4, name: "verify_gstn", time: "1.5s", input: "27AABCU9603R1ZM", output: "Active, matched to Acme Technologies", confidence: null },
  { step: 5, name: "check_fraud", time: "4.1s", input: "Full invoice data", output: "0 flags, 97% confidence", confidence: "97%" },
  { step: 6, name: "get_buyer_intel", time: "2.3s", input: "GSTIN 29AABCT1234R1ZX", output: "8 invoices, 0% default, 28d avg", confidence: null },
  { step: 7, name: "get_credit_score", time: "1.8s", input: "Buyer PAN", output: "CIBIL 750", confidence: null },
  { step: 8, name: "get_company_info", time: "1.4s", input: "Buyer CIN", output: "Active, 5yr old, ₹2Cr revenue", confidence: null },
  { step: 9, name: "calculate_risk", time: "0.9s", input: "All signals", output: "Risk score: 82 (Low)", confidence: null },
  { step: 10, name: "generate_summary", time: "2.1s", input: "All results", output: "Summary generated", confidence: null },
];

const underwritingSteps = [
  { step: 11, name: "cross_validate_outputs", time: "2.4s", output: "ALL CONSISTENT (0 discrepancies)" },
  { step: 12, name: "underwriting_decision", time: "1.8s", output: "AUTO-APPROVED (Rule 2)" },
  { step: 13, name: "log_decision", time: "0.3s", output: "Decision persisted" },
  { step: 14, name: "mint_nft", time: "4.2s", output: "ASA #12345678 created on Algorand testnet" },
];

export default function AuditTrailPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <Link href={`/invoices/${params.id}`} className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
        ← Back to Invoice INV-2026-001
      </Link>

      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="mt-4 section-title">
        Audit Trail — Agent Reasoning Chain
      </motion.h1>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-6 glass-card p-6">
        {/* Invoice Processing Agent */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/20 border border-blue-500/30 text-lg">🤖</div>
          <div>
            <h2 className="font-semibold text-slate-200">Invoice Processing Agent</h2>
            <p className="text-xs text-slate-500">Sonnet 4.6 · Started: 2026-03-18 10:00:00 · Duration: 1m 12s</p>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          {auditSteps.map((s, i) => (
            <motion.div
              key={s.step}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.04 }}
              className="rounded-lg border border-blue-500/10 bg-slate-800/30 p-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200">
                  <span className="text-blue-400">Step {s.step}:</span> {s.name}
                </span>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">{s.time}</span>
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 text-xs">
                <span className="text-slate-500">Input: <span className="text-slate-400">{s.input}</span></span>
                <span className="text-slate-500">Output: <span className="text-emerald-400">{s.output}</span></span>
                {s.confidence && <span className="text-slate-500">Confidence: <span className="text-blue-400">{s.confidence}</span></span>}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Handoff */}
        <div className="my-6 flex items-center gap-2">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
          <div className="flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5">
            <span className="text-xs">🔄</span>
            <span className="text-xs font-medium text-blue-400">HANDOFF → Underwriting Agent</span>
          </div>
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
        </div>

        {/* Underwriting Agent */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-lg">🤖</div>
          <div>
            <h2 className="font-semibold text-slate-200">Underwriting Agent</h2>
            <p className="text-xs text-slate-500">Sonnet 4.6 · Started: 2026-03-18 10:01:12 · Duration: 0m 30s</p>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          {underwritingSteps.map((s, i) => (
            <motion.div
              key={s.step}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 + i * 0.05 }}
              className="rounded-lg border border-indigo-500/10 bg-slate-800/30 p-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-200">
                  <span className="text-indigo-400">Step {s.step}:</span> {s.name}
                </span>
                <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">{s.time}</span>
              </div>
              <p className="mt-1 text-xs text-emerald-400">{s.output}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
