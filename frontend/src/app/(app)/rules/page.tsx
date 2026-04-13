"use client";

import { motion } from "framer-motion";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

interface RuleCondition {
  field: string;
  operator: string;
  value: number | string;
}

interface Rule {
  id: string;
  conditions: RuleCondition[];
  action: string;
  is_active: boolean;
  created_at: string;
}

const FIELDS = ["invoice_amount", "risk_score", "fraud_flags", "cibil_score"];
const OPERATORS = ["<", ">", "<=", ">=", "==", "!="];
const ACTIONS = ["auto_approve", "auto_reject", "flag_for_review"];

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [defaultAction, setDefaultAction] = useState("flag_for_review");
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newConditions, setNewConditions] = useState<RuleCondition[]>([{ field: "risk_score", operator: ">", value: 60 }]);
  const [newAction, setNewAction] = useState("auto_approve");
  const [saving, setSaving] = useState(false);

  const fetchRules = useCallback(async () => {
    try {
      const res = await api.listRules();
      setRules(res.rules);
      setDefaultAction(res.default_action);
    } catch {
      setRules([]);
      setDefaultAction("flag_for_review");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchRules(); }, [fetchRules]);

  async function handleCreate() {
    setSaving(true);
    try {
      await api.createRule({ conditions: newConditions, action: newAction });
      setShowForm(false);
      setNewConditions([{ field: "risk_score", operator: ">", value: 60 }]);
      fetchRules();
    } catch { /* ignore */ }
    setSaving(false);
  }

  async function handleDelete(id: string) {
    try {
      await api.deleteRule(id);
      fetchRules();
    } catch { /* ignore */ }
  }

  async function handleToggle(rule: Rule) {
    try {
      await api.updateRule(rule.id, { is_active: !rule.is_active });
      fetchRules();
    } catch { /* ignore */ }
  }

  async function handleDefaultAction(action: string) {
    setDefaultAction(action);
    try { await api.setDefaultAction(action); } catch { /* ignore */ }
  }

  function addCondition() {
    setNewConditions([...newConditions, { field: "invoice_amount", operator: "<", value: 500000 }]);
  }

  function updateCondition(idx: number, field: string, value: string | number) {
    setNewConditions(newConditions.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  }

  function removeCondition(idx: number) {
    if (newConditions.length > 1) setNewConditions(newConditions.filter((_, i) => i !== idx));
  }

  const OP_LABELS: Record<string, string> = { "<": "less than", ">": "greater than", "<=": "at most", ">=": "at least", "==": "equals", "!=": "not equal" };

  return (
    <div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="section-title">Auto-Approve Rules</h1>
        <p className="mt-1 text-sm text-slate-400">Set conditions for automatic invoice approval.</p>
      </motion.div>

      {loading ? (
        <div className="mt-8 flex justify-center"><span className="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" /></div>
      ) : (
        <div className="mt-6 space-y-4">
          {rules.map((rule, ri) => (
            <motion.div
              key={rule.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: ri * 0.1 }}
              className="glass-card p-6"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 border border-blue-500/30 text-xs font-bold text-blue-400">{ri + 1}</div>
                  <h3 className="font-medium text-slate-200">Rule {ri + 1}</h3>
                </div>
                <button onClick={() => handleDelete(rule.id)} className="text-sm text-red-400/60 hover:text-red-400 transition-colors">Delete</button>
              </div>
              <div className="mt-4 space-y-2">
                {rule.conditions.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="rounded bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-400">{i === 0 ? "IF" : "AND"}</span>
                    <span className="text-slate-300">{c.field.replace(/_/g, " ")}</span>
                    <span className="text-slate-500">{OP_LABELS[c.operator] || c.operator}</span>
                    <span className="rounded bg-slate-800 border border-blue-500/10 px-2 py-0.5 text-blue-300 font-medium">{String(c.value)}</span>
                  </div>
                ))}
                <div className="flex items-center gap-2 text-sm mt-1">
                  <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-400">THEN</span>
                  <span className="text-emerald-400 font-medium">{rule.action.replace(/_/g, " ")}</span>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <span className={`badge ${rule.is_active ? "badge-approved" : "badge-rejected"}`}>{rule.is_active ? "✅ Active" : "❌ Inactive"}</span>
                <button onClick={() => handleToggle(rule)} className="rounded-lg border border-blue-500/20 px-3 py-1 text-xs text-slate-400 hover:bg-blue-500/10 transition-colors">Toggle</button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Add Rule Form */}
      {showForm ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-200">New Rule</h3>
          <div className="mt-4 space-y-3">
            {newConditions.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-xs text-blue-400 w-8">{i === 0 ? "IF" : "AND"}</span>
                <select value={c.field} onChange={(e) => updateCondition(i, "field", e.target.value)} className="glass-input text-xs py-1.5">
                  {FIELDS.map((f) => <option key={f} value={f}>{f.replace(/_/g, " ")}</option>)}
                </select>
                <select value={c.operator} onChange={(e) => updateCondition(i, "operator", e.target.value)} className="glass-input text-xs py-1.5 w-16">
                  {OPERATORS.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
                <input type="number" value={c.value} onChange={(e) => updateCondition(i, "value", Number(e.target.value))} className="glass-input text-xs py-1.5 w-24" />
                {newConditions.length > 1 && (
                  <button onClick={() => removeCondition(i)} className="text-xs text-red-400">✕</button>
                )}
              </div>
            ))}
            <button onClick={addCondition} className="text-xs text-blue-400 hover:text-blue-300">+ Add condition</button>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <span className="text-xs text-emerald-400">THEN</span>
            <select value={newAction} onChange={(e) => setNewAction(e.target.value)} className="glass-input text-xs py-1.5">
              {ACTIONS.map((a) => <option key={a} value={a}>{a.replace(/_/g, " ")}</option>)}
            </select>
          </div>
          <div className="mt-4 flex gap-2">
            <button onClick={handleCreate} disabled={saving} className="btn-glow px-4 py-2 text-sm disabled:opacity-50">
              {saving ? "Saving..." : "Save Rule"}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-outline-glow px-4 py-2 text-sm">Cancel</button>
          </div>
        </motion.div>
      ) : (
        <motion.button
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          whileHover={{ scale: 1.02 }}
          onClick={() => setShowForm(true)}
          className="mt-4 w-full rounded-xl border-2 border-dashed border-blue-500/20 py-4 text-sm font-medium text-blue-400/60 hover:border-blue-500/40 hover:text-blue-400 transition-colors"
        >
          + Add New Rule
        </motion.button>
      )}

      {/* Default Behavior */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="mt-8 glass-card p-6">
        <h3 className="text-sm font-medium text-slate-200">Default Behavior</h3>
        <p className="mt-1 text-sm text-slate-500">When no rules match:</p>
        <select value={defaultAction} onChange={(e) => handleDefaultAction(e.target.value)} className="glass-input mt-2 text-sm">
          <option value="flag_for_review">Flag for manual review</option>
          <option value="auto_reject">Reject</option>
          <option value="auto_approve">Always approve</option>
        </select>
      </motion.div>
    </div>
  );
}
