"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/invoices", label: "Invoices" },
  { href: "/rules", label: "Rules" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2">
            <span className="text-xl font-bold text-primary-700">
              ChainFactor AI
            </span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-6">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm font-medium ${
                  pathname?.startsWith(item.href)
                    ? "text-primary-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Wallet + User (placeholder) */}
          <div className="flex items-center gap-4">
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">
              Wallet: Not connected
            </span>
            <span className="text-sm font-medium text-gray-700">User</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
