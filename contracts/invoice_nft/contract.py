"""ARC4 + ARC-69 Smart Contract for Invoice NFTs.

Built with Algorand Python (algopy v3.5.0), compiled with puyapy v5.8.0.
Deploys to Algorand Testnet via AlgoKit 2.x.

Implementation: Feature 6.1 (Milestone 2, Days 9-10)

This contract creates Algorand Standard Assets (ASAs) representing verified invoices.
Metadata follows the ARC-69 standard: JSON stored in the note field of asset config
transactions.

Key design:
- Only the app creator (application wallet) can create or update NFTs.
- Each NFT is a unique ASA with total=1, decimals=0 (true NFT).
- After minting, the backend transfers the ASA to the user's wallet
  (user must opt-in first).
- MBR: contract must be funded with 0.1 ALGO base + 0.1 ALGO per ASA created.
"""

from algopy import (
    ARC4Contract,
    Global,
    Txn,
    UInt64,
    arc4,
    itxn,
    op,
)


class InvoiceNFT(ARC4Contract):
    """ARC4 contract for creating and managing invoice NFT assets (ARC-69)."""

    @arc4.abimethod()
    def create_nft(
        self,
        invoice_id: arc4.String,
        risk_score: arc4.UInt64,
        decision: arc4.String,
        metadata_json: arc4.String,
    ) -> arc4.UInt64:
        """Create a new ASA for a verified invoice with ARC-69 metadata.

        Args:
            invoice_id: UUID of the invoice being tokenized.
            risk_score: Computed risk score (0-100).
            decision: Underwriting decision (approved/rejected/review).
            metadata_json: Full ARC-69 JSON metadata string for the note field.

        Returns:
            The asset ID of the newly created ASA.

        Only callable by the application creator (the application wallet).
        """
        # Authorization: only app creator can mint
        assert Txn.sender == Global.creator_address, "Only app creator can mint NFTs"

        # Build asset name: "ChainFactor Invoice #<invoice_id>"
        # Algorand asset name max = 32 bytes; truncate invoice_id if needed.
        # We use a prefix + first 8 chars of the UUID for readability.
        asset_name_prefix = b"CF Invoice #"
        invoice_id_native = invoice_id.native
        # Take up to 20 chars of invoice_id to stay within 32-byte limit
        truncated_id = op.extract(invoice_id_native.bytes, UInt64(0), UInt64(20))
        asset_name = op.concat(asset_name_prefix, truncated_id)

        # Encode the ARC-69 metadata JSON as bytes for the note field
        metadata_bytes = metadata_json.native.bytes

        # Create the ASA via inner transaction
        created_asset = itxn.AssetConfig(
            total=1,
            decimals=0,
            unit_name="CFINV",
            asset_name=asset_name,
            note=metadata_bytes,
            default_frozen=False,
            fee=Global.min_txn_fee,
        ).submit()

        return arc4.UInt64(created_asset.created_asset.id)

    @arc4.abimethod()
    def update_metadata(
        self,
        asset_id: arc4.UInt64,
        new_metadata_json: arc4.String,
    ) -> None:
        """Update ARC-69 metadata for an existing invoice NFT.

        ARC-69 defines metadata as the note field of the most recent
        asset config (acfg) transaction. Sending a new acfg with updated
        note effectively updates the metadata.

        Args:
            asset_id: The ASA ID to update metadata for.
            new_metadata_json: New ARC-69 JSON metadata string.

        Only callable by the application creator.
        """
        assert Txn.sender == Global.creator_address, (
            "Only app creator can update metadata"
        )

        metadata_bytes = new_metadata_json.native.bytes

        # Submit a reconfiguration transaction with updated note.
        # manager/reserve/freeze/clawback are set to the contract address
        # to retain management capabilities.
        itxn.AssetConfig(
            config_asset=asset_id.native,
            note=metadata_bytes,
            manager=Global.current_application_address,
            reserve=Global.current_application_address,
            freeze=Global.current_application_address,
            clawback=Global.current_application_address,
            fee=Global.min_txn_fee,
        ).submit()

    @arc4.abimethod()
    def transfer_nft(
        self,
        asset_id: arc4.UInt64,
        receiver: arc4.Address,
    ) -> None:
        """Transfer an invoice NFT to a user's wallet after opt-in.

        The user must have already opted in to the ASA before this call.
        Uses clawback to transfer from the contract's holding.

        Args:
            asset_id: The ASA ID to transfer.
            receiver: The Algorand address of the receiving wallet.

        Only callable by the application creator.
        """
        assert Txn.sender == Global.creator_address, (
            "Only app creator can transfer NFTs"
        )

        itxn.AssetTransfer(
            xfer_asset=asset_id.native,
            asset_receiver=receiver.native,
            asset_amount=1,
            fee=Global.min_txn_fee,
        ).submit()
