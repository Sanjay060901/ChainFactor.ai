"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useWallet } from "@txnlab/use-wallet-react";
import { useAuth } from "@/hooks/useAuth";
import { useEffect, useRef, useState } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/invoices", label: "Invoices", icon: "📋" },
  { href: "/rules", label: "Rules", icon: "⚖️" },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { activeWallet, activeAccount, wallets } = useWallet();

  const connected = !!activeAccount;
  const shortAddr = activeAccount?.address
    ? `${activeAccount.address.slice(0, 4)}...${activeAccount.address.slice(-4)}`
    : null;

  async function handleWalletClick() {
    if (connected && activeWallet) {
      activeWallet.disconnect();
    } else {
      // Connect with first available wallet (Pera)
      const wallet = wallets?.[0];
      if (wallet) {
        try {
          await wallet.connect();
        } catch {
          // user cancelled
        }
      }
    }
  }

  function handleLogout() {
    logout();
    router.push("/auth/login");
  }

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav className="sticky top-0 z-50 border-b border-blue-500/10 bg-slate-900/70 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-sm font-bold text-white shadow-lg shadow-blue-500/25">
              C
            </div>
            <span className="text-lg font-bold text-gradient">
              ChainFactor AI
            </span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-blue-500/15 text-blue-400 shadow-inner shadow-blue-500/10"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  <span className="text-sm">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Wallet + User */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleWalletClick}
              className={`flex items-center gap-2 rounded-full border px-4 py-1.5 transition-colors ${
                connected
                  ? "border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20"
                  : "border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/15"
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-yellow-400 animate-pulse"}`} />
              <span className="text-xs font-medium text-slate-400">
                {connected ? `🔗 ${shortAddr}` : "Connect Wallet"}
              </span>
            </button>
            <div className="relative" ref={dropdownRef}>
              <div
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/20 text-xs font-medium text-blue-400 cursor-pointer"
              >
                {user?.name?.charAt(0)?.toUpperCase() || "S"}
              </div>
              {dropdownOpen && (
                <div className="absolute right-0 top-10 w-48 rounded-lg border border-blue-500/20 bg-slate-900/95 backdrop-blur-xl p-2 shadow-xl z-50">
                  <p className="px-3 py-1.5 text-xs text-slate-400">{user?.name || "User"}</p>
                  <p className="px-3 pb-1.5 text-[10px] text-slate-600">{user?.email || ""}</p>
                  <hr className="border-slate-800 my-1" />
                  <button onClick={handleLogout} className="w-full rounded-md px-3 py-1.5 text-left text-xs text-red-400 hover:bg-red-500/10 transition-colors">
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
