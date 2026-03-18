"use client";

/**
 * Dashboard page skeleton.
 * TODO: Wire to api.dashboardSummary(), add charts (recharts or chart.js),
 * add NL query bar, add recent invoices table.
 * See wireframes.md Screen 2 for layout reference.
 */

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stat Cards */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Value", value: "₹45,20,000", change: "↑ 12% MTD" },
          { label: "Active Invoices", value: "12", change: "3 pending" },
          { label: "Avg Risk Score", value: "72", change: "↓ from 78" },
          { label: "Approval Rate", value: "85%", change: "↑ from 80%" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg bg-white p-6 shadow-sm"
          >
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className="mt-1 text-2xl font-semibold text-gray-900">
              {stat.value}
            </p>
            <p className="mt-1 text-xs text-gray-400">{stat.change}</p>
          </div>
        ))}
      </div>

      {/* Charts placeholder */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex h-64 items-center justify-center rounded-lg bg-white shadow-sm">
          <p className="text-sm text-gray-400">
            Risk Distribution Chart (TODO: recharts donut)
          </p>
        </div>
        <div className="flex h-64 items-center justify-center rounded-lg bg-white shadow-sm">
          <p className="text-sm text-gray-400">
            Monthly Volume Chart (TODO: recharts bar)
          </p>
        </div>
      </div>

      {/* NL Query Bar */}
      <div className="mt-6 rounded-lg bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">Ask anything:</span>
          <input
            type="text"
            placeholder="Show me high-risk invoices this week..."
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          <button className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
            Ask
          </button>
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="mt-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Invoices
          </h2>
          <a
            href="/invoices"
            className="text-sm text-primary-600 hover:underline"
          >
            View All →
          </a>
        </div>
        <div className="mt-3 overflow-hidden rounded-lg bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Invoice</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Seller</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Risk</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {[
                { id: "INV-001", seller: "Acme Tech", amount: "₹5.2L", risk: 82, status: "Approved" },
                { id: "INV-002", seller: "TechCo", amount: "₹3.1L", risk: 45, status: "Flagged" },
                { id: "INV-003", seller: "BuildRight", amount: "₹8.0L", risk: 91, status: "Minted" },
              ].map((inv) => (
                <tr key={inv.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{inv.id}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{inv.seller}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{inv.amount}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{inv.risk}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{inv.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
