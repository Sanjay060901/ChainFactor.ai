"use client";

/**
 * App-level providers: Algorand wallet context.
 * Must be "use client" because wallet providers use browser APIs.
 */

import { WalletProvider, WalletManager, NetworkId } from "@txnlab/use-wallet-react";
import { ReactNode, useMemo } from "react";

function WalletProviderWrapper({ children }: { children: ReactNode }) {
  const manager = useMemo(
    () =>
      new WalletManager({
        wallets: ["pera", "defly"],
        network: NetworkId.TESTNET,
        algod: {
          baseServer: "https://testnet-api.algonode.cloud",
          port: 443,
          token: "",
        },
      }),
    []
  );

  return <WalletProvider manager={manager}>{children}</WalletProvider>;
}

export function Providers({ children }: { children: ReactNode }) {
  return <WalletProviderWrapper>{children}</WalletProviderWrapper>;
}
