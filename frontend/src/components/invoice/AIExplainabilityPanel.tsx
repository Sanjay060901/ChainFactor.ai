"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  riskScore: number;
  fraudDetection: any;
  gstCompliance: any;
  gstnVerification: any;
  buyerIntel: any;
  creditScore: any;
  companyInfo: any;
  underwriting: any;
  delay?: number;
}

interface SignalItem {
  label: string;
  weight: string;
  score: number;
  maxScore: number;
  status: "pass" | "warning" | "fail";
  detail: string;
  icon: string;
}

function computeSignals(props: Props): SignalItem[] {
  const signals: SignalItem[] = [];

  // 1. Fraud Detection (30% weight)
  const fraudOverall = String(props.fraudDetection?.overall || "pass").toLowerCase();
  const fraudConf = props.fraudDetection?.confidence || 0;
  signals.push({
    label: "Fraud Detection",
    weight: "30%",
    score: fraudOverall === "pass" ? 30 : fraudOverall === "warning" ? 19 : 7,
    maxScore: 30,
    status: fraudOverall === "pass" ? "pass" : fraudOverall === "warning" ? "warning" : "fail",
    detail: fraudOverall === "pass"
      ? `All 5 layers passed (${fraudConf}% confidence)`
      : `Fraud ${fraudOverall} detected — ${(props.fraudDetection?.flags || []).join(", ") || "review recommended"}`,
    icon: "🛡️",
  });

  // 2. Field Validation (15% weight)
  const gstOk = props.gstCompliance?.is_compliant !== false;
  signals.push({
    label: "GST Compliance",
    weight: "15%",
    score: gstOk ? 15 : 4,
    maxScore: 15,
    status: gstOk ? "pass" : "fail",
    detail: gstOk ? "HSN codes valid, tax rates match, e-invoice compliant" : "GST non-compliance detected",
    icon: "📋",
  });

  // 3. GSTIN Verification (15% weight — merged with validation)
  const gstnOk = props.gstnVerification?.verified !== false;
  signals.push({
    label: "GSTIN Verification",
    weight: "15%",
    score: gstnOk ? 15 : 4,
    maxScore: 15,
    status: gstnOk ? "pass" : "fail",
    detail: gstnOk
      ? `Status: ${props.gstnVerification?.status || "Active"} — ${props.gstnVerification?.details?.legal_name || "Verified entity"}`
      : "GSTIN could not be verified",
    icon: "🔒",
  });

  // 4. Credit Score (20% weight)
  const cScore = props.creditScore?.score || 0;
  const creditPenalty = cScore >= 750 ? 17 : cScore >= 650 ? 13 : cScore >= 580 ? 8 : 3;
  signals.push({
    label: "CIBIL Credit Score",
    weight: "20%",
    score: creditPenalty,
    maxScore: 20,
    status: cScore >= 700 ? "pass" : cScore >= 580 ? "warning" : "fail",
    detail: `Score: ${cScore} (${props.creditScore?.rating || "unknown"})`,
    icon: "💳",
  });

  // 5. Buyer Intel (10% weight)
  const history = String(props.buyerIntel?.payment_history || "reliable").toLowerCase();
  signals.push({
    label: "Buyer Payment History",
    weight: "10%",
    score: history === "reliable" || history === "good" ? 10 : history === "new_buyer" ? 5 : 2,
    maxScore: 10,
    status: history === "reliable" || history === "good" ? "pass" : history === "new_buyer" ? "warning" : "fail",
    detail: history === "reliable" || history === "good"
      ? `Good history: avg ${props.buyerIntel?.avg_days || 0} days, ${props.buyerIntel?.previous_count || 0} past invoices`
      : history === "new_buyer"
      ? "New buyer with no payment history"
      : `Slow payer: avg ${props.buyerIntel?.avg_days || 0} days`,
    icon: "📊",
  });

  // 6. Company Status (10% weight)
  const coStatus = String(props.companyInfo?.status || "active").toLowerCase();
  signals.push({
    label: "Company Status (MCA)",
    weight: "10%",
    score: coStatus === "active" ? 10 : 2,
    maxScore: 10,
    status: coStatus === "active" ? "pass" : "fail",
    detail: coStatus === "active"
      ? `Active since ${props.companyInfo?.incorporated || "N/A"}, paid-up capital ₹${Math.round(Number(props.companyInfo?.paid_up_capital || 0)).toLocaleString("en-IN")}`
      : "Company is dormant or inactive",
    icon: "🏢",
  });

  return signals;
}

const statusColors = {
  pass: { bg: "bg-emerald-500/10", border: "border-emerald-500/20", text: "text-emerald-400", bar: "bg-emerald-500" },
  warning: { bg: "bg-yellow-500/10", border: "border-yellow-500/20", text: "text-yellow-400", bar: "bg-yellow-500" },
  fail: { bg: "bg-red-500/10", border: "border-red-500/20", text: "text-red-400", bar: "bg-red-500" },
};

export default function AIExplainabilityPanel(props: Props) {
  const [expanded, setExpanded] = useState(false);
  const signals = computeSignals(props);
  const totalScore = signals.reduce((sum, s) => sum + s.score, 0);
  const decision = props.underwriting?.decision || "unknown";

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: props.delay || 0.85 }}
      className="mt-4 glass-card overflow-hidden"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🧠</span>
          <div className="text-left">
            <h3 className="text-sm font-semibold text-slate-200">AI Decision Explainability</h3>
            <p className="text-xs text-slate-500">
              See exactly why the AI {decision === "approved" ? "approved" : decision === "rejected" ? "rejected" : "flagged"} this invoice — signal-by-signal breakdown
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <span className="text-lg font-bold text-slate-200">{totalScore}</span>
            <span className="text-xs text-slate-500">/100</span>
          </div>
          <motion.span
            animate={{ rotate: expanded ? 180 : 0 }}
            className="text-slate-400 text-sm"
          >
            ▼
          </motion.span>
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="border-t border-slate-800 px-6 pb-6 pt-4">
              {/* Decision Summary Bar */}
              <div className={`rounded-lg p-4 mb-4 ${
                decision === "approved" ? "bg-emerald-500/5 border border-emerald-500/10" :
                decision === "rejected" ? "bg-red-500/5 border border-red-500/10" :
                "bg-yellow-500/5 border border-yellow-500/10"
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-300">
                    {decision === "approved" ? "✅ Auto-Approved" : decision === "rejected" ? "❌ Rejected" : "⚠️ Flagged for Review"}
                  </span>
                  <span className="text-xs text-slate-500">{props.underwriting?.rule_matched || ""}</span>
                </div>
                {props.underwriting?.reasoning && (
                  <p className="mt-2 text-xs text-slate-400">{props.underwriting.reasoning}</p>
                )}
              </div>

              {/* Signal Breakdown */}
              <div className="space-y-3">
                {signals.map((signal, i) => {
                  const colors = statusColors[signal.status];
                  const pct = Math.round((signal.score / signal.maxScore) * 100);
                  return (
                    <motion.div
                      key={signal.label}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className={`rounded-lg border ${colors.border} ${colors.bg} p-4`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{signal.icon}</span>
                          <span className="text-sm font-medium text-slate-200">{signal.label}</span>
                          <span className="text-[10px] text-slate-600 border border-slate-700 rounded px-1">Weight: {signal.weight}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-bold ${colors.text}`}>{signal.score}/{signal.maxScore}</span>
                          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                            signal.status === "pass" ? "bg-emerald-500/20 text-emerald-400" :
                            signal.status === "warning" ? "bg-yellow-500/20 text-yellow-400" :
                            "bg-red-500/20 text-red-400"
                          }`}>
                            {signal.status === "pass" ? "PASS" : signal.status === "warning" ? "WARN" : "FAIL"}
                          </span>
                        </div>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-slate-800">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ delay: 0.2 + i * 0.05, duration: 0.5 }}
                          className={`h-1.5 rounded-full ${colors.bar}`}
                        />
                      </div>
                      <p className="mt-2 text-xs text-slate-400">{signal.detail}</p>
                    </motion.div>
                  );
                })}
              </div>

              {/* Cross-validation */}
              {props.underwriting?.cross_validation && (
                <div className="mt-4 rounded-lg bg-blue-500/5 border border-blue-500/10 p-3">
                  <p className="text-xs text-slate-400">
                    <span className="font-medium text-blue-400">Cross-validation:</span>{" "}
                    {props.underwriting.cross_validation === "passed"
                      ? "All tool outputs are internally consistent. No discrepancies found."
                      : `Status: ${props.underwriting.cross_validation}`}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
