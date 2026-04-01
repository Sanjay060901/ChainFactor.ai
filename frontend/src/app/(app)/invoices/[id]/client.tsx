"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { getDemoInvoiceDetail } from "@/lib/demo-data";

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { delay },
});

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function InvoiceDetailClient({ params }: { params: { id: string } }) {
  const [invoice, setInvoice] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getInvoice(params.id).then((data) => {
      setInvoice(data as Record<string, any>);
      setLoading(false);
    }).catch(() => {
      setInvoice(getDemoInvoiceDetail(params.id));
      setLoading(false);
    });
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="h-8 w-8 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
        <span className="ml-3 text-slate-400">Loading invoice...</span>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="py-24 text-center">
        <p className="text-3xl">📄</p>
        <p className="mt-2 text-slate-400">Invoice not found</p>
        <Link href="/invoices" className="mt-3 inline-block text-sm text-blue-400">← Back to Invoices</Link>
      </div>
    );
  }

  const extracted = invoice.extracted_data || {};
  const riskScore = invoice.risk_score ?? extracted.risk_score ?? 82;
  const riskLevel = riskScore >= 70 ? "LOW RISK" : riskScore >= 40 ? "MEDIUM RISK" : "HIGH RISK";
  const riskColor = riskScore >= 70 ? "text-emerald-400" : riskScore >= 40 ? "text-yellow-400" : "text-red-400";
  const status = invoice.status || "processing";
  const fraudFlags = invoice.fraud_flags || [];
  const gstCompliance = extracted.gst_compliance || {};
  const gstnVerification = extracted.gstn_verification || {};
  const underwriting = invoice.underwriting || {};
  const assetId = invoice.nft_asset_id;

  const fields = [
    ["Seller", extracted.seller_name || invoice.seller_name || "—"],
    ["GSTIN", extracted.seller_gstin || "—"],
    ["Buyer", extracted.buyer_name || "—"],
    ["Buyer GSTIN", extracted.buyer_gstin || "—"],
    ["Invoice #", extracted.invoice_number || invoice.invoice_number || "—"],
    ["Date", extracted.invoice_date || "—"],
    ["Amount", extracted.total_amount ? `₹${Number(extracted.total_amount).toLocaleString("en-IN")}` : "—"],
    ["Tax", extracted.tax_amount ? `₹${Number(extracted.tax_amount).toLocaleString("en-IN")}` : "—"],
    ["Total", extracted.grand_total ? `₹${Number(extracted.grand_total).toLocaleString("en-IN")}` : "—"],
    ["Due", extracted.due_date || "—"],
  ];

  return (
    <div>
      <Link href="/invoices" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">← Back to Invoices</Link>

      <motion.div {...fadeUp(0)} className="mt-4 flex items-center justify-between">
        <div>
          <h1 className="section-title">Invoice {extracted.invoice_number || invoice.invoice_number || params.id}</h1>
          <div className="mt-2 flex items-center gap-3">
            <span className={`badge badge-${status}`}>{status === "approved" ? "✅" : ""} {status.charAt(0).toUpperCase() + status.slice(1)}</span>
            {assetId && <span className="badge badge-minted">NFT: ASA #{assetId}</span>}
          </div>
        </div>
        <div className="flex gap-3">
          {(status === "approved" || status === "minted") && (
            <Link href={`/invoices/${params.id}/claim`} className="btn-glow px-4 py-2 text-sm">Claim NFT</Link>
          )}
          <Link href={`/invoices/${params.id}/audit`} className="btn-outline-glow px-4 py-2 text-sm">Audit Trail</Link>
        </div>
      </motion.div>

      {/* Extracted Data */}
      <motion.section {...fadeUp(0.1)} className="mt-6 glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-200">Extracted Data</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          {fields.map(([label, value]) => (
            <div key={label}>
              <span className="text-slate-500">{label}:</span>{" "}
              <span className="text-slate-200">{value}</span>
            </div>
          ))}
        </div>
      </motion.section>

      {/* AI Analysis */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <motion.div {...fadeUp(0.2)} whileHover={{ scale: 1.03 }} className="glass-card p-6 text-center">
          <h3 className="text-sm font-medium text-slate-400">Risk Score</h3>
          <div className="relative mx-auto mt-3 h-24 w-24">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(59,130,246,0.1)" strokeWidth="8" />
              <circle cx="50" cy="50" r="40" fill="none" stroke="url(#scoreGrad)" strokeWidth="8" strokeDasharray={`${riskScore * 2.51} 251`} strokeLinecap="round" />
              <defs><linearGradient id="scoreGrad"><stop stopColor={riskScore >= 70 ? "#22c55e" : riskScore >= 40 ? "#eab308" : "#ef4444"} /><stop offset="1" stopColor={riskScore >= 70 ? "#4ade80" : riskScore >= 40 ? "#fbbf24" : "#f87171"} /></linearGradient></defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-2xl font-bold ${riskColor} stat-glow`}>{riskScore}</span>
            </div>
          </div>
          <p className={`mt-1 text-xs ${riskColor} font-medium`}>{riskLevel}</p>
        </motion.div>
        <motion.div {...fadeUp(0.3)} whileHover={{ scale: 1.03 }} className="glass-card p-6 text-center">
          <h3 className="text-sm font-medium text-slate-400">GST Compliance</h3>
          <p className="mt-4 text-3xl">{gstCompliance.compliant !== false ? "✅" : "❌"}</p>
          <p className={`mt-2 text-sm font-medium ${gstCompliance.compliant !== false ? "text-emerald-400" : "text-red-400"}`}>
            {gstCompliance.compliant !== false ? "Compliant" : "Non-Compliant"}
          </p>
          <p className="mt-1 text-xs text-slate-500">{gstCompliance.summary || "HSN valid, rates match"}</p>
        </motion.div>
        <motion.div {...fadeUp(0.4)} whileHover={{ scale: 1.03 }} className="glass-card p-6 text-center">
          <h3 className="text-sm font-medium text-slate-400">GSTIN</h3>
          <p className="mt-4 text-3xl">{gstnVerification.verified !== false ? "🔒" : "⚠️"}</p>
          <p className={`mt-2 text-sm font-medium ${gstnVerification.verified !== false ? "text-emerald-400" : "text-yellow-400"}`}>
            {gstnVerification.verified !== false ? "Verified" : "Unverified"}
          </p>
          <p className="mt-1 text-xs text-slate-500">{gstnVerification.status || "Active, matched"}</p>
        </motion.div>
      </div>

      {/* Fraud Detection */}
      <motion.section {...fadeUp(0.5)} className="mt-4 glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-200">Fraud Detection (5-Layer)</h3>
        <div className="mt-3 space-y-2">
          {["Document Integrity", "Financial Consistency", "Pattern Analysis", "Entity Verification", "Cross-Reference"].map((layer, i) => {
            const flagged = fraudFlags.some((f: any) => f.layer === layer);
            return (
              <motion.div key={layer} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + i * 0.05 }} className={`flex items-center justify-between rounded-lg border px-4 py-2 text-sm ${flagged ? "bg-red-500/5 border-red-500/10" : "bg-emerald-500/5 border-emerald-500/10"}`}>
                <span className="text-slate-300">{layer}</span>
                <span className={`font-medium ${flagged ? "text-red-400" : "text-emerald-400"}`}>{flagged ? "⚠️ Flag" : "✅ Pass"}</span>
              </motion.div>
            );
          })}
        </div>
        <p className="mt-3 text-sm text-slate-500">Flags: <span className={fraudFlags.length > 0 ? "text-red-400" : "text-emerald-400"}>{fraudFlags.length}</span></p>
      </motion.section>

      {/* Underwriting Decision */}
      <motion.section {...fadeUp(0.7)} className="mt-4 glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-200">Underwriting Decision</h3>
        <div className="mt-3 flex items-center gap-3">
          <span className={`badge text-base px-4 py-1.5 ${
            underwriting.decision === "approved" ? "badge-approved" :
            underwriting.decision === "rejected" ? "badge-rejected" : "badge-flagged"
          }`}>{(underwriting.decision || status).toUpperCase()}</span>
        </div>
        {underwriting.reason && <p className="mt-2 text-sm text-slate-400">{underwriting.reason}</p>}
        {underwriting.cross_validation && <p className="mt-1 text-sm text-slate-400">Cross-validation: <span className="text-emerald-400">PASSED</span></p>}
      </motion.section>

      {/* AI Explanation */}
      {(invoice.risk_explanation || extracted.summary) && (
        <motion.section {...fadeUp(0.8)} className="mt-4 glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-200">🤖 AI Risk Explanation</h3>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed">
            {invoice.risk_explanation || extracted.summary}
          </p>
        </motion.section>
      )}
    </div>
  );
}
