"use client";

import { motion } from "framer-motion";
import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

interface VerifyResult {
  verified: boolean;
  asset_id: number;
  invoice_number: string | null;
  seller_name: string | null;
  buyer_name: string | null;
  amount: number | null;
  risk_score: number | null;
  risk_level: string | null;
  decision: string | null;
  minted_at: string | null;
  claimed: boolean;
  explorer_url: string;
  arc69_metadata: Record<string, unknown> | null;
}

export default function VerifyPage() {
  const [assetId, setAssetId] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchMode, setSearchMode] = useState<"asset" | "invoice">("asset");

  async function handleVerify() {
    const query = searchMode === "asset" ? assetId.trim() : invoiceNumber.trim();
    if (!query) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      let url: string;
      if (searchMode === "asset") {
        url = `${API_BASE}/api/v1/verify/nft/${query}`;
      } else {
        // Search by invoice number first to get asset ID
        const searchRes = await fetch(`${API_BASE}/api/v1/verify/search?invoice_number=${encodeURIComponent(query)}`);
        if (!searchRes.ok) {
          const err = await searchRes.json().catch(() => null);
          throw new Error(err?.detail || "Invoice not found");
        }
        const searchData = await searchRes.json();
        url = `${API_BASE}/api/v1/verify/nft/${searchData.asset_id}`;
      }

      const res = await fetch(url);
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Verification failed");
      }
      setResult(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Verification failed");
    }
    setLoading(false);
  }

  const riskColor = (score: number | null) =>
    !score ? "text-slate-500" : score >= 70 ? "text-emerald-400" : score >= 40 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="min-h-screen bg-[#020617] px-4 py-16">
      <div className="mx-auto max-w-2xl">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            On-Chain Verification
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Verify any ChainFactor AI invoice NFT — no login required
          </p>
        </motion.div>

        {/* Search Mode Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mt-8 flex justify-center gap-2"
        >
          <button
            onClick={() => setSearchMode("asset")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              searchMode === "asset"
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            By Asset ID
          </button>
          <button
            onClick={() => setSearchMode("invoice")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              searchMode === "invoice"
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            By Invoice Number
          </button>
        </motion.div>

        {/* Search Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-4 glass-card p-6"
        >
          <div className="flex gap-3">
            <input
              type="text"
              placeholder={searchMode === "asset" ? "Enter Algorand Asset ID (e.g. 757705539)" : "Enter Invoice Number (e.g. INV-2026-0001)"}
              value={searchMode === "asset" ? assetId : invoiceNumber}
              onChange={(e) =>
                searchMode === "asset" ? setAssetId(e.target.value) : setInvoiceNumber(e.target.value)
              }
              onKeyDown={(e) => e.key === "Enter" && handleVerify()}
              className="glass-input flex-1 text-sm"
            />
            <button
              onClick={handleVerify}
              disabled={loading}
              className="btn-glow px-6 py-2 text-sm disabled:opacity-50"
            >
              {loading ? "Verifying..." : "🔍 Verify"}
            </button>
          </div>
        </motion.div>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400"
          >
            {error}
          </motion.div>
        )}

        {/* Result */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 space-y-4"
          >
            {/* Verification Badge */}
            <div className="glass-card p-6 text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 200 }}
                className="inline-block"
              >
                <span className="text-5xl">{result.verified ? "✅" : "❌"}</span>
              </motion.div>
              <h2 className="mt-3 text-xl font-bold text-slate-100">
                {result.verified ? "Invoice Verified" : "Not Verified"}
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                ASA #{result.asset_id} on Algorand Testnet
              </p>
              <a
                href={result.explorer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                View on Pera Explorer ↗
              </a>
            </div>

            {/* Invoice Details */}
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-slate-200">Invoice Details</h3>
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Invoice #:</span>{" "}
                  <span className="text-slate-200">{result.invoice_number || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500">Decision:</span>{" "}
                  <span className={`font-medium capitalize ${
                    result.decision === "approved" ? "text-emerald-400" :
                    result.decision === "rejected" ? "text-red-400" : "text-yellow-400"
                  }`}>{result.decision || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500">Seller:</span>{" "}
                  <span className="text-slate-200">{result.seller_name || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500">Buyer:</span>{" "}
                  <span className="text-slate-200">{result.buyer_name || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500">Amount:</span>{" "}
                  <span className="text-slate-200">
                    {result.amount ? `₹${Math.round(Number(result.amount)).toLocaleString("en-IN")}` : "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Risk Score:</span>{" "}
                  <span className={`font-bold ${riskColor(result.risk_score)}`}>
                    {result.risk_score || "N/A"}
                  </span>
                  {result.risk_level && (
                    <span className="ml-1 text-xs text-slate-500">({result.risk_level})</span>
                  )}
                </div>
                <div>
                  <span className="text-slate-500">NFT Claimed:</span>{" "}
                  <span className={result.claimed ? "text-emerald-400" : "text-yellow-400"}>
                    {result.claimed ? "Yes" : "Pending"}
                  </span>
                </div>
                {result.minted_at && (
                  <div>
                    <span className="text-slate-500">Minted:</span>{" "}
                    <span className="text-slate-200">{new Date(result.minted_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* ARC-69 Metadata */}
            {result.arc69_metadata && (
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200">ARC-69 Metadata (On-Chain)</h3>
                <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-900/50 p-4 text-xs text-slate-400">
                  {JSON.stringify(result.arc69_metadata, null, 2)}
                </pre>
              </div>
            )}
          </motion.div>
        )}

        {/* How it works */}
        {!result && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mt-8 glass-card p-6"
          >
            <h3 className="text-sm font-semibold text-slate-200">How On-Chain Verification Works</h3>
            <div className="mt-4 space-y-3 text-xs text-slate-400">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-blue-400">1.</span>
                <p>When an invoice is approved, ChainFactor AI mints an <span className="text-slate-300">ARC-69 NFT</span> on the Algorand Testnet</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-blue-400">2.</span>
                <p>The NFT contains immutable metadata: invoice details, risk score, AI decision, and seller/buyer info</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-blue-400">3.</span>
                <p>Anyone (lenders, auditors, regulators) can verify an invoice using its <span className="text-slate-300">Asset ID</span> or <span className="text-slate-300">Invoice Number</span></p>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-blue-400">4.</span>
                <p>Verification is <span className="text-emerald-400">trustless</span> — data comes from the blockchain, not from ChainFactor&apos;s database</p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
