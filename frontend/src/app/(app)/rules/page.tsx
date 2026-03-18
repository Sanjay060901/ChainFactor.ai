"use client";

/**
 * Seller rules page skeleton.
 * TODO: Wire to api.listRules(), api.createRule(), etc.
 * See wireframes.md Screen 7 for layout reference.
 */

export default function RulesPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Auto-Approve Rules</h1>
      <p className="mt-1 text-sm text-gray-500">
        Set conditions for automatic invoice approval.
      </p>

      {/* Rule 1 */}
      <div className="mt-6 space-y-4">
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">Rule 1</h3>
            <button className="text-sm text-red-500 hover:underline">
              Delete
            </button>
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">IF</span>
              <span>invoice amount</span>
              <select className="rounded border px-2 py-1 text-sm">
                <option>is less than</option>
              </select>
              <span>₹</span>
              <input
                type="text"
                defaultValue="5,00,000"
                className="w-28 rounded border px-2 py-1 text-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">AND</span>
              <span>risk score</span>
              <select className="rounded border px-2 py-1 text-sm">
                <option>is greater than</option>
              </select>
              <input
                type="text"
                defaultValue="60"
                className="w-20 rounded border px-2 py-1 text-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">AND</span>
              <span>fraud flags</span>
              <select className="rounded border px-2 py-1 text-sm">
                <option>equals</option>
              </select>
              <input
                type="text"
                defaultValue="0"
                className="w-20 rounded border px-2 py-1 text-sm"
              />
            </div>
            <p className="text-gray-500">
              THEN → <span className="font-medium text-green-600">Auto-approve</span>
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-green-600">✅ Active</span>
            <button className="rounded border px-3 py-1 text-xs text-gray-500 hover:bg-gray-50">
              Toggle
            </button>
          </div>
        </div>

        {/* Rule 2 */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">Rule 2</h3>
            <button className="text-sm text-red-500 hover:underline">
              Delete
            </button>
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">IF</span>
              <span>amount &lt; ₹10,00,000</span>
              <span className="text-gray-500">AND</span>
              <span>risk &gt; 80</span>
              <span className="text-gray-500">AND</span>
              <span>CIBIL &gt; 700</span>
            </div>
            <p className="text-gray-500">
              THEN → <span className="font-medium text-green-600">Auto-approve</span>
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-green-600">✅ Active</span>
            <button className="rounded border px-3 py-1 text-xs text-gray-500 hover:bg-gray-50">
              Toggle
            </button>
          </div>
        </div>
      </div>

      {/* Add Rule */}
      <button className="mt-4 rounded-lg border-2 border-dashed border-gray-300 px-6 py-3 text-sm font-medium text-gray-500 hover:border-primary-400 hover:text-primary-600">
        + Add New Rule
      </button>

      {/* Default Behavior */}
      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700">Default Behavior</h3>
        <p className="mt-1 text-sm text-gray-500">When no rules match:</p>
        <select className="mt-2 rounded-lg border border-gray-300 px-3 py-2 text-sm">
          <option>Flag for manual review</option>
          <option>Reject</option>
          <option>Always approve</option>
        </select>
      </div>

      <button className="mt-6 rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-700">
        Save
      </button>
    </div>
  );
}
