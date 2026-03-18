"use client";

/**
 * Invoice list page skeleton.
 * TODO: Wire to api.listInvoices(), add filters, pagination, search.
 * See wireframes.md "Invoice List" section for layout reference.
 */

import Link from "next/link";

export default function InvoicesPage() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
        <Link
          href="/invoices/upload"
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
        >
          + Upload New
        </Link>
      </div>

      {/* Filters */}
      <div className="mt-4 flex items-center gap-3">
        <select className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
          <option>All Status</option>
          <option>Processing</option>
          <option>Approved</option>
          <option>Rejected</option>
          <option>Flagged</option>
          <option>Minted</option>
        </select>
        <select className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
          <option>All Risk</option>
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
        </select>
        <input
          type="text"
          placeholder="Search invoices..."
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
        />
      </div>

      {/* Table */}
      <div className="mt-4 overflow-hidden rounded-lg bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Invoice</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Seller</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Risk</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {[
              { id: "inv_stub_001", number: "INV-001", seller: "Acme Technologies", amount: "₹6.1L", risk: 82, status: "Approved" },
              { id: "inv_stub_002", number: "INV-002", seller: "TechCo Solutions", amount: "₹3.1L", risk: 45, status: "Flagged" },
              { id: "inv_stub_003", number: "INV-003", seller: "BuildRight Infra", amount: "₹8.0L", risk: 91, status: "Minted" },
              { id: "inv_stub_004", number: "INV-004", seller: "FakeCorp Ltd", amount: "₹2.1L", risk: 12, status: "Rejected" },
            ].map((inv) => (
              <tr key={inv.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{inv.number}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{inv.seller}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{inv.amount}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{inv.risk}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{inv.status}</td>
                <td className="px-6 py-4 text-sm">
                  <Link href={`/invoices/${inv.id}`} className="text-primary-600 hover:underline">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination placeholder */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <span>Showing 1-4 of 4</span>
        <div className="flex gap-2">
          <button className="rounded border px-3 py-1 hover:bg-gray-100">Prev</button>
          <button className="rounded border bg-primary-50 px-3 py-1 text-primary-600">1</button>
          <button className="rounded border px-3 py-1 hover:bg-gray-100">Next</button>
        </div>
      </div>
    </div>
  );
}
