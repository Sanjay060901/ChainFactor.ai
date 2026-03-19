"""Pytest conftest that stubs the algopy module for design verification tests.

The algopy package (algorand-python) is a compile-time-only stub that raises
RuntimeError on import. To run structural/design tests against the contract
class without the AVM simulator, we inject a mock algopy module into
sys.modules BEFORE the contract module is imported.

This allows inspect-based tests (method existence, signatures) and the
ARC-69 metadata builder tests to run in a standard Python environment.
"""

import sys
import types
from unittest.mock import MagicMock


def _build_mock_algopy() -> types.ModuleType:
    """Create a mock algopy module that satisfies contract imports."""
    algopy = types.ModuleType("algopy")

    # --- Base class for contracts ---
    class ARC4Contract:
        pass

    algopy.ARC4Contract = ARC4Contract

    # --- GlobalState: acts as a simple descriptor ---
    class GlobalState:
        def __init__(self, initial_value=None):
            self._value = initial_value

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, val):
            self._value = val

    algopy.GlobalState = GlobalState

    # --- UInt64: simple int wrapper ---
    class UInt64(int):
        pass

    algopy.UInt64 = UInt64

    # --- Global namespace (creator_address, etc.) ---
    class _Global:
        creator_address = "MOCK_CREATOR"
        current_application_address = "MOCK_APP_ADDR"
        min_txn_fee = UInt64(1000)

    algopy.Global = _Global

    # --- Txn namespace ---
    class _Txn:
        sender = "MOCK_SENDER"

    algopy.Txn = _Txn

    # --- arc4 sub-module ---
    arc4_mod = types.ModuleType("algopy.arc4")

    class Arc4String:
        def __init__(self, val=""):
            self._val = val

        @property
        def native(self):
            mock = MagicMock()
            mock.bytes = self._val.encode() if isinstance(self._val, str) else self._val
            return mock

    class Arc4UInt64:
        def __init__(self, val=0):
            self._val = val

        @property
        def native(self):
            return self._val

    class Arc4Address:
        def __init__(self, val=""):
            self._val = val

        @property
        def native(self):
            return self._val

    class Arc4Bool:
        def __init__(self, val=False):
            self._val = val

    # abimethod decorator: just returns the function unchanged
    def abimethod(*args, **kwargs):
        def decorator(fn):
            return fn

        if args and callable(args[0]):
            return args[0]
        return decorator

    arc4_mod.String = Arc4String
    arc4_mod.UInt64 = Arc4UInt64
    arc4_mod.Address = Arc4Address
    arc4_mod.Bool = Arc4Bool
    arc4_mod.abimethod = abimethod

    algopy.arc4 = arc4_mod

    # --- itxn sub-module (inner transactions) ---
    itxn_mod = types.ModuleType("algopy.itxn")

    class _MockItxnResult:
        class _CreatedAsset:
            id = UInt64(12345)

        created_asset = _CreatedAsset()

    class _MockItxn:
        def __init__(self, **kwargs):
            pass

        def submit(self):
            return _MockItxnResult()

    itxn_mod.AssetConfig = _MockItxn
    itxn_mod.AssetTransfer = _MockItxn
    itxn_mod.AssetFreeze = _MockItxn

    algopy.itxn = itxn_mod

    # --- op sub-module (opcodes) ---
    op_mod = types.ModuleType("algopy.op")

    def extract(data, start, length):
        s = int(start) if not isinstance(start, int) else start
        l = int(length) if not isinstance(length, int) else length
        return data[s : s + l]

    def concat(a, b):
        if isinstance(a, bytes) and isinstance(b, bytes):
            return a + b
        return bytes(a) + bytes(b)

    class _AssetHolding:
        @staticmethod
        def asset_balance(account, asset_id):
            return UInt64(0), False

    op_mod.extract = extract
    op_mod.concat = concat
    op_mod.AssetHolding = _AssetHolding

    algopy.op = op_mod

    return algopy


# Install mock before any test collection imports the contract
_mock = _build_mock_algopy()
sys.modules["algopy"] = _mock
sys.modules["algopy.arc4"] = _mock.arc4
sys.modules["algopy.itxn"] = _mock.itxn
sys.modules["algopy.op"] = _mock.op
