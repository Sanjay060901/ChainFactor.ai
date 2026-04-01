"use client";

import { WalletProvider, WalletManager, NetworkId, WalletId } from "@txnlab/use-wallet-react";
import { ReactNode, useMemo } from "react";
import { AuthContext, useAuthState } from "@/hooks/useAuth";

function WalletProviderWrapper({ children }: { children: ReactNode }) {
  const manager = useMemo(
    () =>
      new WalletManager({
        wallets: [WalletId.PERA, WalletId.DEFLY],
        defaultNetwork: NetworkId.TESTNET,
        networks: {
          [NetworkId.TESTNET]: {
            algod: {
              baseServer: "https://testnet-api.algonode.cloud",
              port: 443,
              token: "",
            },
          },
        },
      }),
    []
  );

  return <WalletProvider manager={manager}>{children}</WalletProvider>;
}

export function Providers({ children }: { children: ReactNode }) {
  const auth = useAuthState();
  return (
    <AuthContext.Provider value={auth}>
      <WalletProviderWrapper>{children}</WalletProviderWrapper>
    </AuthContext.Provider>
  );
}
