"use client";

/**
 * Invoice detail page skeleton.
 * TODO: Wire to api.getInvoice(), display all AI analysis sections.
 * See wireframes.md Screen 5 for layout reference.
 */

import Link from "next/link";

export default function InvoiceDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div>
      <Link href="/invoices" className="text-sm text-gray-500 hover:underline">
        ← Back to Invoices
      </Link>

      <div className="mt-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Invoice INV-2026-001
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Status: ✅ Approved &nbsp; NFT: Minted (ASA #12345678)
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href={`/invoices/${params.id}/claim`}
            className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            Claim NFT
          </Link>
          <Link
            href={`/invoices/${params.id}/audit`}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Audit Trail
          </Link>
        </div>
      </div>

      {/* Extracted Data */}
      <section className="mt-6 rounded-lg bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Extracted Data</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Seller:</span> Acme Technologies Pvt Ltd</div>
          <div><span className="text-gray-500">GSTIN:</span> 27AABCU9603R1ZM</div>
          <div><span className="text-gray-500">Buyer:</span> TechBuild Solutions</div>
          <div><span className="text-gray-500">GSTIN:</span> 29AABCT1234R1ZX</div>
          <div><span className="text-gray-500">Invoice #:</span> INV-2026-001</div>
          <div><span className="text-gray-500">Date:</span> 2026-03-15</div>
          <div><span className="text-gray-500">Amount:</span> ₹5,20,000</div>
          <div><span className="text-gray-500">Tax:</span> ₹93,600 (18% GST)</div>
          <div><span className="text-gray-500">Total:</span> ₹6,13,600</div>
          <div><span className="text-gray-500">Due:</span> 2026-04-14</div>
        </div>
      </section>

      {/* AI Analysis */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900">Risk Score</h3>
          <p className="mt-2 text-3xl font-bold text-green-600">82 / 100</p>
          <p className="text-sm text-green-600">LOW RISK</p>
        </div>
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900">GST Compliance</h3>
          <p className="mt-2 text-lg font-medium text-green-600">✅ Compliant</p>
          <p className="text-sm text-gray-500">HSN valid, rates match, e-invoice present</p>
        </div>
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900">GSTIN</h3>
          <p className="mt-2 text-lg font-medium text-green-600">✅ Verified</p>
          <p className="text-sm text-gray-500">Active, matched to Acme Technologies</p>
        </div>
      </div>

      {/* Fraud Detection */}
      <section className="mt-4 rounded-lg bg-white p-6 shadow-sm">
        <h3 className="font-semibold text-gray-900">Fraud Detection (5-Layer)</h3>
        <div className="mt-3 space-y-2">
          {["Document Integrity", "Financial Consistency", "Pattern Analysis", "Entity Verification", "Cross-Reference"].map((layer) => (
            <div key={layer} className="flex items-center justify-between text-sm">
              <span className="text-gray-700">{layer}</span>
              <span className="text-green-600">✅ Pass</span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-sm text-gray-500">Flags: 0 &nbsp; Confidence: 97%</p>
      </section>

      {/* Underwriting Decision */}
      <section className="mt-4 rounded-lg bg-white p-6 shadow-sm">
        <h3 className="font-semibold text-gray-900">Underwriting Decision</h3>
        <p className="mt-2 text-lg font-medium text-green-600">AUTO-APPROVED</p>
        <p className="mt-1 text-sm text-gray-500">Rule matched: &quot;Approve invoices under ₹10L with risk score &gt; 80&quot;</p>
        <p className="mt-1 text-sm text-gray-500">Cross-validation: PASSED</p>
      </section>

      {/* AI Explanation */}
      <section className="mt-4 rounded-lg bg-white p-6 shadow-sm">
        <h3 className="font-semibold text-gray-900">AI Risk Explanation</h3>
        <p className="mt-2 text-sm text-gray-600">
          This invoice presents low risk. The seller has an active GSTIN with consistent filing history.
          The buyer has a CIBIL score of 750 and has paid all 8 previous invoices on time. GST rates
          match the applicable slab for HSN 998314. No fraud indicators detected across all 5 layers.
        </p>
      </section>
    </div>
  );
}
