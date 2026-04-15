"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { PERA_EXPLORER_BASE } from "@/lib/constants";

interface NFTCardProps {
  invoiceId: string;
  invoiceNumber?: string;
  sellerName?: string;
  buyerName?: string;
  amount?: number;
  riskScore?: number;
  assetId?: number | null;
  status?: string;
  metadata?: Record<string, unknown>;
  /** Show the Claim NFT button (default true when status is approved or minted) */
  showClaimButton?: boolean;
}

/**
 * NFTCard — displays Algorand ASA details for a verified invoice NFT.
 *
 * Used on:
 *  - Invoice Detail page (read-only preview with Claim CTA)
 *  - Claim page (interactive, embedded inside the flow)
 *
 * Shows: ASA ID, metadata snippet, risk score, Pera Explorer link,
 *        and a Claim CTA that routes to /invoices/[id]/claim.
 */
export function NFTCard({
  invoiceId,
  invoiceNumber,
  sellerName,
  buyerName,
  amount,
  riskScore = 0,
  assetId,
  status = "approved",
  metadata,
  showClaimButton,
}: NFTCardProps) {
  const isMinted = !!assetId;
  const canClaim = showClaimButton ?? (status === "approved" || status === "minted");

  const riskColor =
    riskScore >= 70
      ? "text-emerald-400"
      : riskScore >= 40
        ? "text-yellow-400"
        : "text-red-400";

  const riskLabel =
    riskScore >= 70 ? "Low" : riskScore >= 40 ? "Medium" : "High";

  const explorerUrl = assetId
    ? `${PERA_EXPLORER_BASE}/asset/${assetId}/`
    : null;

  // Pull metadata properties if available
  const props =
    metadata && typeof metadata.properties === "object" && metadata.properties !== null
      ? (metadata.properties as Record<string, unknown>)
      : {};

  const displaySeller =
    sellerName || (typeof props.seller === "string" ? props.seller : null) || "—";
  const displayBuyer =
    buyerName || (typeof props.buyer === "string" ? props.buyer : null) || "—";
  const displayNumber =
    invoiceNumber ||
    (typeof props.invoice_number === "string" ? props.invoice_number : null) ||
    "—";
  const displayAmount =
    amount ??
    (typeof props.amount === "number" ? props.amount : null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-500/10 via-slate-900/90 to-indigo-500/10 p-6 shadow-xl shadow-blue-500/10"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-blue-400">
            ChainFactor AI
          </p>
          <p className="text-[10px] text-slate-500">INVOICE NFT · ARC-69</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-sm font-bold text-white shadow-lg shadow-blue-500/30">
          ⛓️
        </div>
      </div>

      {/* Invoice info */}
      <div className="mt-5">
        <p className="text-lg font-bold text-slate-100">{displayNumber}</p>
        <p className="mt-0.5 text-sm text-slate-400">
          {displaySeller} → {displayBuyer}
        </p>
        {displayAmount != null && (
          <p className="mt-2 text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            ₹{Math.round(Number(displayAmount)).toLocaleString("en-IN")}
          </p>
        )}
      </div>

      {/* Risk + Status row */}
      <div className="mt-5 flex items-center justify-between">
        <div>
          <p className="text-[10px] text-slate-500">Risk Score</p>
          <p className={`text-sm font-semibold ${riskColor}`}>
            {riskScore} ({riskLabel})
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-slate-500">Status</p>
          <p
            className={`text-sm font-semibold ${
              status === "minted" || status === "claimed"
                ? "text-purple-400"
                : status === "approved"
                  ? "text-emerald-400"
                  : "text-slate-400"
            }`}
          >
            {status.toUpperCase()}
          </p>
        </div>
      </div>

      {/* ASA / Algorand footer */}
      <div className="mt-5 border-t border-blue-500/10 pt-4">
        {isMinted ? (
          <div className="flex items-center justify-between">
            <p className="font-mono text-xs text-blue-300">ASA #{assetId}</p>
            <p className="text-[10px] text-slate-500">Algorand Testnet</p>
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">
            NFT will be minted after approval
          </p>
        )}

        {/* Metadata description snippet */}
        {metadata && typeof metadata.description === "string" && (
          <p className="mt-2 text-[11px] text-slate-500 leading-relaxed line-clamp-2">
            {metadata.description}
          </p>
        )}
      </div>

      {/* Action buttons */}
      <div className="mt-5 flex flex-wrap items-center gap-3">
        {explorerUrl && (
          <a
            href={explorerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-300 transition-all hover:bg-blue-500/20 hover:text-blue-200"
          >
            Pera Explorer ↗
          </a>
        )}
        {canClaim && (
          <Link
            href={`/invoices/${invoiceId}/claim`}
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-all hover:from-blue-500 hover:to-indigo-500"
          >
            {status === "minted" ? "Claim NFT →" : "Mint & Claim →"}
          </Link>
        )}
      </div>
    </motion.div>
  );
}
