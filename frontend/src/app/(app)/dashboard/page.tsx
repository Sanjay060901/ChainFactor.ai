"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface DashboardData {
  total_value: number;
  active_invoices: number;
  pending_invoices: number;
  avg_risk_score: number;
  approval_rate: number;
  risk_distribution: { low: number; medium: number; high: number };
  monthly_volume: Array<{ month: string; count: number; value: number }>;
}

interface RecentInvoice {
  id: string;
  invoice_number: string;
  seller_name: string;
  amount: number;
  risk_score: number | null;
  status: string;
}

const BADGE_MAP: Record<string, string> = {
  approved: "badge-approved",
  rejected: "badge-rejected",
  flagged: "badge-flagged",
  minted: "badge-minted",
  processing: "badge-processing",
};

function formatValue(v: number): string {
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(0)}K`;
  return `₹${v}`;
}

function RiskBar({ value }: { value: number | null }) {
  if (!value) return <span className="text-xs text-slate-600">—</span>;
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
  const [data, setData] = useState<DashboardData | null>(null);
  const [invoices, setInvoices] = useState<RecentInvoice[]>([]);
  const [nlQuery, setNlQuery] = useState("");
  const [nlAnswer, setNlAnswer] = useState("");
  const [nlLoading, setNlLoading] = useState(false);

  useEffect(() => {
    api.dashboardSummary().then(setData).catch(() => setData(null));
    api.listInvoices({ limit: 5, sort: "-created_at" })
      .then((res) => setInvoices(res.invoices as unknown as RecentInvoice[]))
      .catch(() => setInvoices([]));
  }, []);

  async function handleNlQuery() {
    if (!nlQuery.trim()) return;
    setNlLoading(true);
    setNlAnswer("");
    try {
      const res = await api.nlQuery(nlQuery);
      setNlAnswer(res.answer);
    } catch {
      setNlAnswer("Unable to process your query. Please try again later.");
    }
    setNlLoading(false);
  }

  const stats = data ? [
    { label: "Total Value", value: formatValue(data.total_value), change: `${data.active_invoices} active`, icon: "💰", color: "from-blue-500/20 to-blue-600/5", changeColor: "text-emerald-400" },
    { label: "Active Invoices", value: String(data.active_invoices), change: `${data.pending_invoices} pending`, icon: "📄", color: "from-indigo-500/20 to-indigo-600/5", changeColor: "text-yellow-400" },
    { label: "Avg Risk Score", value: String(data.avg_risk_score), change: data.avg_risk_score >= 70 ? "Low risk" : "Medium risk", icon: "📊", color: "from-emerald-500/20 to-emerald-600/5", changeColor: "text-emerald-400" },
    { label: "Approval Rate", value: `${data.approval_rate}%`, change: "of total", icon: "✅", color: "from-violet-500/20 to-violet-600/5", changeColor: "text-emerald-400" },
  ] : [
    { label: "Total Value", value: "—", change: "Loading", icon: "💰", color: "from-blue-500/20 to-blue-600/5", changeColor: "text-slate-500" },
    { label: "Active Invoices", value: "—", change: "Loading", icon: "📄", color: "from-indigo-500/20 to-indigo-600/5", changeColor: "text-slate-500" },
    { label: "Avg Risk Score", value: "—", change: "Loading", icon: "📊", color: "from-emerald-500/20 to-emerald-600/5", changeColor: "text-slate-500" },
    { label: "Approval Rate", value: "—", change: "Loading", icon: "✅", color: "from-violet-500/20 to-violet-600/5", changeColor: "text-slate-500" },
  ];

  const riskDist = data?.risk_distribution || { low: 70, medium: 19, high: 11 };
  const avgRisk = data?.avg_risk_score || 0;
  const volumes = data?.monthly_volume || [];
  const maxVolume = Math.max(...volumes.map((v) => v.count), 1);

  return (
    <div>
      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="section-title">
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
              <circle cx="60" cy="60" r="50" fill="none" stroke="url(#blueGrad)" strokeWidth="12" strokeDasharray={`${riskDist.low * 3.14} 314`} strokeLinecap="round" />
              <circle cx="60" cy="60" r="50" fill="none" stroke="url(#greenGrad)" strokeWidth="12" strokeDasharray={`${riskDist.medium * 3.14} 314`} strokeDashoffset={`${-riskDist.low * 3.14}`} strokeLinecap="round" />
              <circle cx="60" cy="60" r="50" fill="none" stroke="url(#yellowGrad)" strokeWidth="12" strokeDasharray={`${riskDist.high * 3.14} 314`} strokeDashoffset={`${-(riskDist.low + riskDist.medium) * 3.14}`} strokeLinecap="round" />
              <defs>
                <linearGradient id="blueGrad"><stop stopColor="#3b82f6" /><stop offset="1" stopColor="#6366f1" /></linearGradient>
                <linearGradient id="greenGrad"><stop stopColor="#22c55e" /><stop offset="1" stopColor="#10b981" /></linearGradient>
                <linearGradient id="yellowGrad"><stop stopColor="#eab308" /><stop offset="1" stopColor="#f59e0b" /></linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-slate-100">{avgRisk || "—"}</span>
              <span className="text-[10px] text-slate-400">Avg Risk</span>
            </div>
          </div>
          <div className="mt-4 flex gap-4 text-xs">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-blue-500" />Low ({riskDist.low}%)</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" />Med ({riskDist.medium}%)</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-yellow-500" />High ({riskDist.high}%)</span>
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
            {volumes.length > 0 ? volumes.map((v, i) => (
              <motion.div
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${(v.count / maxVolume) * 100}%` }}
                transition={{ delay: 0.6 + i * 0.05, duration: 0.5 }}
                className="flex-1 rounded-t-md bg-gradient-to-t from-blue-500/60 to-blue-400/20 hover:from-blue-400/80 hover:to-blue-300/40 transition-colors cursor-pointer"
                title={`${v.month}: ${v.count} invoices`}
              />
            )) : (
              Array.from({ length: 12 }, (_, i) => (
                <div key={i} className="flex-1 rounded-t-md bg-slate-800/50 h-4" />
              ))
            )}
          </div>
          {volumes.length > 0 && (
            <div className="mt-2 flex justify-between text-[10px] text-slate-500">
              {volumes.map((v) => <span key={v.month}>{v.month}</span>)}
            </div>
          )}
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
            value={nlQuery}
            onChange={(e) => setNlQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleNlQuery()}
            className="glass-input flex-1 text-sm"
          />
          <button onClick={handleNlQuery} disabled={nlLoading} className="btn-glow px-4 py-2 text-sm disabled:opacity-50">
            {nlLoading ? "..." : "Ask"}
          </button>
        </div>
        {nlAnswer && (
          <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mt-3 rounded-lg bg-blue-500/5 border border-blue-500/10 p-3 text-sm text-slate-300">
            {nlAnswer}
          </motion.div>
        )}
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
          {invoices.length > 0 ? (
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
                    <td className="font-medium text-slate-200">
                      <Link href={`/invoices/${inv.id}`} className="hover:text-blue-400 transition-colors">{inv.invoice_number || "—"}</Link>
                    </td>
                    <td className="text-slate-400">{inv.seller_name || "—"}</td>
                    <td className="text-slate-300 font-medium">{formatValue(inv.amount)}</td>
                    <td><RiskBar value={inv.risk_score} /></td>
                    <td><span className={`badge ${BADGE_MAP[inv.status] || "badge-processing"}`}>{inv.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="py-8 text-center text-sm text-slate-500">
              No invoices yet. <Link href="/invoices/upload" className="text-blue-400">Upload your first →</Link>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
