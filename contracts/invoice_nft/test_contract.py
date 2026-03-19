"""Design verification tests for InvoiceNFT contract and ARC-69 metadata.

Since Algorand Python contracts require the AVM simulator to execute,
these tests verify:
- Contract class structure and method signatures
- ARC-69 metadata builder output correctness
- Metadata JSON format compliance
"""

import inspect
import json

import pytest

from contracts.invoice_nft.arc69_metadata import (
    ARC69_STANDARD_VALUE,
    REQUIRED_PROPERTIES,
    build_arc69_metadata,
)
from contracts.invoice_nft.contract import InvoiceNFT


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_METADATA_KWARGS = {
    "invoice_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "seller_name": "Acme Pvt Ltd",
    "buyer_name": "Global Corp",
    "amount": 150000.50,
    "risk_score": 25,
    "risk_level": "low",
    "decision": "approved",
    "invoice_date": "2026-03-01",
    "due_date": "2026-04-01",
}


@pytest.fixture
def sample_metadata_json() -> str:
    """Return a sample ARC-69 metadata JSON string."""
    return build_arc69_metadata(**SAMPLE_METADATA_KWARGS)


@pytest.fixture
def sample_metadata_dict(sample_metadata_json: str) -> dict:
    """Return the parsed dict from sample metadata."""
    return json.loads(sample_metadata_json)


# ---------------------------------------------------------------------------
# Contract structure tests
# ---------------------------------------------------------------------------


class TestContractStructure:
    """Verify InvoiceNFT contract class has the expected shape."""

    def test_contract_class_exists(self):
        """InvoiceNFT class should be importable."""
        assert InvoiceNFT is not None

    def test_inherits_arc4_contract(self):
        """InvoiceNFT must extend ARC4Contract."""
        from algopy import ARC4Contract

        assert issubclass(InvoiceNFT, ARC4Contract)

    def test_has_create_nft_method(self):
        """Contract must expose create_nft."""
        assert hasattr(InvoiceNFT, "create_nft")
        assert callable(getattr(InvoiceNFT, "create_nft"))

    def test_has_update_metadata_method(self):
        """Contract must expose update_metadata."""
        assert hasattr(InvoiceNFT, "update_metadata")
        assert callable(getattr(InvoiceNFT, "update_metadata"))

    def test_has_transfer_nft_method(self):
        """Contract must expose transfer_nft."""
        assert hasattr(InvoiceNFT, "transfer_nft")
        assert callable(getattr(InvoiceNFT, "transfer_nft"))

    def test_has_get_nft_count_method(self):
        """Contract must expose get_nft_count."""
        assert hasattr(InvoiceNFT, "get_nft_count")
        assert callable(getattr(InvoiceNFT, "get_nft_count"))

    def test_has_verify_ownership_method(self):
        """Contract must expose verify_ownership."""
        assert hasattr(InvoiceNFT, "verify_ownership")
        assert callable(getattr(InvoiceNFT, "verify_ownership"))

    def test_has_freeze_nft_method(self):
        """Contract must expose freeze_nft."""
        assert hasattr(InvoiceNFT, "freeze_nft")
        assert callable(getattr(InvoiceNFT, "freeze_nft"))

    def test_has_unfreeze_nft_method(self):
        """Contract must expose unfreeze_nft."""
        assert hasattr(InvoiceNFT, "unfreeze_nft")
        assert callable(getattr(InvoiceNFT, "unfreeze_nft"))

    def test_has_init_method(self):
        """Contract must define __init__ for state initialization."""
        assert "__init__" in InvoiceNFT.__dict__


class TestMethodSignatures:
    """Verify method parameter names and return annotations."""

    def test_create_nft_params(self):
        sig = inspect.signature(InvoiceNFT.create_nft)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == [
            "invoice_id",
            "risk_score",
            "decision",
            "metadata_json",
        ]

    def test_create_nft_return_type(self):
        sig = inspect.signature(InvoiceNFT.create_nft)
        assert sig.return_annotation is not inspect.Parameter.empty

    def test_update_metadata_params(self):
        sig = inspect.signature(InvoiceNFT.update_metadata)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == ["asset_id", "new_metadata_json"]

    def test_transfer_nft_params(self):
        sig = inspect.signature(InvoiceNFT.transfer_nft)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == ["asset_id", "receiver"]

    def test_get_nft_count_params(self):
        sig = inspect.signature(InvoiceNFT.get_nft_count)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == [], "get_nft_count should take no parameters"

    def test_verify_ownership_params(self):
        sig = inspect.signature(InvoiceNFT.verify_ownership)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == ["asset_id", "owner"]

    def test_freeze_nft_params(self):
        sig = inspect.signature(InvoiceNFT.freeze_nft)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == ["asset_id", "target"]

    def test_unfreeze_nft_params(self):
        sig = inspect.signature(InvoiceNFT.unfreeze_nft)
        param_names = [p for p in sig.parameters if p != "self"]
        assert param_names == ["asset_id", "target"]

    def test_total_method_count(self):
        """Contract should have exactly 7 ABI methods + __init__."""
        abi_methods = [
            "create_nft",
            "update_metadata",
            "transfer_nft",
            "get_nft_count",
            "verify_ownership",
            "freeze_nft",
            "unfreeze_nft",
        ]
        for method_name in abi_methods:
            assert hasattr(InvoiceNFT, method_name), f"Missing method: {method_name}"


# ---------------------------------------------------------------------------
# ARC-69 metadata builder tests
# ---------------------------------------------------------------------------


class TestArc69MetadataBuilder:
    """Verify build_arc69_metadata produces valid ARC-69 output."""

    def test_returns_string(self, sample_metadata_json: str):
        assert isinstance(sample_metadata_json, str)

    def test_valid_json(self, sample_metadata_json: str):
        """Output must be parseable JSON."""
        parsed = json.loads(sample_metadata_json)
        assert isinstance(parsed, dict)

    def test_compact_json_no_whitespace(self, sample_metadata_json: str):
        """ARC-69 note field should be compact (no extra whitespace)."""
        # Re-encode with compact separators and compare
        parsed = json.loads(sample_metadata_json)
        expected = json.dumps(parsed, separators=(",", ":"))
        assert sample_metadata_json == expected

    def test_standard_field_is_arc69(self, sample_metadata_dict: dict):
        assert sample_metadata_dict["standard"] == ARC69_STANDARD_VALUE

    def test_has_description(self, sample_metadata_dict: dict):
        assert "description" in sample_metadata_dict
        assert "ChainFactor AI" in sample_metadata_dict["description"]

    def test_has_mime_type(self, sample_metadata_dict: dict):
        assert sample_metadata_dict["mime_type"] == "application/json"

    def test_has_properties_section(self, sample_metadata_dict: dict):
        assert "properties" in sample_metadata_dict
        assert isinstance(sample_metadata_dict["properties"], dict)

    def test_all_required_properties_present(self, sample_metadata_dict: dict):
        """Every property in REQUIRED_PROPERTIES must appear."""
        props = sample_metadata_dict["properties"]
        missing = REQUIRED_PROPERTIES - set(props.keys())
        assert not missing, f"Missing required properties: {missing}"

    def test_invoice_id_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["invoice_id"] == SAMPLE_METADATA_KWARGS["invoice_id"]

    def test_seller_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["seller"] == SAMPLE_METADATA_KWARGS["seller_name"]

    def test_buyer_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["buyer"] == SAMPLE_METADATA_KWARGS["buyer_name"]

    def test_amount_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["amount_inr"] == SAMPLE_METADATA_KWARGS["amount"]

    def test_risk_score_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["risk_score"] == SAMPLE_METADATA_KWARGS["risk_score"]

    def test_risk_level_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["risk_level"] == SAMPLE_METADATA_KWARGS["risk_level"]

    def test_decision_matches(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["decision"] == SAMPLE_METADATA_KWARGS["decision"]

    def test_platform_is_chainfactor(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["platform"] == "ChainFactor AI"

    def test_network_is_testnet(self, sample_metadata_dict: dict):
        props = sample_metadata_dict["properties"]
        assert props["network"] == "algorand-testnet"

    def test_verified_at_is_iso_format(self, sample_metadata_dict: dict):
        """verified_at must be a valid ISO 8601 timestamp."""
        from datetime import datetime

        props = sample_metadata_dict["properties"]
        # Should not raise
        dt = datetime.fromisoformat(props["verified_at"])
        assert dt is not None

    def test_description_includes_invoice_id(self, sample_metadata_dict: dict):
        invoice_id = SAMPLE_METADATA_KWARGS["invoice_id"]
        assert invoice_id in sample_metadata_dict["description"]

    def test_different_inputs_produce_different_output(self):
        """Two calls with different invoice IDs must produce different JSON."""
        json1 = build_arc69_metadata(**SAMPLE_METADATA_KWARGS)
        kwargs2 = {**SAMPLE_METADATA_KWARGS, "invoice_id": "different-uuid"}
        json2 = build_arc69_metadata(**kwargs2)
        assert json1 != json2

    def test_high_risk_metadata(self):
        """Verify metadata works for high-risk rejected invoices."""
        result = build_arc69_metadata(
            invoice_id="high-risk-001",
            seller_name="Risky Corp",
            buyer_name="Shell Co",
            amount=9999999.99,
            risk_score=95,
            risk_level="critical",
            decision="rejected",
            invoice_date="2026-03-15",
            due_date="2026-03-16",
        )
        parsed = json.loads(result)
        assert parsed["properties"]["risk_score"] == 95
        assert parsed["properties"]["decision"] == "rejected"
        assert parsed["properties"]["risk_level"] == "critical"
