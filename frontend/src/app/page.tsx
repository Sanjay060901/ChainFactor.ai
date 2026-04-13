"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const features = [
  { icon: "🤖", title: "AI-Powered Analysis", desc: "11 tools, 2 agents, 5-layer fraud detection — all automated" },
  { icon: "⛓️", title: "Blockchain Verified", desc: "ARC-69 NFTs on Algorand testnet for tamper-proof records" },
  { icon: "📊", title: "Multi-Signal Risk", desc: "GSTIN, CIBIL, MCA, buyer intel fused into a single score" },
  { icon: "⚡", title: "Under 2 Minutes", desc: "End-to-end: upload to NFT mint in real-time" },
];

const pages = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/invoices", label: "Invoices", icon: "📋" },
  { href: "/invoices/upload", label: "Upload", icon: "📤" },
  { href: "/rules", label: "Rules", icon: "⚖️" },
  { href: "/settings", label: "AI Settings", icon: "🧠" },
];

const howToSteps = [
  { step: "1", title: "Connect Wallet", desc: "Link your Pera or Defly Algorand wallet to get started.", icon: "🔗" },
  { step: "2", title: "Upload Invoice", desc: "Upload a GST invoice PDF (max 5MB). Our AI extracts all data automatically.", icon: "📤" },
  { step: "3", title: "AI Analysis", desc: "11 AI tools run in sequence: OCR, validation, GST compliance, 5-layer fraud detection, GSTIN verification, credit scoring, and risk assessment.", icon: "🤖" },
  { step: "4", title: "Underwriting", desc: "The Underwriting Agent cross-validates all signals and makes an autonomous approve/reject/flag decision.", icon: "⚖️" },
  { step: "5", title: "Claim NFT", desc: "Approved invoices are minted as ARC-69 NFTs on Algorand testnet. Opt-in and claim your verifiable asset.", icon: "🎨" },
];

const targetAudience = [
  { title: "Indian SMEs", desc: "Small and medium enterprises seeking faster invoice financing with transparent risk scoring.", icon: "🏢" },
  { title: "Invoice Financiers", desc: "NBFCs, banks, and fintech platforms looking for AI-powered due diligence on invoice portfolios.", icon: "🏦" },
  { title: "GST-Registered Businesses", desc: "Any GSTIN-registered business wanting to verify invoice authenticity and buyer reliability.", icon: "📋" },
  { title: "Blockchain Enthusiasts", desc: "Developers and innovators exploring real-world DeFi applications on Algorand.", icon: "⛓️" },
];

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden mesh-bg">
      {/* Grid overlay */}
      <div className="absolute inset-0 grid-pattern" />

      {/* Floating orbs */}
      <div className="orb absolute -left-32 top-20 h-96 w-96 bg-blue-500/20 animate-float" />
      <div className="orb absolute -right-32 top-1/3 h-80 w-80 bg-indigo-500/15 animate-float-delayed" />
      <div className="orb absolute left-1/3 -bottom-20 h-72 w-72 bg-blue-600/10 animate-float-slow" />

      {/* Hero */}
      <div className="relative z-10 flex flex-col items-center justify-center px-6 pt-32 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center"
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-2 backdrop-blur-sm"
          >
            <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
            <span className="text-sm font-medium text-blue-300">Built for AlgoBharat Hack Series 3.0</span>
          </motion.div>

          <div style={{ perspective: "1000px" }}>
            <motion.h1
              initial={{ rotateX: 20, opacity: 0 }}
              animate={{ rotateX: 0, opacity: 1 }}
              transition={{ duration: 1, delay: 0.3 }}
              className="text-6xl font-extrabold tracking-tight sm:text-7xl lg:text-8xl"
            >
              <span className="text-gradient">ChainFactor</span>
              <span className="text-white"> AI</span>
            </motion.h1>
          </div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 sm:text-xl"
          >
            AI-powered invoice financing for Indian SMEs.
            <br className="hidden sm:block" />
            Upload. Analyze. Mint. — All on <span className="font-medium text-blue-400">Algorand</span>.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
          >
            <Link href="/auth/login" className="btn-glow text-sm">Get Started →</Link>
            <Link href="/auth/register" className="btn-outline-glow text-sm">Create Account</Link>
          </motion.div>
        </motion.div>

        {/* 3D Feature Cards */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 1 }}
          className="mt-24 grid max-w-5xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
        >
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 1.1 + i * 0.1 }}
              whileHover={{ scale: 1.05, rotateY: 5 }}
              className="card-3d"
            >
              <div className="glass-card p-6 text-center h-full">
                <div className="text-3xl">{f.icon}</div>
                <h3 className="mt-3 text-sm font-semibold text-slate-200">{f.title}</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* 3D Floating Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="mt-24 w-full max-w-4xl"
          style={{ perspective: "1200px" }}
        >
          <motion.div
            animate={{ rotateX: [2, -2, 2], rotateY: [-3, 3, -3] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="glass-card overflow-hidden p-1"
            style={{ transformStyle: "preserve-3d" }}
          >
            <div className="rounded-xl bg-gradient-to-br from-slate-900/80 to-slate-800/40 p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-3 w-3 rounded-full bg-red-500/60" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
                <div className="h-3 w-3 rounded-full bg-green-500/60" />
                <div className="ml-4 flex-1 rounded-md bg-slate-800/60 px-3 py-1 text-xs text-slate-500">
                  chainfactor.ai/dashboard
                </div>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: "Total Value", val: "₹45.2L", color: "from-blue-500/20 to-blue-600/5" },
                  { label: "Active", val: "12", color: "from-indigo-500/20 to-indigo-600/5" },
                  { label: "Risk Score", val: "72", color: "from-emerald-500/20 to-emerald-600/5" },
                  { label: "Approval", val: "85%", color: "from-violet-500/20 to-violet-600/5" },
                ].map((s) => (
                  <div key={s.label} className={`rounded-lg bg-gradient-to-br ${s.color} border border-white/5 p-4`}>
                    <p className="text-[10px] text-slate-400">{s.label}</p>
                    <p className="text-lg font-bold text-slate-200 stat-glow">{s.val}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex h-32 items-center justify-center rounded-lg border border-white/5 bg-gradient-to-br from-blue-500/5 to-transparent">
                <span className="text-xs text-slate-500">Live Processing Pipeline</span>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* How To Use */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.6 }}
          className="mt-24 w-full max-w-5xl"
        >
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-blue-400 mb-8">
            How It Works
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-5">
            {howToSteps.map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.7 + i * 0.1 }}
                className="glass-card p-5 text-center relative"
              >
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 h-6 w-6 rounded-full bg-blue-500/30 border border-blue-500/50 flex items-center justify-center text-xs font-bold text-blue-300">
                  {s.step}
                </div>
                <div className="text-2xl mt-2">{s.icon}</div>
                <h3 className="mt-2 text-sm font-semibold text-slate-200">{s.title}</h3>
                <p className="mt-1 text-xs text-slate-400 leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Target Audience */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 2.2 }}
          className="mt-20 w-full max-w-4xl"
        >
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-blue-400 mb-8">
            Who Is This For?
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {targetAudience.map((t, i) => (
              <motion.div
                key={t.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2.3 + i * 0.1 }}
                whileHover={{ scale: 1.05 }}
                className="glass-card p-6 text-center"
              >
                <div className="text-3xl">{t.icon}</div>
                <h3 className="mt-3 text-sm font-semibold text-slate-200">{t.title}</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">{t.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Navigation */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 2.7 }}
          className="mt-20 w-full max-w-3xl"
        >
          <div className="glass-card p-8">
            <p className="text-center text-xs font-semibold uppercase tracking-widest text-blue-400">
              Quick Navigation
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
              {pages.map((p) => (
                <motion.div key={p.href} whileHover={{ scale: 1.08, y: -4 }} whileTap={{ scale: 0.95 }}>
                  <Link
                    href={p.href}
                    className="flex flex-col items-center gap-2 rounded-xl border border-blue-500/10 bg-blue-500/5 p-4 text-center transition-colors hover:border-blue-500/30 hover:bg-blue-500/10"
                  >
                    <span className="text-2xl">{p.icon}</span>
                    <span className="text-xs font-medium text-slate-300">{p.label}</span>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        <div className="mt-20 pb-8 text-center text-xs text-slate-600">
          Built with Next.js, Algorand, Strands Agents &amp; Amazon Bedrock
        </div>
      </div>
    </div>
  );
}
