"use client";

/**
 * Claim NFT page skeleton.
 * TODO: Wire to wallet opt-in transaction, then api.nftClaim().
 * See wireframes.md Screen 6 for layout reference.
 */

export default function ClaimNFTPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">
        Claim Your Invoice NFT
      </h1>

      <div className="mt-6 rounded-lg bg-white p-8 shadow-sm">
        {/* NFT Card */}
        <div className="mx-auto max-w-sm rounded-xl border-2 border-primary-200 bg-gradient-to-br from-primary-50 to-white p-6">
          <p className="text-xs font-medium uppercase text-primary-600">
            ChainFactor AI
          </p>
          <p className="text-xs text-gray-400">INVOICE NFT</p>
          <div className="mt-4">
            <p className="text-lg font-bold text-gray-900">INV-2026-001</p>
            <p className="text-sm text-gray-500">
              Acme Tech → TechBuild
            </p>
            <p className="mt-1 text-xl font-bold text-gray-900">₹6,13,600</p>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400">Risk Score</p>
              <p className="text-sm font-semibold text-green-600">82 (Low)</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Status</p>
              <p className="text-sm font-semibold text-green-600">APPROVED</p>
            </div>
          </div>
          <div className="mt-4 border-t pt-3">
            <p className="text-xs text-gray-400">ASA #12345678</p>
            <p className="text-xs text-gray-400">Algorand Testnet</p>
          </div>
        </div>

        {/* Step 1: Opt-in */}
        <div className="mt-8">
          <h3 className="font-medium text-gray-900">
            Step 1: Opt-in to Asset
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            This will increase your minimum balance by 0.1 ALGO. Your wallet
            will sign an opt-in transaction.
          </p>
          <button className="mt-3 rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-700">
            Opt-in to ASA (0.1 ALGO)
          </button>
        </div>

        {/* Step 2: Claim */}
        <div className="mt-6">
          <h3 className="font-medium text-gray-900">
            Step 2: Receive NFT Transfer
          </h3>
          <button
            disabled
            className="mt-3 rounded-lg bg-gray-300 px-6 py-2.5 text-sm font-medium text-gray-500"
          >
            Claim NFT (after opt-in)
          </button>
        </div>
      </div>
    </div>
  );
}
