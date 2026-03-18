import type { Metadata } from "next";
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
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
