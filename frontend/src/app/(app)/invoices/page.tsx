"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const invoices = [
  { id: "inv_stub_001", number: "INV-001", seller: "Acme Technologies", amount: "₹6.1L", risk: 82, status: "Approved", badge: "badge-approved" },
  { id: "inv_stub_002", number: "INV-002", seller: "TechCo Solutions", amount: "₹3.1L", risk: 45, status: "Flagged", badge: "badge-flagged" },
  { id: "inv_stub_003", number: "INV-003", seller: "BuildRight Infra", amount: "₹8.0L", risk: 91, status: "Minted", badge: "badge-minted" },
  { id: "inv_stub_004", number: "INV-004", seller: "FakeCorp Ltd", amount: "₹2.1L", risk: 12, status: "Rejected", badge: "badge-rejected" },
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

export default function InvoicesPage() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="section-title">Invoices</motion.h1>
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
          <Link href="/invoices/upload" className="btn-glow px-4 py-2 text-sm">+ Upload New</Link>
        </motion.div>
      </div>

      {/* Filters */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-4 flex items-center gap-3">
        <select className="glass-input text-sm py-2">
          <option>All Status</option>
          <option>Processing</option>
          <option>Approved</option>
          <option>Rejected</option>
          <option>Flagged</option>
          <option>Minted</option>
        </select>
        <select className="glass-input text-sm py-2">
          <option>All Risk</option>
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
        </select>
        <input type="text" placeholder="Search invoices..." className="glass-input flex-1 text-sm" />
      </motion.div>

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mt-4 glass-table">
        <table className="min-w-full">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Seller</th>
              <th>Amount</th>
              <th>Risk</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv, i) => (
              <motion.tr
                key={inv.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
              >
                <td className="font-medium text-slate-200">{inv.number}</td>
                <td className="text-slate-400">{inv.seller}</td>
                <td className="font-medium text-slate-300">{inv.amount}</td>
                <td><RiskBar value={inv.risk} /></td>
                <td><span className={`badge ${inv.badge}`}>{inv.status}</span></td>
                <td>
                  <Link href={`/invoices/${inv.id}`} className="text-blue-400 hover:text-blue-300 text-sm transition-colors">View →</Link>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </motion.div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
        <span>Showing 1-4 of 4</span>
        <div className="flex gap-2">
          <button className="rounded-lg border border-blue-500/20 px-3 py-1 text-slate-400 hover:bg-blue-500/10 transition-colors">Prev</button>
          <button className="rounded-lg bg-blue-500/20 px-3 py-1 text-blue-400">1</button>
          <button className="rounded-lg border border-blue-500/20 px-3 py-1 text-slate-400 hover:bg-blue-500/10 transition-colors">Next</button>
        </div>
      </div>
    </div>
  );
}
