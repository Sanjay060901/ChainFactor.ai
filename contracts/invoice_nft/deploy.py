"""Deploy InvoiceNFT contract to Algorand testnet.

Usage (after setting ALGORAND_APP_WALLET_MNEMONIC env var):
    python deploy.py

Reads compiled TEAL from out/ directory, deploys to testnet via Algonode,
saves the App ID and App Address to deployment.json for use by the backend.

Requirements:
    pip install py-algorand-sdk   (already in backend/requirements.txt)
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "out"
APPROVAL_TEAL = OUT_DIR / "InvoiceNFT.approval.teal"
CLEAR_TEAL = OUT_DIR / "InvoiceNFT.clear.teal"
DEPLOYMENT_FILE = HERE / "deployment.json"

ALGOD_URL = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN = ""


def deploy() -> None:
    try:
        import algosdk
        from algosdk.v2client import algod
        from algosdk import transaction
    except ImportError:
        print("ERROR: py-algorand-sdk not installed.")
        print("Run: pip install py-algorand-sdk")
        sys.exit(1)

    # --- Load deployer mnemonic ---
    mnemonic = os.environ.get("ALGORAND_APP_WALLET_MNEMONIC", "").strip()
    if not mnemonic:
        print("ERROR: ALGORAND_APP_WALLET_MNEMONIC environment variable not set.")
        print("Set it to your testnet wallet's 25-word mnemonic before running.")
        sys.exit(1)

    private_key = algosdk.mnemonic.to_private_key(mnemonic)
    sender = algosdk.account.address_from_private_key(private_key)
    print(f"Deploying from: {sender}")

    # --- Connect to testnet ---
    client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)
    account_info = client.account_info(sender)
    balance_algo = account_info.get("amount", 0) / 1_000_000
    print(f"Account balance: {balance_algo:.4f} ALGO")
    if balance_algo < 0.5:
        print("WARNING: Low balance! Fund at https://bank.testnet.algorand.network/")
        if balance_algo < 0.1:
            print("ERROR: Insufficient balance to deploy (need >= 0.1 ALGO).")
            sys.exit(1)

    # --- Load compiled TEAL ---
    if not APPROVAL_TEAL.exists() or not CLEAR_TEAL.exists():
        print(f"ERROR: Compiled TEAL not found in {OUT_DIR}")
        print("Run: uv run --with puyapy==5.7.1 -- puyapy contract.py --out-dir out")
        sys.exit(1)

    approval_program_src = APPROVAL_TEAL.read_text()
    clear_program_src = CLEAR_TEAL.read_text()

    # Compile TEAL to binary
    approval_result = client.compile(approval_program_src)
    clear_result = client.compile(clear_program_src)
    import base64
    approval_program = base64.b64decode(approval_result["result"])
    clear_program = base64.b64decode(clear_result["result"])

    # --- Create application transaction ---
    params = client.suggested_params()
    txn = transaction.ApplicationCreateTxn(
        sender=sender,
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=transaction.StateSchema(num_uints=1, num_byte_slices=0),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
    )

    signed_txn = txn.sign(private_key)
    txn_id = client.send_transaction(signed_txn)
    print(f"Deployment transaction sent: {txn_id}")
    print("Waiting for confirmation...")

    result = transaction.wait_for_confirmation(client, txn_id, 5)
    app_id = result["application-index"]
    app_address = algosdk.logic.get_application_address(app_id)

    print(f"\n{'='*50}")
    print(f"Contract deployed successfully!")
    print(f"  App ID      : {app_id}")
    print(f"  App Address : {app_address}")
    print(f"  Txn ID      : {txn_id}")
    print(f"{'='*50}")
    print(f"\nFund the contract address with at least 0.1 ALGO (MBR):")
    print(f"  https://bank.testnet.algorand.network/")
    print(f"  Address: {app_address}")
    print(f"\nView on Pera Explorer:")
    print(f"  https://testnet.explorer.perawallet.app/application/{app_id}/")

    # --- Save deployment info ---
    deployment = {
        "network": "testnet",
        "app_id": app_id,
        "app_address": app_address,
        "txn_id": txn_id,
        "deployer": sender,
    }
    DEPLOYMENT_FILE.write_text(json.dumps(deployment, indent=2))
    print(f"\nDeployment info saved to: {DEPLOYMENT_FILE}")
    print("Add ALGORAND_APP_ID to your .env file:")
    print(f"  ALGORAND_APP_ID={app_id}")


if __name__ == "__main__":
    deploy()
