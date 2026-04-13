"use client";

import { usePathname } from "next/navigation";

/**
 * Extract the real invoice ID from the browser URL path.
 * Next.js static export pre-renders [id] pages with params.id = "placeholder",
 * but the actual UUID is in the browser URL after client-side navigation.
 */
export function useInvoiceId(paramsId: string): string {
  const pathname = usePathname();
  const segments = pathname.split("/");
  const idx = segments.indexOf("invoices");
  if (idx !== -1 && idx + 1 < segments.length) {
    const id = segments[idx + 1];
    if (id && id !== "placeholder") return id;
  }
  return paramsId;
}
