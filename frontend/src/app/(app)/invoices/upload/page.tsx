"use client";

/**
 * Invoice upload page skeleton.
 * TODO: Wire to api.uploadInvoice(), handle drag-and-drop, redirect to processing page.
 * See wireframes.md Screen 3 for layout reference.
 */

export default function UploadPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Upload Invoice</h1>

      <div className="mt-6 rounded-lg bg-white p-8 shadow-sm">
        {/* Drop zone */}
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 p-12 hover:border-primary-400">
          <div className="text-4xl">📄</div>
          <p className="mt-4 text-sm font-medium text-gray-700">
            Drop PDF here
          </p>
          <p className="mt-1 text-xs text-gray-500">or click to browse</p>
          <p className="mt-2 text-xs text-gray-400">Max 5MB, PDF only</p>
          <input
            type="file"
            accept=".pdf"
            className="mt-4 text-sm text-gray-500 file:mr-4 file:rounded-lg file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-700 hover:file:bg-primary-100"
          />
        </div>

        {/* After file selected - placeholder */}
        <div className="mt-6 hidden rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">
              📄 invoice_march_2026.pdf (1.2 MB)
            </span>
            <button className="text-sm text-red-500 hover:underline">
              Remove
            </button>
          </div>
          <button className="mt-4 w-full rounded-lg bg-primary-600 py-3 text-sm font-medium text-white hover:bg-primary-700">
            🚀 Process Invoice
          </button>
        </div>
      </div>
    </div>
  );
}
