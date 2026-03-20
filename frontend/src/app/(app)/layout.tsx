/**
 * Layout for authenticated app pages (dashboard, invoices, rules).
 * Includes navbar. Auth pages have their own layout.
 */

import { Navbar } from "@/components/layout/navbar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen mesh-bg">
      <div className="absolute inset-0 grid-pattern pointer-events-none" />
      <div className="relative z-10">
        <Navbar />
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
