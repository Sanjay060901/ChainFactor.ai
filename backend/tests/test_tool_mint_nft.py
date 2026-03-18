"""TDD tests for Feature 4.11: mint_nft tool.

Tests ARC-69 NFT minting on Algorand testnet.

In DEMO_MODE: returns mock result (no algosdk calls).
In real mode: algosdk calls are mocked via unittest.mock to avoid testnet side effects.

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

    def test_return_keys_present_demo(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert "asset_id" in result
        assert "txn_id" in result
        assert "explorer_url" in result
        assert "metadata" in result

    def test_asset_id_is_int_demo(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert isinstance(result["asset_id"], int)

    def test_txn_id_is_str_demo(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert isinstance(result["txn_id"], str)
        assert len(result["txn_id"]) > 0

    def test_explorer_url_is_str_demo(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert isinstance(result["explorer_url"], str)

    def test_metadata_is_dict_demo(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert isinstance(result["metadata"], dict)


# ---------------------------------------------------------------------------
# Tests: DEMO_MODE values
# ---------------------------------------------------------------------------


class TestMintNftDemoMode:
    """Demo mode returns the correct mock values."""

    def test_demo_asset_id(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert result["asset_id"] == 123456789

    def test_demo_txn_id_starts_with_demo(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert result["txn_id"].startswith("DEMO_TXN_")

    def test_demo_explorer_url_contains_asset_id(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert "123456789" in result["explorer_url"]
        assert "perawallet" in result["explorer_url"]

    def test_demo_explorer_url_format(self):
        """Explorer URL must match the Pera testnet pattern."""
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert (
            result["explorer_url"]
            == "https://testnet.explorer.perawallet.app/asset/123456789/"
        )

    def test_demo_metadata_arc69_standard(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert result["metadata"]["standard"] == "arc69"

    def test_demo_metadata_has_description(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert "description" in result["metadata"]
        assert isinstance(result["metadata"]["description"], str)

    def test_demo_metadata_properties_present(self):
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        props = result["metadata"]["properties"]
        assert "invoice_number" in props
        assert "seller" in props
        assert "buyer" in props
        assert "amount" in props
        assert "risk_score" in props
        assert "risk_level" in props

    def test_demo_metadata_properties_values(self):
        """Properties should match the input extracted_data and risk_assessment."""
        result = mint_nft(
            invoice_id="inv-123",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        props = result["metadata"]["properties"]
        assert props["invoice_number"] == "INV-2026-001"
        assert props["risk_score"] == 15
        assert props["risk_level"] == "low"
        assert props["amount"] == 11800.0


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
        """Real mode result has same keys as demo mode."""
        _mock_algod, txn_id, asset_id = self._make_mock_algod()

        # Patch _create_asa (the algosdk boundary) -- algosdk is a local import
        # inside _create_asa, so we patch the function itself, not the module attr.
        with patch("app.agents.tools.mint_nft._create_asa") as mock_create:
            mock_create.return_value = (asset_id, txn_id)

            result = mint_nft(
                invoice_id="inv-real-001",
                extracted_data=_extracted_data(),
                risk_assessment=_risk_assessment(),
                _demo=False,
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
                _demo=False,
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
                _demo=False,
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
                _demo=False,
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

    def test_demo_url_ends_with_slash(self):
        result = mint_nft(
            invoice_id="inv-url-test",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert result["explorer_url"].endswith("/")

    def test_demo_url_uses_testnet_pera(self):
        result = mint_nft(
            invoice_id="inv-url-test",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert "testnet.explorer.perawallet.app" in result["explorer_url"]

    def test_demo_url_path_contains_asset(self):
        result = mint_nft(
            invoice_id="inv-url-test",
            extracted_data=_extracted_data(),
            risk_assessment=_risk_assessment(),
            _demo=True,
        )
        assert "/asset/" in result["explorer_url"]
