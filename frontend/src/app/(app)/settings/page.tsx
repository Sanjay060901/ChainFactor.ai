"use client";

import { motion } from "framer-motion";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

interface AgentInfo {
  name: string;
  model_id: string;
  description: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  timeout: number;
  max_iterations: number;
  stream_events: boolean;
}

interface SwarmInfo {
  max_handoffs: number;
  max_iterations: number;
  execution_timeout: number;
  node_timeout: number;
  agents: string[];
}

interface AIConfig {
  bedrock_region: string;
  demo_mode: boolean;
  pipeline_timeout: number;
  max_retries: number;
  agents: AgentInfo[];
  swarm: SwarmInfo;
  event_types: string[];
}

interface AIPreferences {
  pipeline_timeout: number;
  auto_process: boolean;
  enable_ws_streaming: boolean;
  risk_threshold_low: number;
  risk_threshold_high: number;
  enable_nft_auto_mint: boolean;
}

const AGENT_ICONS: Record<string, string> = {
  invoice_processing_agent: "📄",
  underwriting_agent: "⚖️",
  nl_query_agent: "🤖",
  collection_agent: "📬",
};

const AGENT_LABELS: Record<string, string> = {
  invoice_processing_agent: "Invoice Processing",
  underwriting_agent: "Underwriting",
  nl_query_agent: "NL Query",
  collection_agent: "Collection",
};

const MODEL_BADGES: Record<string, { label: string; color: string }> = {
  sonnet: { label: "Sonnet 4.6", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  opus: { label: "Opus 4.6", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  haiku: { label: "Haiku 4.5", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
};

function getModelBadge(modelId: string) {
  if (modelId.includes("sonnet")) return MODEL_BADGES.sonnet;
  if (modelId.includes("opus")) return MODEL_BADGES.opus;
  if (modelId.includes("haiku")) return MODEL_BADGES.haiku;
  return { label: modelId, color: "bg-slate-500/20 text-slate-400 border-slate-500/30" };
}

// Default values when API fails
const DEFAULT_CONFIG: AIConfig = {
  bedrock_region: "us-east-1",
  demo_mode: false,
  pipeline_timeout: 120,
  max_retries: 2,
  agents: [
    { name: "invoice_processing_agent", model_id: "us.anthropic.claude-sonnet-4-6-v1", description: "Processes invoices through 10-step analysis pipeline", temperature: 0.1, max_tokens: 4096, top_p: 0.9, timeout: 60, max_iterations: 15, stream_events: true },
    { name: "underwriting_agent", model_id: "us.anthropic.claude-sonnet-4-6-v1", description: "Makes autonomous underwriting decisions", temperature: 0.0, max_tokens: 4096, top_p: 1.0, timeout: 60, max_iterations: 10, stream_events: true },
    { name: "nl_query_agent", model_id: "us.anthropic.claude-opus-4-6-v1", description: "Natural language portfolio queries (standalone)", temperature: 0.3, max_tokens: 2048, top_p: 0.95, timeout: 30, max_iterations: 5, stream_events: true },
    { name: "collection_agent", model_id: "us.anthropic.claude-haiku-4-5-20251001", description: "Overdue invoice monitoring (deferred)", temperature: 0.1, max_tokens: 2048, top_p: 0.9, timeout: 30, max_iterations: 8, stream_events: true },
  ],
  swarm: { max_handoffs: 5, max_iterations: 10, execution_timeout: 120, node_timeout: 60, agents: ["invoice_processing_agent", "underwriting_agent"] },
  event_types: ["tool_start", "tool_complete", "agent_thinking", "agent_handoff", "pipeline_complete", "pipeline_error"],
};

const DEFAULT_PREFS: AIPreferences = {
  pipeline_timeout: 120,
  auto_process: true,
  enable_ws_streaming: true,
  risk_threshold_low: 70,
  risk_threshold_high: 40,
  enable_nft_auto_mint: true,
};

export default function SettingsPage() {
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [prefs, setPrefs] = useState<AIPreferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState<"agents" | "preferences" | "swarm">("agents");

  const fetchData = useCallback(async () => {
    try {
      const [configRes, prefsRes] = await Promise.all([
        api.getAIConfig().catch(() => DEFAULT_CONFIG),
        api.getAIPreferences().catch(() => DEFAULT_PREFS),
      ]);
      setConfig(configRes);
      setPrefs(prefsRes);
    } catch {
      setConfig(DEFAULT_CONFIG);
      setPrefs(DEFAULT_PREFS);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  async function handleSavePrefs() {
    setSaving(true);
    setSaved(false);
    try {
      const res = await api.updateAIPreferences(prefs);
      setPrefs(res);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    setSaving(false);
  }

  function updatePref<K extends keyof AIPreferences>(key: K, value: AIPreferences[K]) {
    setPrefs((p) => ({ ...p, [key]: value }));
  }

  const activeConfig = config || DEFAULT_CONFIG;

  return (
    <div>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="section-title">AI Settings</h1>
        <p className="mt-1 text-sm text-slate-400">
          View AI agent configuration and customize your processing preferences.
        </p>
      </motion.div>

      {/* System Status Bar */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-6 glass-card p-4"
      >
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-slate-400">Region:</span>
            <span className="font-mono text-slate-200">{activeConfig.bedrock_region}</span>
          </div>
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${activeConfig.demo_mode ? "bg-yellow-400 animate-pulse" : "bg-emerald-400"}`} />
            <span className="text-slate-400">Mode:</span>
            <span className={`font-medium ${activeConfig.demo_mode ? "text-yellow-400" : "text-emerald-400"}`}>
              {activeConfig.demo_mode ? "Demo" : "Production"}
            </span>
          </div>
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Pipeline Timeout:</span>
            <span className="font-mono text-slate-200">{activeConfig.pipeline_timeout}s</span>
          </div>
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Max Retries:</span>
            <span className="font-mono text-slate-200">{activeConfig.max_retries}</span>
          </div>
        </div>
      </motion.div>

      {/* Tab Switcher */}
      <div className="mt-6 flex gap-1 rounded-lg bg-slate-800/50 p-1 w-fit">
        {([
          { key: "agents" as const, label: "Agent Roster", icon: "🧠" },
          { key: "preferences" as const, label: "My Preferences", icon: "⚙️" },
          { key: "swarm" as const, label: "Swarm Pipeline", icon: "🔄" },
        ]).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all ${
              tab === t.key
                ? "bg-blue-500/15 text-blue-400 shadow-inner shadow-blue-500/10"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="mt-8 flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500/30 border-t-blue-500" />
        </div>
      ) : (
        <>
          {/* --- Tab: Agent Roster --- */}
          {tab === "agents" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2"
            >
              {activeConfig.agents.map((agent, i) => {
                const badge = getModelBadge(agent.model_id);
                const isInSwarm = activeConfig.swarm.agents.includes(agent.name);
                const isDeferred = agent.name === "collection_agent";
                return (
                  <motion.div
                    key={agent.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className={`glass-card p-5 ${isDeferred ? "opacity-60" : ""}`}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{AGENT_ICONS[agent.name] || "🤖"}</span>
                        <div>
                          <h3 className="text-sm font-semibold text-slate-200">
                            {AGENT_LABELS[agent.name] || agent.name}
                          </h3>
                          <p className="text-xs text-slate-500 mt-0.5">{agent.description}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${badge.color}`}>
                          {badge.label}
                        </span>
                        {isInSwarm && (
                          <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] text-indigo-400">
                            Swarm
                          </span>
                        )}
                        {isDeferred && (
                          <span className="rounded-full border border-yellow-500/30 bg-yellow-500/10 px-2 py-0.5 text-[10px] text-yellow-400">
                            Deferred
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Parameters Grid */}
                    <div className="mt-4 grid grid-cols-3 gap-3">
                      <div className="rounded-lg bg-slate-800/50 p-2.5 text-center">
                        <p className="text-[10px] text-slate-500 uppercase">Temp</p>
                        <p className="text-sm font-bold text-slate-200 mt-0.5">{agent.temperature}</p>
                      </div>
                      <div className="rounded-lg bg-slate-800/50 p-2.5 text-center">
                        <p className="text-[10px] text-slate-500 uppercase">Max Tokens</p>
                        <p className="text-sm font-bold text-slate-200 mt-0.5">{agent.max_tokens.toLocaleString()}</p>
                      </div>
                      <div className="rounded-lg bg-slate-800/50 p-2.5 text-center">
                        <p className="text-[10px] text-slate-500 uppercase">Top-P</p>
                        <p className="text-sm font-bold text-slate-200 mt-0.5">{agent.top_p}</p>
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="mt-3 flex justify-between text-[10px] text-slate-500">
                      <span>Timeout: {agent.timeout}s</span>
                      <span>Max Iterations: {agent.max_iterations}</span>
                      <span>
                        Streaming: {agent.stream_events ? (
                          <span className="text-emerald-400">ON</span>
                        ) : (
                          <span className="text-red-400">OFF</span>
                        )}
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          )}

          {/* --- Tab: User Preferences --- */}
          {tab === "preferences" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 max-w-2xl space-y-6"
            >
              {/* Pipeline Settings */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <span>⚡</span> Pipeline Settings
                </h3>
                <div className="space-y-5">
                  {/* Pipeline Timeout */}
                  <div>
                    <label className="flex items-center justify-between">
                      <span className="text-sm text-slate-300">Pipeline Timeout</span>
                      <span className="font-mono text-sm text-blue-400">{prefs.pipeline_timeout}s</span>
                    </label>
                    <input
                      type="range"
                      min={30}
                      max={300}
                      step={10}
                      value={prefs.pipeline_timeout}
                      onChange={(e) => updatePref("pipeline_timeout", Number(e.target.value))}
                      className="mt-2 w-full accent-blue-500"
                    />
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                      <span>30s (fast)</span>
                      <span>300s (thorough)</span>
                    </div>
                  </div>

                  {/* Auto Process */}
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-300">Auto-process after upload</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Automatically start the 14-step pipeline when an invoice is uploaded
                      </p>
                    </div>
                    <button
                      onClick={() => updatePref("auto_process", !prefs.auto_process)}
                      className={`relative h-6 w-11 rounded-full transition-colors ${
                        prefs.auto_process ? "bg-blue-500" : "bg-slate-700"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                          prefs.auto_process ? "translate-x-5" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </div>

                  {/* WebSocket Streaming */}
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-300">Real-time streaming</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Stream agent events via WebSocket during processing
                      </p>
                    </div>
                    <button
                      onClick={() => updatePref("enable_ws_streaming", !prefs.enable_ws_streaming)}
                      className={`relative h-6 w-11 rounded-full transition-colors ${
                        prefs.enable_ws_streaming ? "bg-blue-500" : "bg-slate-700"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                          prefs.enable_ws_streaming ? "translate-x-5" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </div>

                  {/* Auto-mint NFT */}
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-300">Auto-mint NFT on approval</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Automatically mint ARC-69 NFT when an invoice is approved
                      </p>
                    </div>
                    <button
                      onClick={() => updatePref("enable_nft_auto_mint", !prefs.enable_nft_auto_mint)}
                      className={`relative h-6 w-11 rounded-full transition-colors ${
                        prefs.enable_nft_auto_mint ? "bg-blue-500" : "bg-slate-700"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                          prefs.enable_nft_auto_mint ? "translate-x-5" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>

              {/* Risk Thresholds */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <span>📊</span> Risk Thresholds
                </h3>
                <div className="space-y-5">
                  {/* Low Risk Threshold */}
                  <div>
                    <label className="flex items-center justify-between">
                      <span className="text-sm text-slate-300">Low Risk Threshold</span>
                      <span className="font-mono text-sm text-emerald-400">≥ {prefs.risk_threshold_low}</span>
                    </label>
                    <p className="text-xs text-slate-500 mt-0.5 mb-2">
                      Invoices with risk score at or above this are considered low risk
                    </p>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={prefs.risk_threshold_low}
                      onChange={(e) => updatePref("risk_threshold_low", Number(e.target.value))}
                      className="w-full accent-emerald-500"
                    />
                  </div>

                  {/* High Risk Threshold */}
                  <div>
                    <label className="flex items-center justify-between">
                      <span className="text-sm text-slate-300">High Risk Threshold</span>
                      <span className="font-mono text-sm text-red-400">&lt; {prefs.risk_threshold_high}</span>
                    </label>
                    <p className="text-xs text-slate-500 mt-0.5 mb-2">
                      Invoices with risk score below this are considered high risk
                    </p>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={prefs.risk_threshold_high}
                      onChange={(e) => updatePref("risk_threshold_high", Number(e.target.value))}
                      className="w-full accent-red-500"
                    />
                  </div>

                  {/* Visual Preview */}
                  <div className="rounded-lg bg-slate-800/50 p-3">
                    <p className="text-[10px] text-slate-500 uppercase mb-2">Risk Scale Preview</p>
                    <div className="relative h-3 w-full rounded-full bg-slate-700 overflow-hidden">
                      <div
                        className="absolute left-0 top-0 h-full bg-red-500/60"
                        style={{ width: `${prefs.risk_threshold_high}%` }}
                      />
                      <div
                        className="absolute top-0 h-full bg-yellow-500/60"
                        style={{ left: `${prefs.risk_threshold_high}%`, width: `${prefs.risk_threshold_low - prefs.risk_threshold_high}%` }}
                      />
                      <div
                        className="absolute top-0 h-full bg-emerald-500/60"
                        style={{ left: `${prefs.risk_threshold_low}%`, width: `${100 - prefs.risk_threshold_low}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] mt-1">
                      <span className="text-red-400">High (&lt;{prefs.risk_threshold_high})</span>
                      <span className="text-yellow-400">Medium ({prefs.risk_threshold_high}-{prefs.risk_threshold_low})</span>
                      <span className="text-emerald-400">Low (≥{prefs.risk_threshold_low})</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Save Button */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handleSavePrefs}
                  disabled={saving}
                  className="btn-glow px-6 py-2.5 text-sm font-medium disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Preferences"}
                </button>
                {saved && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-sm text-emerald-400"
                  >
                    ✓ Saved successfully
                  </motion.span>
                )}
              </div>
            </motion.div>
          )}

          {/* --- Tab: Swarm Pipeline --- */}
          {tab === "swarm" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 space-y-6 max-w-3xl"
            >
              {/* Swarm Config */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <span>🔄</span> Swarm Configuration
                </h3>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                    <p className="text-[10px] text-slate-500 uppercase">Max Handoffs</p>
                    <p className="text-lg font-bold text-slate-200 mt-1">{activeConfig.swarm.max_handoffs}</p>
                  </div>
                  <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                    <p className="text-[10px] text-slate-500 uppercase">Max Iterations</p>
                    <p className="text-lg font-bold text-slate-200 mt-1">{activeConfig.swarm.max_iterations}</p>
                  </div>
                  <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                    <p className="text-[10px] text-slate-500 uppercase">Exec Timeout</p>
                    <p className="text-lg font-bold text-slate-200 mt-1">{activeConfig.swarm.execution_timeout}s</p>
                  </div>
                  <div className="rounded-lg bg-slate-800/50 p-3 text-center">
                    <p className="text-[10px] text-slate-500 uppercase">Node Timeout</p>
                    <p className="text-lg font-bold text-slate-200 mt-1">{activeConfig.swarm.node_timeout}s</p>
                  </div>
                </div>
              </div>

              {/* Pipeline Flow */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <span>🔗</span> Agent Pipeline Flow
                </h3>
                <div className="flex items-center gap-3 overflow-x-auto pb-2">
                  {/* Invoice Agent */}
                  <div className="flex-shrink-0 rounded-lg border border-blue-500/20 bg-blue-500/5 p-3 min-w-[180px]">
                    <div className="flex items-center gap-2">
                      <span>📄</span>
                      <span className="text-xs font-semibold text-blue-400">Invoice Processing</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">Steps 1-10: Extract → Risk</p>
                    <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-[10px] font-medium ${MODEL_BADGES.sonnet.color}`}>
                      Sonnet 4.6
                    </span>
                  </div>

                  {/* Arrow */}
                  <div className="flex flex-col items-center flex-shrink-0">
                    <span className="text-xs text-slate-500">handoff</span>
                    <span className="text-blue-400 text-lg">→</span>
                  </div>

                  {/* Underwriting Agent */}
                  <div className="flex-shrink-0 rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-3 min-w-[180px]">
                    <div className="flex items-center gap-2">
                      <span>⚖️</span>
                      <span className="text-xs font-semibold text-indigo-400">Underwriting</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">Steps 11-13: Validate → Decide</p>
                    <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-[10px] font-medium ${MODEL_BADGES.sonnet.color}`}>
                      Sonnet 4.6
                    </span>
                  </div>

                  {/* Arrow back */}
                  <div className="flex flex-col items-center flex-shrink-0">
                    <span className="text-xs text-slate-500">if approved</span>
                    <span className="text-emerald-400 text-lg">→</span>
                  </div>

                  {/* Mint NFT */}
                  <div className="flex-shrink-0 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 min-w-[140px]">
                    <div className="flex items-center gap-2">
                      <span>🎨</span>
                      <span className="text-xs font-semibold text-emerald-400">Mint NFT</span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">Step 14: ARC-69 on Algorand</p>
                  </div>
                </div>
              </div>

              {/* Event Types */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <span>📡</span> WebSocket Event Types
                </h3>
                <div className="flex flex-wrap gap-2">
                  {activeConfig.event_types.map((evt) => (
                    <span
                      key={evt}
                      className="rounded-full border border-slate-600 bg-slate-800/50 px-3 py-1 text-xs font-mono text-slate-300"
                    >
                      {evt}
                    </span>
                  ))}
                </div>
              </div>

              {/* Standalone Agents */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <span>🤖</span> Standalone Agents (Not in Swarm)
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg bg-slate-800/30 p-3">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">🤖</span>
                      <div>
                        <p className="text-xs font-semibold text-purple-400">NL Query Agent</p>
                        <p className="text-[10px] text-slate-500">On-demand portfolio analysis. Dashboard query bar.</p>
                      </div>
                    </div>
                    <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${MODEL_BADGES.opus.color}`}>
                      Opus 4.6
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-slate-800/30 p-3 opacity-50">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">📬</span>
                      <div>
                        <p className="text-xs font-semibold text-emerald-400">Collection Agent</p>
                        <p className="text-[10px] text-slate-500">Overdue monitoring. Deferred to Round 3.</p>
                      </div>
                    </div>
                    <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${MODEL_BADGES.haiku.color}`}>
                      Haiku 4.5
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
}
