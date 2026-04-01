"use client";

import { NFTCard } from "@/components/invoice/NFTCard";

/**
 * NFT Preview Page — shows NFTCard in different states.
 * Temporary page for UI review. Owner: Jeevidha.
 */
export default function NFTPreviewPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-10 py-8">
      <h1 className="text-2xl font-bold text-slate-100">NFT Card Preview</h1>
      <p className="text-sm text-slate-500 -mt-6">
        These are all the visual states of your NFTCard component.
      </p>

      {/* State 1: Minted — has ASA ID, Pera Explorer link, Claim button */}
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">
          State 1 — Minted (has ASA ID, can claim)
        </p>
        <NFTCard
          invoiceId="inv-002"
          invoiceNumber="INV-2024-0042"
          sellerName="Infosys Technologies Ltd"
          buyerName="HDFC Bank Ltd"
          amount={4250000}
          riskScore={82}
          assetId={757705537}
          status="minted"
          metadata={{
            standard: "arc69",
            description:
              "ChainFactor AI verified invoice INV-2024-0042 from Infosys Technologies Ltd to HDFC Bank Ltd.",
            properties: {
              invoice_number: "INV-2024-0042",
              seller: "Infosys Technologies Ltd",
              buyer: "HDFC Bank Ltd",
              amount: 4250000,
              risk_score: 82,
              risk_level: "low",
              date: "2024-03-15",
            },
          }}
          showClaimButton={true}
        />
      </div>

      {/* State 2: Approved — no ASA yet, shows "Mint & Claim" button */}
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-emerald-400">
          State 2 — Approved (not yet minted, ready to claim)
        </p>
        <NFTCard
          invoiceId="inv-001"
          invoiceNumber="INV-2024-0039"
          sellerName="Tata Steel Ltd"
          buyerName="Reliance Industries"
          amount={1875000}
          riskScore={74}
          assetId={null}
          status="approved"
          showClaimButton={true}
        />
      </div>

      {/* State 3: Medium risk */}
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-yellow-400">
          State 3 — Medium Risk Score
        </p>
        <NFTCard
          invoiceId="inv-003"
          invoiceNumber="INV-2024-0055"
          sellerName="Wipro Ltd"
          buyerName="State Bank of India"
          amount={750000}
          riskScore={51}
          assetId={799901234}
          status="minted"
          showClaimButton={true}
        />
      </div>

      {/* State 4: High risk / rejected */}
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-red-400">
          State 4 — High Risk / Rejected (no claim button)
        </p>
        <NFTCard
          invoiceId="inv-004"
          invoiceNumber="INV-2024-0099"
          sellerName="Suspicious Corp Pvt Ltd"
          buyerName="Unknown Buyer"
          amount={9999999}
          riskScore={18}
          assetId={null}
          status="rejected"
          showClaimButton={false}
        />
      </div>
    </div>
  );
}
