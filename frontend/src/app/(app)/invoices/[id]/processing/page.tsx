"use client";

import { PROCESSING_STEPS } from "@/lib/constants";
import { motion } from "framer-motion";
import { useProcessing } from "@/hooks/useProcessing";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProcessingPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { currentStep, completedSteps, progress, isComplete, isFailed, finalStatus, liveDetail, elapsedSeconds } = useProcessing(params.id);

  // Redirect to detail page on completion
  useEffect(() => {
    if (isComplete) {
      const timer = setTimeout(() => router.push(`/invoices/${params.id}`), 2000);
      return () => clearTimeout(timer);
    }
  }, [isComplete, params.id, router]);

  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;
  const timeStr = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  return (
    <div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <h1 className="section-title">Processing Invoice</h1>
        <div className="flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-1.5">
          <span className={`h-2 w-2 rounded-full ${isComplete ? "bg-emerald-400" : isFailed ? "bg-red-400" : "bg-blue-400 animate-pulse"}`} />
          <span className="text-sm font-mono text-blue-300">{timeStr}</span>
        </div>
      </motion.div>

      {/* Status banner */}
      {isComplete && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-400 text-center">
          ✅ Processing complete — {finalStatus?.toUpperCase()}. Redirecting...
        </motion.div>
      )}
      {isFailed && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400 text-center">
          ❌ Processing failed. Please try again.
        </motion.div>
      )}

      {/* Progress bar */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-4">
        <div className="flex items-center justify-between text-sm text-slate-400">
          <span>Progress</span>
          <span className="text-blue-400 font-medium">{progress}% ({completedSteps.length}/14 steps)</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={`h-full rounded-full shadow-lg ${
              isComplete ? "bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-emerald-500/30" :
              isFailed ? "bg-gradient-to-r from-red-600 to-red-400 shadow-red-500/30" :
              "bg-gradient-to-r from-blue-600 to-blue-400 shadow-blue-500/30"
            }`}
          />
        </div>
      </motion.div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Agent Pipeline */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
          <h2 className="text-sm font-semibold text-slate-200">Agent Pipeline</h2>
          <div className="mt-4 space-y-2">
            {PROCESSING_STEPS.map((step, i) => {
              const isCompleted = completedSteps.includes(step.step);
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
                      isCompleted ? "bg-emerald-500/5" : "opacity-50"
                    }`}
                  >
                    <span className="text-sm">{isCompleted ? "✅" : isActive ? "🔄" : "⏳"}</span>
                    <div className="flex-1">
                      <p className={`text-xs font-medium ${
                        isCompleted ? "text-slate-300" : isActive ? "text-blue-400" : "text-slate-500"
                      }`}>
                        {step.step}. {step.label}
                      </p>
                      {isActive && <p className="text-[10px] text-blue-400/70 animate-pulse">In progress...</p>}
                    </div>
                    {isCompleted && <span className="text-[10px] text-emerald-400">✓ Done</span>}
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
            {liveDetail ? (
              <>
                <p className="text-sm text-slate-300">
                  Current: <span className="text-blue-400 font-medium">
                    {PROCESSING_STEPS.find((s) => s.step === currentStep)?.label || liveDetail.tool || "Processing"}
                  </span>
                </p>
                {liveDetail.message && (
                  <p className="mt-2 text-sm text-slate-500">{liveDetail.message}</p>
                )}
                {liveDetail.data && (
                  <div className="mt-4 space-y-2">
                    {Object.entries(liveDetail.data).slice(0, 5).map(([key, val]) => (
                      <div key={key} className="flex items-center justify-between rounded-lg bg-slate-800/50 border border-blue-500/10 px-3 py-2">
                        <span className="text-xs text-slate-400">{key.replace(/_/g, " ")}</span>
                        <span className="text-xs font-medium text-blue-300">{String(val)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-8">
                <span className="h-8 w-8 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
                <p className="mt-3 text-sm text-slate-500">Waiting for events...</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
