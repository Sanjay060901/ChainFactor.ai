"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

interface Invoice {
  id: string;
  invoice_number: string;
  seller_name: string;
  amount: number;
  risk_score: number | null;
  status: string;
  created_at: string;
}

const BADGE_MAP: Record<string, string> = {
  approved: "badge-approved",
  rejected: "badge-rejected",
  flagged: "badge-flagged",
  minted: "badge-minted",
  processing: "badge-processing",
  claimed: "badge-approved",
};

function formatAmount(amount: number): string {
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
  return `₹${amount}`;
}

function RiskBar({ value }: { value: number | null }) {
  if (value === null) return <span className="text-xs text-slate-600">—</span>;
  const color = value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-slate-700">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-slate-400">{Math.round(value)}</span>
    </div>
  );
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listInvoices({
        page,
        limit: 10,
        status: statusFilter || undefined,
        search: search || undefined,
        sort: "-created_at",
      });
      setInvoices(res.invoices);
      setTotal(res.total);
      setPages(res.pages);
    } catch {
      setInvoices([]);
      setTotal(0);
      setPages(1);
    }
    setLoading(false);
  }, [page, statusFilter, search]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  async function handleDelete(id: string) {
    if (!confirm("Delete this invoice? This cannot be undone.")) return;
    setDeleting(id);
    try {
      await api.deleteInvoice(id);
      await fetchInvoices();
    } catch {
      // ignore
    }
    setDeleting(null);
  }

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
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="glass-input text-sm py-2">
          <option value="">All Status</option>
          <option value="processing">Processing</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="flagged">Flagged</option>
          <option value="minted">Minted</option>
        </select>
        <input
          type="text"
          placeholder="Search invoices..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="glass-input flex-1 text-sm"
        />
      </motion.div>

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="mt-4 glass-table">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <span className="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
            <span className="ml-3 text-sm text-slate-400">Loading invoices...</span>
          </div>
        ) : invoices.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-3xl">📄</p>
            <p className="mt-2 text-sm text-slate-500">No invoices found</p>
            <Link href="/invoices/upload" className="mt-3 inline-block text-sm text-blue-400 hover:text-blue-300">Upload your first invoice →</Link>
          </div>
        ) : (
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
                  <td className="font-medium text-slate-200">{inv.invoice_number || "—"}</td>
                  <td className="text-slate-400">{inv.seller_name || "—"}</td>
                  <td className="font-medium text-slate-300">{formatAmount(inv.amount)}</td>
                  <td><RiskBar value={inv.risk_score} /></td>
                  <td><span className={`badge ${BADGE_MAP[inv.status] || "badge-processing"}`}>{inv.status}</span></td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Link href={`/invoices/${inv.id}`} className="text-blue-400 hover:text-blue-300 text-sm transition-colors">View →</Link>
                      <button
                        onClick={() => handleDelete(inv.id)}
                        disabled={deleting === inv.id}
                        className="text-red-400/60 hover:text-red-400 text-sm transition-colors disabled:opacity-30"
                        title="Delete invoice"
                      >
                        {deleting === inv.id ? "…" : "🗑"}
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
        <span>Showing {invoices.length} of {total}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded-lg border border-blue-500/20 px-3 py-1 text-slate-400 hover:bg-blue-500/10 transition-colors disabled:opacity-30">Prev</button>
          {Array.from({ length: pages }, (_, i) => i + 1).slice(0, 5).map((p) => (
            <button key={p} onClick={() => setPage(p)} className={`rounded-lg px-3 py-1 ${p === page ? "bg-blue-500/20 text-blue-400" : "border border-blue-500/20 text-slate-400 hover:bg-blue-500/10"} transition-colors`}>{p}</button>
          ))}
          <button disabled={page >= pages} onClick={() => setPage(page + 1)} className="rounded-lg border border-blue-500/20 px-3 py-1 text-slate-400 hover:bg-blue-500/10 transition-colors disabled:opacity-30">Next</button>
        </div>
      </div>
    </div>
  );
}
