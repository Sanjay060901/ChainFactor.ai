"use client";

/**
 * Real-time processing page skeleton (STAR SCREEN).
 * TODO: Wire to subscribeToProcessing() SSE client, animate step progression.
 * See wireframes.md Screen 4 for layout reference.
 */

import { PROCESSING_STEPS } from "@/lib/constants";

export default function ProcessingPage({
  params,
}: {
  params: { id: string };
}) {
  // Stub: show steps 1-5 as complete, step 6 in progress, rest pending
  const currentStep = 6;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          Processing Invoice {params.id}
        </h1>
        <span className="text-sm text-gray-500">⏱ 00:47</span>
      </div>

      {/* Progress bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Progress</span>
          <span>{Math.round((currentStep / 14) * 100)}% ({currentStep}/14 steps)</span>
        </div>
        <div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full bg-primary-600 transition-all"
            style={{ width: `${(currentStep / 14) * 100}%` }}
          />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Agent Pipeline */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-gray-900">Agent Pipeline</h2>
          <div className="mt-4 space-y-3">
            {PROCESSING_STEPS.map((step) => {
              const isComplete = step.step < currentStep;
              const isActive = step.step === currentStep;
              const isPending = step.step > currentStep;
              const isHandoff = step.step === 11;

              return (
                <div key={step.step}>
                  {isHandoff && (
                    <div className="my-2 border-t border-dashed border-gray-300 py-1 text-center text-xs text-gray-400">
                      ── Agent Handoff ──
                    </div>
                  )}
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 text-sm">
                      {isComplete ? "✅" : isActive ? "🔄" : "⏳"}
                    </span>
                    <div>
                      <p
                        className={`text-sm font-medium ${
                          isComplete
                            ? "text-gray-900"
                            : isActive
                              ? "text-primary-600"
                              : "text-gray-400"
                        }`}
                      >
                        {step.step}. {step.label}
                      </p>
                      {isActive && (
                        <p className="mt-0.5 text-xs text-primary-500">
                          In progress...
                        </p>
                      )}
                      {isComplete && (
                        <p className="mt-0.5 text-xs text-gray-400">
                          Complete
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Details */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-gray-900">Live Details</h2>
          <div className="mt-4">
            <p className="text-sm text-gray-700">
              Current: <span className="font-medium">Buyer Intelligence</span>
            </p>
            <p className="mt-2 text-sm text-gray-500">
              Analyzing buyer payment history and previous invoice records for
              GSTIN 29AABCT1234R1ZX...
            </p>
            <div className="mt-4 rounded-lg bg-gray-50 p-3">
              <p className="text-xs text-gray-500">
                Previous invoices found: 8
              </p>
              <p className="text-xs text-gray-500">Average payment: 28 days</p>
              <p className="text-xs text-gray-500">Default rate: 0%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
