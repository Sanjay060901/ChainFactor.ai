"use client";

import { PROCESSING_STEPS } from "@/lib/constants";
import { motion } from "framer-motion";

export default function ProcessingPage({ params }: { params: { id: string } }) {
  const currentStep = 6;
  const progress = Math.round((currentStep / 14) * 100);

  return (
    <div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <h1 className="section-title">Processing Invoice</h1>
        <div className="flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-1.5">
          <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
          <span className="text-sm font-mono text-blue-300">00:47</span>
        </div>
      </motion.div>

      {/* Progress bar */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-4">
        <div className="flex items-center justify-between text-sm text-slate-400">
          <span>Progress</span>
          <span className="text-blue-400 font-medium">{progress}% ({currentStep}/14 steps)</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 shadow-lg shadow-blue-500/30"
          />
        </div>
      </motion.div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Agent Pipeline */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
          <h2 className="text-sm font-semibold text-slate-200">Agent Pipeline</h2>
          <div className="mt-4 space-y-2">
            {PROCESSING_STEPS.map((step, i) => {
              const isComplete = step.step < currentStep;
              const isActive = step.step === currentStep;
              const isHandoff = step.step === 11;

              return (
                <div key={step.step}>
                  {isHandoff && (
                    <div className="my-3 flex items-center gap-2">
                      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
                      <span className="text-[10px] font-medium uppercase tracking-wider text-blue-400">Agent Handoff</span>
                      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
                    </div>
                  )}
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + i * 0.03 }}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
                      isActive ? "bg-blue-500/10 border border-blue-500/30" :
                      isComplete ? "bg-emerald-500/5" : "opacity-50"
                    }`}
                  >
                    <span className="text-sm">{isComplete ? "✅" : isActive ? "🔄" : "⏳"}</span>
                    <div className="flex-1">
                      <p className={`text-xs font-medium ${
                        isComplete ? "text-slate-300" : isActive ? "text-blue-400" : "text-slate-500"
                      }`}>
                        {step.step}. {step.label}
                      </p>
                      {isActive && <p className="text-[10px] text-blue-400/70 animate-pulse">In progress...</p>}
                    </div>
                    {isComplete && <span className="text-[10px] text-slate-600">Done</span>}
                  </motion.div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Live Details */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6">
          <h2 className="text-sm font-semibold text-slate-200">Live Details</h2>
          <div className="mt-4">
            <p className="text-sm text-slate-300">Current: <span className="text-blue-400 font-medium">Buyer Intelligence</span></p>
            <p className="mt-2 text-sm text-slate-500">Analyzing buyer payment history and previous invoice records for GSTIN 29AABCT1234R1ZX...</p>
            <div className="mt-4 space-y-2">
              {[
                { label: "Previous invoices found", value: "8" },
                { label: "Average payment", value: "28 days" },
                { label: "Default rate", value: "0%" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-lg bg-slate-800/50 border border-blue-500/10 px-3 py-2">
                  <span className="text-xs text-slate-400">{item.label}</span>
                  <span className="text-xs font-medium text-blue-300">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
