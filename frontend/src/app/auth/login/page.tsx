"use client";

import { useRouter } from "next/navigation";
import { FormEvent } from "react";
import { motion } from "framer-motion";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    router.push("/dashboard");
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center mesh-bg overflow-hidden">
      <div className="absolute inset-0 grid-pattern" />
      <div className="orb absolute -left-32 top-20 h-96 w-96 bg-blue-500/20 animate-float" />
      <div className="orb absolute -right-32 bottom-20 h-80 w-80 bg-indigo-500/15 animate-float-delayed" />

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-md glass-card p-8"
      >
        <div className="flex justify-center mb-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-xl font-bold text-white shadow-lg shadow-blue-500/30">
            C
          </div>
        </div>
        <h1 className="text-center text-2xl font-bold text-gradient">ChainFactor AI</h1>
        <p className="mt-1 text-center text-sm text-slate-400">AI-powered invoice financing for SMEs</p>

        <div className="mt-8">
          <div className="flex rounded-lg bg-slate-800/50 p-1">
            <button className="flex-1 rounded-md bg-blue-500/20 py-2 text-sm font-medium text-blue-400">Login</button>
            <Link href="/auth/register" className="flex-1 rounded-md py-2 text-center text-sm font-medium text-slate-500 hover:text-slate-300 transition-colors">Register</Link>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300">Phone / Email</label>
              <input type="text" placeholder="+91 9876543210" className="glass-input mt-1 w-full text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Password</label>
              <input type="password" placeholder="••••••••" className="glass-input mt-1 w-full text-sm" />
            </div>
            <button type="submit" className="btn-glow w-full py-2.5 text-sm">Sign In</button>
          </form>

          <div className="mt-4 flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-xs text-slate-500">or</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>
          <button onClick={() => router.push("/dashboard")} className="btn-outline-glow mt-3 w-full py-2.5 text-sm">OTP Login</button>
        </div>
      </motion.div>
    </main>
  );
}
