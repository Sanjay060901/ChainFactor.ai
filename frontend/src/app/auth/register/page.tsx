"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error } = useAuth();
  const [form, setForm] = useState({ name: "", company_name: "", gstin: "", phone: "", email: "", password: "" });

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await register(form);
      router.push("/auth/login");
    } catch {
      // error is set in useAuth
    }
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
        <p className="mt-1 text-center text-sm text-slate-400">Create your account</p>

        <div className="mt-8">
          <div className="flex rounded-lg bg-slate-800/50 p-1">
            <Link href="/auth/login" className="flex-1 rounded-md py-2 text-center text-sm font-medium text-slate-500 hover:text-slate-300 transition-colors">Login</Link>
            <button className="flex-1 rounded-md bg-blue-500/20 py-2 text-sm font-medium text-blue-400">Register</button>
          </div>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-300">Name</label>
              <input type="text" placeholder="Manoj RS" value={form.name} onChange={(e) => update("name", e.target.value)} className="glass-input mt-1 w-full text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Company Name</label>
              <input type="text" placeholder="Acme Technologies Pvt Ltd" value={form.company_name} onChange={(e) => update("company_name", e.target.value)} className="glass-input mt-1 w-full text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">GSTIN</label>
              <input type="text" placeholder="27AABCU9603R1ZM" value={form.gstin} onChange={(e) => update("gstin", e.target.value)} className="glass-input mt-1 w-full text-sm" required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-slate-300">Phone</label>
                <input type="tel" placeholder="+91 9876543210" value={form.phone} onChange={(e) => update("phone", e.target.value)} className="glass-input mt-1 w-full text-sm" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300">Email</label>
                <input type="email" placeholder="manoj@acmetech.in" value={form.email} onChange={(e) => update("email", e.target.value)} className="glass-input mt-1 w-full text-sm" required />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Password</label>
              <input type="password" placeholder="••••••••" value={form.password} onChange={(e) => update("password", e.target.value)} className="glass-input mt-1 w-full text-sm" required />
            </div>
            <button type="submit" disabled={isLoading} className="btn-glow w-full py-2.5 text-sm disabled:opacity-50">
              {isLoading ? "Creating..." : "Create Account"}
            </button>
          </form>
        </div>
      </motion.div>
    </main>
  );
}
