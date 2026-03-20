"use client";

import { motion } from "framer-motion";

export default function UploadPage() {
  return (
    <div>
      <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="section-title">
        Upload Invoice
      </motion.h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-6 glass-card p-8"
      >
        {/* Drop zone */}
        <motion.div
          whileHover={{ scale: 1.01, borderColor: "rgba(59, 130, 246, 0.5)" }}
          className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-blue-500/20 bg-blue-500/5 p-16 transition-colors cursor-pointer"
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="text-5xl"
          >
            📄
          </motion.div>
          <p className="mt-4 text-sm font-medium text-slate-200">Drop PDF here</p>
          <p className="mt-1 text-xs text-slate-500">or click to browse</p>
          <p className="mt-2 text-xs text-slate-600">Max 5MB, PDF only</p>
          <input
            type="file"
            accept=".pdf"
            className="mt-6 text-sm text-slate-400 file:mr-4 file:rounded-lg file:border file:border-blue-500/30 file:bg-blue-500/10 file:px-4 file:py-2 file:text-sm file:font-medium file:text-blue-400 hover:file:bg-blue-500/20 file:transition-colors file:cursor-pointer"
          />
        </motion.div>

        {/* After file selected */}
        <div className="mt-6 hidden rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-300">📄 invoice_march_2026.pdf (1.2 MB)</span>
            <button className="text-sm text-red-400 hover:text-red-300 transition-colors">Remove</button>
          </div>
          <button className="btn-glow mt-4 w-full py-3 text-sm">🚀 Process Invoice</button>
        </div>
      </motion.div>
    </div>
  );
}
