"""TDD tests for Feature 4.11: mint_nft tool.

Tests ARC-69 NFT minting on Algorand testnet.
All tests mock _create_asa to avoid real algosdk/testnet calls.

Return shape:
    {"asset_id": int, "txn_id": str, "explorer_url": str, "metadata": dict}

ARC-69 metadata shape:
    {"standard": "arc69", "description": str,
     "properties": {invoice_number, seller, buyer, amount, risk_score, risk_level, date}}
"""

from unittest.mock import MagicMock, patch

from app.agents.tools.mint_nft import mint_nft


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_ASA = patch(
    "app.agents.tools.mint_nft._create_asa",
    return_value=(123456789, "MOCK_TXN_ABC123"),
)


def _extracted_data() -> dict:
    return {
        "seller": {"name": "Acme Pvt Ltd", "gstin": "27AABCA1234R1ZM"},
        "buyer": {"name": "Beta Corp", "gstin": "29AABCB5678R1ZX"},
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-03-15",
        "total_amount": 11800.0,
    }


def _risk_assessment() -> dict:
    return {"score": 15, "level": "low", "explanation": "Low risk invoice."}


# ---------------------------------------------------------------------------
# Tests: Return shape
# ---------------------------------------------------------------------------


class TestMintNftReturnShape:
    """Result must contain asset_id, txn_id, explorer_url, and metadata."""

    @_MOCK_ASA
    def test_return_keys_present(self, _mock):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert "asset_id" in result
        assert "txn_id" in result
        assert "explorer_url" in result
        assert "metadata" in result

    @_MOCK_ASA
    def test_asset_id_is_int(self, _mock):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert isinstance(result["asset_id"], int)

    @_MOCK_ASA
    def test_txn_id_is_str(self, _mock):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert isinstance(result["txn_id"], str)
        assert len(result["txn_id"]) > 0

    @_MOCK_ASA
    def test_explorer_url_is_str(self, _mock):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert isinstance(result["explorer_url"], str)

    @_MOCK_ASA
    def test_metadata_is_dict(self, _mock):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert isinstance(result["metadata"], dict)


# ---------------------------------------------------------------------------
# Tests: Real mode (algosdk mocked)
# ---------------------------------------------------------------------------


class TestMintNftRealMode:
    """Real mode creates ASA on testnet. algosdk calls are mocked."""

    def _make_mock_algod(self, asset_id: int = 555000, txn_id: str = "REAL_TXN_XYZ"):
        """Build a mock algod client that simulates a successful ASA creation."""
        mock_algod = MagicMock()
        # suggested_params
        mock_params = MagicMock()
        mock_params.fee = 1000
        mock_params.min_fee = 1000
        mock_params.flat_fee = True
        mock_params.first = 1000
        mock_params.last = 2000
        mock_params.gh = "testnet-genesis-hash"
        mock_algod.suggested_params.return_value = mock_params

        # send_transaction returns txn confirmation info
        mock_algod.send_transaction.return_value = txn_id

        # wait_for_confirmation returns dict with asset-index
        mock_algod.status.return_value = {"last-round": 1000}
        return mock_algod, txn_id, asset_id

    def test_real_mode_returns_correct_shape(self):
        """Result has same keys as expected shape."""
        _mock_algod, txn_id, asset_id = self._make_mock_algod()

        # Patch _create_asa (the algosdk boundary) -- algosdk is a local import
        # inside _create_asa, so we patch the function itself, not the module attr.
        with patch("app.agents.tools.mint_nft._create_asa") as mock_create:
            mock_create.return_value = (asset_id, txn_id)

            result = mint_nft(
                invoice_id="inv-real-001",
                extracted_data=_extracted_data(),
                risk_assessment=_risk_assessment(),
            )

        assert "asset_id" in result
        assert "txn_id" in result
        assert "explorer_url" in result
        assert "metadata" in result

    def test_real_mode_explorer_url_format(self):
        """Real mode must produce a Pera testnet explorer URL."""
        with patch("app.agents.tools.mint_nft._create_asa") as mock_create:
            mock_create.return_value = (987654321, "REALTXNID123")

            result = mint_nft(
                invoice_id="inv-real-002",
                extracted_data=_extracted_data(),
                risk_assessment=_risk_assessment(),
            )

        assert "987654321" in result["explorer_url"]
        assert "testnet.explorer.perawallet.app" in result["explorer_url"]
        assert result["explorer_url"].endswith("/")

    def test_real_mode_metadata_arc69(self):
        """Real mode metadata must have standard=arc69."""
        with patch("app.agents.tools.mint_nft._create_asa") as mock_create:
            mock_create.return_value = (111222333, "TXNID456")

            result = mint_nft(
                invoice_id="inv-real-003",
                extracted_data=_extracted_data(),
                risk_assessment=_risk_assessment(),
            )

        assert result["metadata"]["standard"] == "arc69"
        assert "properties" in result["metadata"]

    def test_real_mode_asset_id_from_create_asa(self):
        """asset_id in result comes from _create_asa return value."""
        expected_asset_id = 444555666
        with patch("app.agents.tools.mint_nft._create_asa") as mock_create:
            mock_create.return_value = (expected_asset_id, "TXN_ABC")

            result = mint_nft(
                invoice_id="inv-real-004",
                extracted_data=_extracted_data(),
                risk_assessment=_risk_assessment(),
            )

        assert result["asset_id"] == expected_asset_id


# ---------------------------------------------------------------------------
# Tests: ARC-69 metadata builder (internal helper)
# ---------------------------------------------------------------------------


class TestBuildArc69Metadata:
    """The _build_arc69_metadata helper must produce correct structure."""

    def test_metadata_structure(self):
        from app.agents.tools.mint_nft import _build_arc69_metadata

        metadata = _build_arc69_metadata(
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert metadata["standard"] == "arc69"
        assert "description" in metadata
        assert "properties" in metadata

    def test_metadata_properties_keys(self):
        from app.agents.tools.mint_nft import _build_arc69_metadata

        metadata = _build_arc69_metadata(
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        props = metadata["properties"]
        required = {
            "invoice_number",
            "seller",
            "buyer",
            "amount",
            "risk_score",
            "risk_level",
        }
        assert required.issubset(set(props.keys()))

    def test_metadata_values_match_inputs(self):
        from app.agents.tools.mint_nft import _build_arc69_metadata

        metadata = _build_arc69_metadata(
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        props = metadata["properties"]
        assert props["invoice_number"] == "INV-2026-001"
        assert props["seller"] == "Acme Pvt Ltd"
        assert props["buyer"] == "Beta Corp"
        assert props["amount"] == 11800.0
        assert props["risk_score"] == 15
        assert props["risk_level"] == "low"

    def test_metadata_description_contains_invoice_number(self):
        from app.agents.tools.mint_nft import _build_arc69_metadata

        metadata = _build_arc69_metadata(
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert "INV-2026-001" in metadata["description"]


# ---------------------------------------------------------------------------
# Tests: Explorer URL construction
# ---------------------------------------------------------------------------


class TestExplorerUrl:
    """Explorer URL must always use Pera testnet and end with /."""

    @_MOCK_ASA
    def test_url_ends_with_slash(self, _mock):
        result = mint_nft(
            invoice_id="inv-url-test",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert result["explorer_url"].endswith("/")

    @_MOCK_ASA
    def test_url_uses_testnet_pera(self, _mock):
        result = mint_nft(
            invoice_id="inv-url-test",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert "testnet.explorer.perawallet.app" in result["explorer_url"]

    @_MOCK_ASA
    def test_url_path_contains_asset(self, _mock):
        result = mint_nft(
            invoice_id="inv-url-test",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
        )
        assert "/asset/" in result["explorer_url"]
