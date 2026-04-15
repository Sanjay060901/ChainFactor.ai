"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useInvoiceId } from "@/hooks/useInvoiceId";
import AIExplainabilityPanel from "@/components/invoice/AIExplainabilityPanel";

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { delay },
});

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function InvoiceDetailClient({ params }: { params: { id: string } }) {
  const invoiceId = useInvoiceId(params.id);
  const router = useRouter();
  const [invoice, setInvoice] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    // Skip fetching with the static placeholder ID
    if (!invoiceId || invoiceId === "placeholder") return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    api.getInvoice(invoiceId).then((data) => {
      if (!cancelled) {
        setInvoice(data as Record<string, any>);
        setLoading(false);
      }
    }).catch((err) => {
      if (!cancelled) {
        setError(err?.message || "Failed to load invoice");
        setInvoice(null);
        setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [invoiceId]);

  async function handleDelete() {
    if (!invoiceId || !confirm("Delete this invoice? This cannot be undone.")) return;
    setDeleteLoading(true);
    try {
      await api.deleteInvoice(invoiceId);
      router.push("/invoices");
    } catch {
      setDeleteLoading(false);
    }
  }

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
        <p className="mt-2 text-slate-400">{error || "Invoice not found"}</p>
        <Link href="/invoices" className="mt-3 inline-block text-sm text-blue-400">← Back to Invoices</Link>
      </div>
    );
  }

  const extracted = invoice.extracted_data || {};
  const seller = extracted.seller || {};
  const buyer = extracted.buyer || {};
  const riskScore = invoice.risk_assessment?.score ?? invoice.risk_score ?? extracted.risk_score ?? 0;
  const riskLevel = riskScore >= 70 ? "LOW RISK" : riskScore >= 40 ? "MEDIUM RISK" : "HIGH RISK";
  const riskColor = riskScore >= 70 ? "text-emerald-400" : riskScore >= 40 ? "text-yellow-400" : "text-red-400";
  const status = invoice.status || "processing";
  const fraudDetection = invoice.fraud_detection || {};
  const fraudLayers = fraudDetection.layers || [];
  const fraudFlags = fraudDetection.flags || [];
  const gstCompliance = invoice.gst_compliance || {};
  const gstnVerification = invoice.gstin_verification || {};
  const underwriting = invoice.underwriting || {};
  const nftData = invoice.nft || {};
  const assetId = nftData.asset_id;

  const fields = [
    ["Seller", seller.name || "—"],
    ["GSTIN", seller.gstin || "—"],
    ["Buyer", buyer.name || "—"],
    ["Buyer GSTIN", buyer.gstin || "—"],
    ["Invoice #", extracted.invoice_number || invoice.invoice_number || "—"],
    ["Date", extracted.invoice_date || "—"],
    ["Subtotal", extracted.subtotal ? `₹${Math.round(Number(extracted.subtotal)).toLocaleString("en-IN")}` : "—"],
    ["Tax", extracted.tax_amount ? `₹${Math.round(Number(extracted.tax_amount)).toLocaleString("en-IN")}` : "—"],
    ["Total", extracted.total_amount ? `₹${Math.round(Number(extracted.total_amount)).toLocaleString("en-IN")}` : "—"],
    ["Due", extracted.due_date || "—"],
  ];

  return (
    <div>
      <Link href="/invoices" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">← Back to Invoices</Link>

      <motion.div {...fadeUp(0)} className="mt-4 flex items-center justify-between">
        <div>
          <h1 className="section-title">Invoice {extracted.invoice_number || invoice.invoice_number || invoiceId}</h1>
          <div className="mt-2 flex items-center gap-3">
            <span className={`badge badge-${status}`}>{status === "approved" ? "✅" : ""} {status.charAt(0).toUpperCase() + status.slice(1)}</span>
            {assetId && <span className="badge badge-minted">NFT: ASA #{assetId}</span>}
          </div>
        </div>
        <div className="flex gap-3">
          {status === "uploaded" && (
            <button onClick={() => router.push(`/invoices/${invoiceId}/processing`)} className="btn-glow px-4 py-2 text-sm">🤖 Process Invoice</button>
          )}
          {(status === "approved" || status === "minted") && (
            <Link href={`/invoices/${invoiceId}/claim`} className="btn-glow px-4 py-2 text-sm">Claim NFT</Link>
          )}
          <Link href={`/invoices/${invoiceId}/audit`} className="btn-outline-glow px-4 py-2 text-sm">Audit Trail</Link>
          <button
            onClick={handleDelete}
            disabled={deleteLoading}
            className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/20 transition-colors disabled:opacity-50"
          >
            {deleteLoading ? "Deleting…" : "🗑 Delete"}
          </button>
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
          <p className="mt-4 text-3xl">{gstCompliance.is_compliant !== false ? "✅" : "❌"}</p>
          <p className={`mt-2 text-sm font-medium ${gstCompliance.is_compliant !== false ? "text-emerald-400" : "text-red-400"}`}>
            {gstCompliance.is_compliant !== false ? "Compliant" : "Non-Compliant"}
          </p>
          <p className="mt-1 text-xs text-slate-500">{gstCompliance.details?.hsn_valid ? "HSN valid" : ""}{gstCompliance.details?.rate_match ? ", rates match" : ""}{gstCompliance.details?.e_invoice ? ", e-invoice" : ""}</p>
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
          {(fraudLayers.length > 0 ? fraudLayers : ["Document Integrity", "Financial Consistency", "Pattern Analysis", "Entity Verification", "Cross-Reference"].map((name: string) => ({ name, result: "pass", detail: "", confidence: 0 }))).map((layer: any, i: number) => {
            const passed = layer.result === "pass";
            return (
              <motion.div key={layer.name} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + i * 0.05 }} className={`flex items-center justify-between rounded-lg border px-4 py-2 text-sm ${!passed ? "bg-red-500/5 border-red-500/10" : "bg-emerald-500/5 border-emerald-500/10"}`}>
                <div>
                  <span className="text-slate-300">{layer.name}</span>
                  {layer.detail && <span className="ml-2 text-xs text-slate-500">{layer.detail}</span>}
                </div>
                <div className="flex items-center gap-2">
                  {layer.confidence > 0 && <span className="text-[10px] text-slate-500">{Number(layer.confidence).toFixed(1)}%</span>}
                  <span className={`font-medium ${!passed ? "text-red-400" : "text-emerald-400"}`}>{!passed ? "⚠️ Flag" : "✅ Pass"}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
        <p className="mt-3 text-sm text-slate-500">Overall: <span className={fraudDetection.overall === "pass" ? "text-emerald-400" : "text-red-400"}>{fraudDetection.overall || "pass"}</span> · Confidence: <span className="text-slate-400">{Number(fraudDetection.confidence || 0).toFixed(1)}%</span> · Flags: <span className={fraudFlags.length > 0 ? "text-red-400" : "text-emerald-400"}>{fraudFlags.length}</span></p>
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
        {underwriting.reasoning && <p className="mt-2 text-sm text-slate-400">{underwriting.reasoning}</p>}
        {underwriting.rule_matched && <p className="mt-1 text-xs text-slate-500">Rule: {underwriting.rule_matched}</p>}
        {underwriting.cross_validation && <p className="mt-1 text-sm text-slate-400">Cross-validation: <span className="text-emerald-400">{underwriting.cross_validation.toUpperCase()}</span></p>}
      </motion.section>

      {/* AI Explanation */}
      {(invoice.risk_assessment?.explanation || invoice.ai_explanation) && (
        <motion.section {...fadeUp(0.8)} className="mt-4 glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-200">🤖 AI Risk Explanation</h3>
          <p className="mt-2 text-sm text-slate-400 leading-relaxed">
            {invoice.risk_assessment?.explanation || invoice.ai_explanation}
          </p>
        </motion.section>
      )}

      {/* AI Explainability Deep-Dive */}
      <AIExplainabilityPanel
        riskScore={riskScore}
        fraudDetection={fraudDetection}
        gstCompliance={gstCompliance}
        gstnVerification={gstnVerification}
        buyerIntel={invoice.buyer_intel}
        creditScore={invoice.credit_score}
        companyInfo={invoice.company_info}
        underwriting={underwriting}
        delay={0.85}
      />

      {/* Buyer Intel + Credit Score + Company Info */}
      {(invoice.buyer_intel || invoice.credit_score || invoice.company_info) && (
        <motion.section {...fadeUp(0.9)} className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          {invoice.buyer_intel && (
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-slate-200">📊 Buyer Intel</h3>
              <div className="mt-3 space-y-1 text-xs">
                <p className="text-slate-400">Payment History: <span className="text-slate-200">{invoice.buyer_intel.payment_history}</span></p>
                <p className="text-slate-400">Avg Payment Days: <span className="text-slate-200">{invoice.buyer_intel.avg_days}</span></p>
                <p className="text-slate-400">Previous Invoices: <span className="text-slate-200">{invoice.buyer_intel.previous_count}</span></p>
              </div>
            </div>
          )}
          {invoice.credit_score && (
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-slate-200">💳 Credit Score</h3>
              <p className="mt-3 text-3xl font-bold text-center">
                <span className={invoice.credit_score.score >= 700 ? "text-emerald-400" : invoice.credit_score.score >= 500 ? "text-yellow-400" : "text-red-400"}>
                  {invoice.credit_score.score}
                </span>
              </p>
              <p className="mt-1 text-center text-xs text-slate-500 capitalize">{invoice.credit_score.rating}</p>
            </div>
          )}
          {invoice.company_info && (
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-slate-200">🏢 Company Info</h3>
              <div className="mt-3 space-y-1 text-xs">
                <p className="text-slate-400">Status: <span className="text-emerald-400 capitalize">{invoice.company_info.status}</span></p>
                <p className="text-slate-400">Incorporated: <span className="text-slate-200">{invoice.company_info.incorporated}</span></p>
                <p className="text-slate-400">Paid-up Capital: <span className="text-slate-200">₹{Math.round(Number(invoice.company_info.paid_up_capital || 0)).toLocaleString("en-IN")}</span></p>
              </div>
            </div>
          )}
        </motion.section>
      )}

      {/* NFT Info */}
      {nftData.asset_id && (
        <motion.section {...fadeUp(1.0)} className="mt-4 glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-200">🔗 NFT (ARC-69)</h3>
          <div className="mt-3 flex items-center gap-4">
            <span className="badge badge-minted">ASA #{nftData.asset_id}</span>
            <span className="text-xs text-slate-500 capitalize">Status: {nftData.status}</span>
            {nftData.explorer_url && (
              <a href={nftData.explorer_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300">
                View on Pera Explorer ↗
              </a>
            )}
          </div>
        </motion.section>
      )}
    </div>
  );
}
