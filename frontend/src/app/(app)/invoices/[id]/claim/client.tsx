"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { useWallet } from "@txnlab/use-wallet-react";
import { api } from "@/lib/api";
import { getDemoInvoiceDetail } from "@/lib/demo-data";
import { PERA_EXPLORER_BASE } from "@/lib/constants";
import Link from "next/link";

/* eslint-disable @typescript-eslint/no-explicit-any */
export default function ClaimNFTClient({ params }: { params: { id: string } }) {
  const { activeAccount, activeWallet } = useWallet();
  const [invoice, setInvoice] = useState<Record<string, any> | null>(null);
  const [step, setStep] = useState<1 | 2>(1);
  const [optingIn, setOptingIn] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [claimResult, setClaimResult] = useState<{ txn_id: string; asset_id: number; explorer_url: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getInvoice(params.id).then((data) => setInvoice(data as Record<string, any>)).catch(() => {
      setInvoice(getDemoInvoiceDetail(params.id));
    });
  }, [params.id]);

  const extracted = invoice?.extracted_data || {};
  const assetId = invoice?.nft_asset_id;
  const riskScore = invoice?.risk_score ?? 82;
  const status = invoice?.status || "approved";

  async function handleOptIn() {
    if (!activeAccount || !activeWallet) {
      setError("Please connect your wallet first");
      return;
    }
    setOptingIn(true);
    setError(null);
    try {
      const res = await api.nftOptIn(params.id, {
        wallet_address: activeAccount.address,
        signed_txn: "",
      });
      console.log("Opt-in response:", res);
      setStep(2);
    } catch (err: any) {
      setError(err.message || "Opt-in failed");
    }
    setOptingIn(false);
  }

  async function handleClaim() {
    if (!activeAccount) {
      setError("Please connect your wallet first");
      return;
    }
    setClaiming(true);
    setError(null);
    try {
      const res = await api.nftClaim(params.id, {
        wallet_address: activeAccount.address,
      });
      setClaimResult(res);
    } catch (err: any) {
      setError(err.message || "Claim failed");
    }
    setClaiming(false);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="section-title">Claim Your Invoice NFT</motion.h1>

      {error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </motion.div>
      )}

      {claimResult ? (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mt-6 glass-card p-8 text-center">
          <p className="text-5xl">🎉</p>
          <h2 className="mt-4 text-xl font-bold text-gradient">NFT Claimed Successfully!</h2>
          <p className="mt-2 text-sm text-slate-400">Asset ID: <span className="text-blue-400 font-mono">#{claimResult.asset_id}</span></p>
          <p className="mt-1 text-sm text-slate-400">Transaction: <span className="text-blue-400 font-mono">{claimResult.txn_id.slice(0, 12)}...</span></p>
          <div className="mt-6 flex justify-center gap-3">
            <a href={`${PERA_EXPLORER_BASE}/asset/${claimResult.asset_id}/`} target="_blank" rel="noopener noreferrer" className="btn-glow px-6 py-2.5 text-sm">
              View on Pera Explorer ↗
            </a>
            <Link href={`/invoices/${params.id}`} className="btn-outline-glow px-6 py-2.5 text-sm">
              Back to Invoice
            </Link>
          </div>
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-6 glass-card p-8">
          {/* NFT Card */}
          <motion.div
            animate={{ rotateY: [0, 5, 0, -5, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="mx-auto max-w-sm rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-500/10 via-slate-900/90 to-indigo-500/10 p-6 shadow-xl shadow-blue-500/10"
            style={{ transformStyle: "preserve-3d", perspective: "800px" }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-blue-400">ChainFactor AI</p>
                <p className="text-[10px] text-slate-500">INVOICE NFT</p>
              </div>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-xs font-bold text-white">C</div>
            </div>
            <div className="mt-5">
              <p className="text-xl font-bold text-slate-100">{extracted.invoice_number || invoice?.invoice_number || "INV-..."}</p>
              <p className="text-sm text-slate-400">{extracted.seller_name || "Seller"} → {extracted.buyer_name || "Buyer"}</p>
              <p className="mt-2 text-2xl font-bold text-gradient">
                {extracted.grand_total ? `₹${Number(extracted.grand_total).toLocaleString("en-IN")}` : "—"}
              </p>
            </div>
            <div className="mt-5 flex items-center justify-between">
              <div><p className="text-[10px] text-slate-500">Risk Score</p><p className={`text-sm font-semibold ${riskScore >= 70 ? "text-emerald-400" : "text-yellow-400"}`}>{riskScore} ({riskScore >= 70 ? "Low" : "Med"})</p></div>
              <div className="text-right"><p className="text-[10px] text-slate-500">Status</p><p className="text-sm font-semibold text-emerald-400">{status.toUpperCase()}</p></div>
            </div>
            <div className="mt-5 border-t border-blue-500/10 pt-3 flex items-center justify-between">
              <p className="text-[10px] text-slate-600">{assetId ? `ASA #${assetId}` : "Pending mint"}</p>
              <p className="text-[10px] text-blue-400">Algorand Testnet</p>
            </div>
          </motion.div>

          {/* Connection status */}
          {!activeAccount && (
            <div className="mt-6 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-3 text-center text-sm text-yellow-400">
              ⚠️ Connect your Algorand wallet using the button in the navbar to claim this NFT
            </div>
          )}

          {/* Step 1 */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="mt-8">
            <div className="flex items-center gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full border text-sm font-bold ${
                step >= 2 ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" : "bg-blue-500/20 border-blue-500/30 text-blue-400"
              }`}>{step >= 2 ? "✓" : "1"}</div>
              <h3 className="font-medium text-slate-200">Opt-in to Asset</h3>
            </div>
            <p className="mt-2 ml-11 text-sm text-slate-500">This will increase your minimum balance by 0.1 ALGO. Your wallet will sign an opt-in transaction.</p>
            <button
              onClick={handleOptIn}
              disabled={optingIn || step >= 2 || !activeAccount}
              className="btn-glow mt-3 ml-11 px-6 py-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {optingIn ? "Opting in..." : step >= 2 ? "✓ Opted In" : "Opt-in to ASA (0.1 ALGO)"}
            </button>
          </motion.div>

          {/* Step 2 */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="mt-8">
            <div className="flex items-center gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full border text-sm font-bold ${
                step >= 2 ? "bg-blue-500/20 border-blue-500/30 text-blue-400" : "bg-slate-800 border-slate-700 text-slate-500"
              }`}>2</div>
              <h3 className={`font-medium ${step >= 2 ? "text-slate-200" : "text-slate-500"}`}>Receive NFT Transfer</h3>
            </div>
            <button
              onClick={handleClaim}
              disabled={claiming || step < 2 || !activeAccount}
              className={`mt-3 ml-11 rounded-xl px-6 py-2.5 text-sm font-medium transition-all ${
                step >= 2
                  ? "btn-glow disabled:opacity-50"
                  : "bg-slate-800 border border-slate-700 text-slate-500 cursor-not-allowed"
              }`}
            >
              {claiming ? "Claiming NFT..." : "Claim NFT"}
            </button>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
