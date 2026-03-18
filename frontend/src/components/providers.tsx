"use client";

/**
 * App-level providers: Algorand wallet context.
 * Must be "use client" because wallet providers use browser APIs.
 */

import {
  WalletProvider,
  useInitializeProviders,
  PROVIDER_ID,
} from "@txnlab/use-wallet-react";
import { ReactNode } from "react";

function WalletProviderWrapper({ children }: { children: ReactNode }) {
  const providers = useInitializeProviders({
    providers: [{ id: PROVIDER_ID.PERA }, { id: PROVIDER_ID.DEFLY }],
    nodeConfig: {
      network: "testnet",
      nodeServer: "https://testnet-api.algonode.cloud",
      nodePort: 443,
      nodeToken: "",
    },
  });

  return <WalletProvider value={providers}>{children}</WalletProvider>;
}

export function Providers({ children }: { children: ReactNode }) {
  return <WalletProviderWrapper>{children}</WalletProviderWrapper>;
}
