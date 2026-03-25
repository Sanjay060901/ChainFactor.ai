/** @type {import('next').NextConfig} */
const path = require("path");

const noopPath = path.resolve(__dirname, "src/lib/noop.js");

const nextConfig = {
  // output: "export" — enable for production static builds (S3 + CloudFront)
  // Removed for dev to allow dynamic [id] routes without generateStaticParams
  images: {
    unoptimized: true,
  },
  webpack: (config) => {
    // Handle optional peer dependencies from @txnlab/use-wallet-react
    // Only Pera and Defly wallets are configured; all others are optional
    const optionalDeps = [
      "@web3auth/modal",
      "@web3auth/base",
      "@web3auth/base-provider",
      "@web3auth/single-factor-auth",
      "@web3auth/ethereum-provider",
      "@web3auth/solana-provider",
      "@web3auth/openlogin-adapter",
      "@web3auth/wallet-services-plugin",
      "@magic-ext/algorand",
      "magic-sdk",
    ];
    for (const dep of optionalDeps) {
      config.resolve.alias[dep] = noopPath;
    }
    return config;
  },
};

module.exports = nextConfig;
