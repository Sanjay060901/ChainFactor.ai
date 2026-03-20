"use client";

import { motion } from "framer-motion";

export default function ClaimNFTPage({ params }: { params: { id: string } }) {
  return (
    <div className="mx-auto max-w-2xl">
      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="section-title">Claim Your Invoice NFT</motion.h1>

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
            <p className="text-xl font-bold text-slate-100">INV-2026-001</p>
            <p className="text-sm text-slate-400">Acme Tech → TechBuild</p>
            <p className="mt-2 text-2xl font-bold text-gradient">₹6,13,600</p>
          </div>
          <div className="mt-5 flex items-center justify-between">
            <div><p className="text-[10px] text-slate-500">Risk Score</p><p className="text-sm font-semibold text-emerald-400">82 (Low)</p></div>
            <div className="text-right"><p className="text-[10px] text-slate-500">Status</p><p className="text-sm font-semibold text-emerald-400">APPROVED</p></div>
          </div>
          <div className="mt-5 border-t border-blue-500/10 pt-3 flex items-center justify-between">
            <p className="text-[10px] text-slate-600">ASA #12345678</p>
            <p className="text-[10px] text-blue-400">Algorand Testnet</p>
          </div>
        </motion.div>

        {/* Step 1 */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="mt-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/20 border border-blue-500/30 text-sm font-bold text-blue-400">1</div>
            <h3 className="font-medium text-slate-200">Opt-in to Asset</h3>
          </div>
          <p className="mt-2 ml-11 text-sm text-slate-500">This will increase your minimum balance by 0.1 ALGO. Your wallet will sign an opt-in transaction.</p>
          <button className="btn-glow mt-3 ml-11 px-6 py-2.5 text-sm">Opt-in to ASA (0.1 ALGO)</button>
        </motion.div>

        {/* Step 2 */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="mt-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-sm font-bold text-slate-500">2</div>
            <h3 className="font-medium text-slate-500">Receive NFT Transfer</h3>
          </div>
          <button disabled className="mt-3 ml-11 rounded-xl bg-slate-800 border border-slate-700 px-6 py-2.5 text-sm font-medium text-slate-500 cursor-not-allowed">
            Claim NFT (after opt-in)
          </button>
        </motion.div>
      </motion.div>
    </div>
  );
}
