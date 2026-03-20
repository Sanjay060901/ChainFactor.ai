"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const stats = [
  { label: "Total Value", value: "₹45.2L", change: "↑ 12% MTD", icon: "💰", color: "from-blue-500/20 to-blue-600/5", changeColor: "text-emerald-400" },
  { label: "Active Invoices", value: "12", change: "3 pending", icon: "📄", color: "from-indigo-500/20 to-indigo-600/5", changeColor: "text-yellow-400" },
  { label: "Avg Risk Score", value: "72", change: "↓ from 78", icon: "📊", color: "from-emerald-500/20 to-emerald-600/5", changeColor: "text-emerald-400" },
  { label: "Approval Rate", value: "85%", change: "↑ from 80%", icon: "✅", color: "from-violet-500/20 to-violet-600/5", changeColor: "text-emerald-400" },
];

const invoices = [
  { id: "INV-001", seller: "Acme Tech", amount: "₹5.2L", risk: 82, status: "Approved", badge: "badge-approved" },
  { id: "INV-002", seller: "TechCo", amount: "₹3.1L", risk: 45, status: "Flagged", badge: "badge-flagged" },
  { id: "INV-003", seller: "BuildRight", amount: "₹8.0L", risk: 91, status: "Minted", badge: "badge-minted" },
];

function RiskBar({ value }: { value: number }) {
  const color = value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-slate-700">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-slate-400">{value}</span>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div>
      <motion.h1
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="section-title"
      >
        Dashboard
      </motion.h1>

      {/* Stat Cards */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ scale: 1.03, y: -4 }}
            className="card-3d"
          >
            <div className={`glass-card bg-gradient-to-br ${stat.color} p-6`}>
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{stat.label}</p>
                <span className="text-xl">{stat.icon}</span>
              </div>
              <p className="mt-3 text-3xl font-bold text-slate-100 stat-glow">{stat.value}</p>
              <p className={`mt-1 text-xs font-medium ${stat.changeColor}`}>{stat.change}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass-card flex h-72 flex-col items-center justify-center p-6"
        >
          <div className="relative h-40 w-40">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(59,130,246,0.1)" strokeWidth="12" />
              <circle cx="60" cy="60" r="50" fill="none" stroke="url(#blueGrad)" strokeWidth="12" strokeDasharray="220 314" strokeLinecap="round" />
              <circle cx="60" cy="60" r="50" fill="none" stroke="url(#greenGrad)" strokeWidth="12" strokeDasharray="60 314" strokeDashoffset="-220" strokeLinecap="round" />
              <circle cx="60" cy="60" r="50" fill="none" stroke="url(#yellowGrad)" strokeWidth="12" strokeDasharray="34 314" strokeDashoffset="-280" strokeLinecap="round" />
              <defs>
                <linearGradient id="blueGrad"><stop stopColor="#3b82f6" /><stop offset="1" stopColor="#6366f1" /></linearGradient>
                <linearGradient id="greenGrad"><stop stopColor="#22c55e" /><stop offset="1" stopColor="#10b981" /></linearGradient>
                <linearGradient id="yellowGrad"><stop stopColor="#eab308" /><stop offset="1" stopColor="#f59e0b" /></linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-slate-100">72</span>
              <span className="text-[10px] text-slate-400">Avg Risk</span>
            </div>
          </div>
          <div className="mt-4 flex gap-4 text-xs">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-blue-500" />Low (70%)</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" />Med (19%)</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-yellow-500" />High (11%)</span>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card flex h-72 flex-col justify-end p-6"
        >
          <p className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-400">Monthly Volume</p>
          <div className="flex items-end gap-3 h-40">
            {[40, 65, 55, 80, 70, 95, 60, 75, 88, 72, 90, 85].map((h, i) => (
              <motion.div
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${h}%` }}
                transition={{ delay: 0.6 + i * 0.05, duration: 0.5 }}
                className="flex-1 rounded-t-md bg-gradient-to-t from-blue-500/60 to-blue-400/20 hover:from-blue-400/80 hover:to-blue-300/40 transition-colors cursor-pointer"
              />
            ))}
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-slate-500">
            <span>Apr</span><span>May</span><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span><span>Jan</span><span>Feb</span><span>Mar</span>
          </div>
        </motion.div>
      </div>

      {/* NL Query Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card mt-6 p-4"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">🤖</span>
          <input
            type="text"
            placeholder="Ask anything: Show me high-risk invoices this week..."
            className="glass-input flex-1 text-sm"
          />
          <button className="btn-glow px-4 py-2 text-sm">Ask</button>
        </div>
      </motion.div>

      {/* Recent Invoices */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="mt-6"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-200">Recent Invoices</h2>
          <Link href="/invoices" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
            View All →
          </Link>
        </div>
        <div className="mt-3 glass-table">
          <table className="min-w-full">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Seller</th>
                <th>Amount</th>
                <th>Risk</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td className="font-medium text-slate-200">{inv.id}</td>
                  <td className="text-slate-400">{inv.seller}</td>
                  <td className="text-slate-300 font-medium">{inv.amount}</td>
                  <td><RiskBar value={inv.risk} /></td>
                  <td><span className={`badge ${inv.badge}`}>{inv.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
