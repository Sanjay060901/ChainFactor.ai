import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChainFactor AI",
  description:
    "AI-powered invoice financing platform for Indian SMEs on Algorand",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#020617] text-slate-100 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
