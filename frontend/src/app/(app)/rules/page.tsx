"use client";

import { motion } from "framer-motion";

const rules = [
  {
    name: "Rule 1",
    conditions: [
      { connector: "IF", field: "invoice amount", op: "is less than", value: "₹5,00,000" },
      { connector: "AND", field: "risk score", op: "is greater than", value: "60" },
      { connector: "AND", field: "fraud flags", op: "equals", value: "0" },
    ],
    action: "Auto-approve",
    active: true,
  },
  {
    name: "Rule 2",
    conditions: [
      { connector: "IF", field: "amount", op: "<", value: "₹10,00,000" },
      { connector: "AND", field: "risk", op: ">", value: "80" },
      { connector: "AND", field: "CIBIL", op: ">", value: "700" },
    ],
    action: "Auto-approve",
    active: true,
  },
];

export default function RulesPage() {
  return (
    <div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="section-title">Auto-Approve Rules</h1>
        <p className="mt-1 text-sm text-slate-400">Set conditions for automatic invoice approval.</p>
      </motion.div>

      <div className="mt-6 space-y-4">
        {rules.map((rule, ri) => (
          <motion.div
            key={rule.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: ri * 0.1 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 border border-blue-500/30 text-xs font-bold text-blue-400">{ri + 1}</div>
                <h3 className="font-medium text-slate-200">{rule.name}</h3>
              </div>
              <button className="text-sm text-red-400/60 hover:text-red-400 transition-colors">Delete</button>
            </div>
            <div className="mt-4 space-y-2">
              {rule.conditions.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="rounded bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-400">{c.connector}</span>
                  <span className="text-slate-300">{c.field}</span>
                  <span className="text-slate-500">{c.op}</span>
                  <span className="rounded bg-slate-800 border border-blue-500/10 px-2 py-0.5 text-blue-300 font-medium">{c.value}</span>
                </div>
              ))}
              <div className="flex items-center gap-2 text-sm mt-1">
                <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-400">THEN</span>
                <span className="text-emerald-400 font-medium">{rule.action}</span>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <span className="badge badge-approved">✅ Active</span>
              <button className="rounded-lg border border-blue-500/20 px-3 py-1 text-xs text-slate-400 hover:bg-blue-500/10 transition-colors">Toggle</button>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Add Rule */}
      <motion.button
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
        whileHover={{ scale: 1.02 }}
        className="mt-4 w-full rounded-xl border-2 border-dashed border-blue-500/20 py-4 text-sm font-medium text-blue-400/60 hover:border-blue-500/40 hover:text-blue-400 transition-colors"
      >
        + Add New Rule
      </motion.button>

      {/* Default Behavior */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="mt-8 glass-card p-6">
        <h3 className="text-sm font-medium text-slate-200">Default Behavior</h3>
        <p className="mt-1 text-sm text-slate-500">When no rules match:</p>
        <select className="glass-input mt-2 text-sm">
          <option>Flag for manual review</option>
          <option>Reject</option>
          <option>Always approve</option>
        </select>
      </motion.div>

      <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }} className="btn-glow mt-6 px-6 py-2.5 text-sm">
        Save Rules
      </motion.button>
    </div>
  );
}
