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
  { href: "/invoices/inv_stub_001", label: "Invoice Detail", icon: "🔍" },
  { href: "/invoices/inv_stub_001/processing", label: "Processing", icon: "⚙️" },
  { href: "/invoices/inv_stub_001/claim", label: "Claim NFT", icon: "🎨" },
  { href: "/invoices/inv_stub_001/audit", label: "Audit Trail", icon: "📜" },
  { href: "/rules", label: "Rules", icon: "⚖️" },
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

        {/* Demo Navigation */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 2 }}
          className="mt-20 w-full max-w-3xl"
        >
          <div className="glass-card p-8">
            <p className="text-center text-xs font-semibold uppercase tracking-widest text-blue-400">
              Demo — Browse All Pages
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
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
