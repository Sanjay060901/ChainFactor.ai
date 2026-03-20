"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const fadeUp = (delay: number) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { delay },
});

export default function InvoiceDetailPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <Link href="/invoices" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">← Back to Invoices</Link>

      <motion.div {...fadeUp(0)} className="mt-4 flex items-center justify-between">
        <div>
          <h1 className="section-title">Invoice INV-2026-001</h1>
          <div className="mt-2 flex items-center gap-3">
            <span className="badge badge-approved">✅ Approved</span>
            <span className="badge badge-minted">NFT: ASA #12345678</span>
          </div>
        </div>
        <div className="flex gap-3">
          <Link href={`/invoices/${params.id}/claim`} className="btn-glow px-4 py-2 text-sm">Claim NFT</Link>
          <Link href={`/invoices/${params.id}/audit`} className="btn-outline-glow px-4 py-2 text-sm">Audit Trail</Link>
        </div>
      </motion.div>

      {/* Extracted Data */}
      <motion.section {...fadeUp(0.1)} className="mt-6 glass-card p-6">
        <h2 className="text-lg font-semibold text-slate-200">Extracted Data</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          {[
            ["Seller", "Acme Technologies Pvt Ltd"],
            ["GSTIN", "27AABCU9603R1ZM"],
            ["Buyer", "TechBuild Solutions"],
            ["Buyer GSTIN", "29AABCT1234R1ZX"],
            ["Invoice #", "INV-2026-001"],
            ["Date", "2026-03-15"],
            ["Amount", "₹5,20,000"],
            ["Tax", "₹93,600 (18% GST)"],
            ["Total", "₹6,13,600"],
            ["Due", "2026-04-14"],
          ].map(([label, value]) => (
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
              <circle cx="50" cy="50" r="40" fill="none" stroke="url(#scoreGrad)" strokeWidth="8" strokeDasharray={`${82 * 2.51} 251`} strokeLinecap="round" />
              <defs><linearGradient id="scoreGrad"><stop stopColor="#22c55e" /><stop offset="1" stopColor="#4ade80" /></linearGradient></defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-emerald-400 stat-glow">82</span>
            </div>
          </div>
          <p className="mt-1 text-xs text-emerald-400 font-medium">LOW RISK</p>
        </motion.div>
        <motion.div {...fadeUp(0.3)} whileHover={{ scale: 1.03 }} className="glass-card p-6 text-center">
          <h3 className="text-sm font-medium text-slate-400">GST Compliance</h3>
          <p className="mt-4 text-3xl">✅</p>
          <p className="mt-2 text-sm font-medium text-emerald-400">Compliant</p>
          <p className="mt-1 text-xs text-slate-500">HSN valid, rates match, e-invoice present</p>
        </motion.div>
        <motion.div {...fadeUp(0.4)} whileHover={{ scale: 1.03 }} className="glass-card p-6 text-center">
          <h3 className="text-sm font-medium text-slate-400">GSTIN</h3>
          <p className="mt-4 text-3xl">🔒</p>
          <p className="mt-2 text-sm font-medium text-emerald-400">Verified</p>
          <p className="mt-1 text-xs text-slate-500">Active, matched to Acme Technologies</p>
        </motion.div>
      </div>

      {/* Fraud Detection */}
      <motion.section {...fadeUp(0.5)} className="mt-4 glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-200">Fraud Detection (5-Layer)</h3>
        <div className="mt-3 space-y-2">
          {["Document Integrity", "Financial Consistency", "Pattern Analysis", "Entity Verification", "Cross-Reference"].map((layer, i) => (
            <motion.div key={layer} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 + i * 0.05 }} className="flex items-center justify-between rounded-lg bg-emerald-500/5 border border-emerald-500/10 px-4 py-2 text-sm">
              <span className="text-slate-300">{layer}</span>
              <span className="text-emerald-400 font-medium">✅ Pass</span>
            </motion.div>
          ))}
        </div>
        <p className="mt-3 text-sm text-slate-500">Flags: <span className="text-emerald-400">0</span> · Confidence: <span className="text-emerald-400">97%</span></p>
      </motion.section>

      {/* Underwriting Decision */}
      <motion.section {...fadeUp(0.7)} className="mt-4 glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-200">Underwriting Decision</h3>
        <div className="mt-3 flex items-center gap-3">
          <span className="badge badge-approved text-base px-4 py-1.5">AUTO-APPROVED</span>
        </div>
        <p className="mt-2 text-sm text-slate-400">Rule matched: &quot;Approve invoices under ₹10L with risk score &gt; 80&quot;</p>
        <p className="mt-1 text-sm text-slate-400">Cross-validation: <span className="text-emerald-400">PASSED</span></p>
      </motion.section>

      {/* AI Explanation */}
      <motion.section {...fadeUp(0.8)} className="mt-4 glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-200">🤖 AI Risk Explanation</h3>
        <p className="mt-2 text-sm text-slate-400 leading-relaxed">
          This invoice presents low risk. The seller has an active GSTIN with consistent filing history.
          The buyer has a CIBIL score of 750 and has paid all 8 previous invoices on time. GST rates
          match the applicable slab for HSN 998314. No fraud indicators detected across all 5 layers.
        </p>
      </motion.section>
    </div>
  );
}
