"use client";

/**
 * Audit trail page skeleton.
 * TODO: Wire to api.getAuditTrail(), display full agent reasoning chain.
 * See wireframes.md Screen 8 for layout reference.
 */

import Link from "next/link";

export default function AuditTrailPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div>
      <Link
        href={`/invoices/${params.id}`}
        className="text-sm text-gray-500 hover:underline"
      >
        ← Back to Invoice INV-2026-001
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-gray-900">
        Audit Trail - Full Agent Reasoning Chain
      </h1>

      <div className="mt-6 rounded-lg bg-white p-6 shadow-sm">
        {/* Invoice Processing Agent */}
        <div>
          <div className="flex items-center gap-2">
            <span>🤖</span>
            <h2 className="font-semibold text-gray-900">
              Invoice Processing Agent (Sonnet 4.6)
            </h2>
          </div>
          <p className="mt-1 text-xs text-gray-400">
            Started: 2026-03-18 10:00:00 &nbsp; Duration: 1m 12s
          </p>

          <div className="mt-4 space-y-3">
            {[
              { step: 1, name: "extract_invoice", time: "3.2s", input: "invoice_march_2026.pdf (1.2 MB)", output: "23 fields extracted, 2 line items", confidence: "98.2%" },
              { step: 2, name: "validate_fields", time: "1.1s", input: "23 extracted fields", output: "All fields valid (23/23)", confidence: null },
              { step: 3, name: "validate_gst_compliance", time: "0.8s", input: "2 HSN codes, 18% rate", output: "GST COMPLIANT", confidence: null },
            ].map((s) => (
              <div
                key={s.step}
                className="rounded-lg border border-gray-200 p-4"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">
                    Step {s.step}: {s.name}
                  </span>
                  <span className="text-xs text-gray-400">{s.time}</span>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Input: {s.input}
                </p>
                <p className="text-xs text-gray-500">Output: {s.output}</p>
                {s.confidence && (
                  <p className="text-xs text-gray-500">
                    Confidence: {s.confidence}
                  </p>
                )}
              </div>
            ))}
            <p className="text-sm text-gray-400">... (Steps 4-10 same format)</p>
          </div>
        </div>

        {/* Handoff */}
        <div className="my-6 border-t border-dashed border-gray-300 py-3 text-center">
          <p className="text-sm text-gray-500">
            ── HANDOFF → Underwriting Agent ──
          </p>
          <p className="text-xs text-gray-400">
            Context: extracted_data, risk_score, fraud_result, gst_compliance,
            gstin_status, credit_score, company_info
          </p>
        </div>

        {/* Underwriting Agent */}
        <div>
          <div className="flex items-center gap-2">
            <span>🤖</span>
            <h2 className="font-semibold text-gray-900">
              Underwriting Agent (Sonnet 4.6)
            </h2>
          </div>
          <p className="mt-1 text-xs text-gray-400">
            Started: 2026-03-18 10:01:12 &nbsp; Duration: 0m 30s
          </p>

          <div className="mt-4 space-y-3">
            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  Step 11: cross_validate_outputs
                </span>
                <span className="text-xs text-gray-400">2.4s</span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Result: ALL CONSISTENT (0 discrepancies)
              </p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  Step 12: underwriting_decision
                </span>
                <span className="text-xs text-gray-400">1.8s</span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Decision: AUTO-APPROVED (Rule 2)
              </p>
              <p className="text-xs text-gray-500">
                Reasoning: Invoice meets Rule 2 criteria. Risk score of 82
                exceeds threshold of 80.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
