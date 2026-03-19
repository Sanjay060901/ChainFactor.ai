# M2 Backend Integration Design

> Milestone 2: Wire existing agents, tools, and smart contract into end-to-end pipeline.

## Context

M1 delivered all building blocks:
- 11 invoice processing tools + 7 underwriting tools (321 tests)
- Invoice Processing Agent + Underwriting Agent definitions
- Strands Swarm config (2-agent pipeline)
- WebSocket server + Redis pub/sub bridge
- ARC4+ARC-69 smart contract (7 ABI methods)
- NFT model, agent trace model, invoice JSONB columns

M2 wires these into a working pipeline: API trigger -> agent execution -> DB persistence -> WebSocket streaming -> NFT minting.

## Scope

Backend only. Frontend deferred to separate session/handoff.

## Design

### 1. Pipeline Runner (`backend/app/modules/agents/pipeline.py`)

Background task that orchestrates the full invoice processing pipeline.

**Entry point:** `async def run_invoice_pipeline(invoice_id: UUID, db: AsyncSession)`

**Flow:**
1. Load invoice from DB, set status=processing
2. Execute Invoice Agent tools sequentially (steps 1-11)
3. After each tool: persist result to invoice JSONB column + publish WebSocket event
4. Handoff context to Underwriting Agent (steps 12-14)
5. Based on decision: update invoice status (approved/rejected/flagged)
6. If approved: trigger mint_nft (step 14, after underwriting decision -- NOT part of invoice agent's sequential flow)
7. Save agent trace to `agent_traces` table

**Note on `_mint_nft_tool` in `INVOICE_AGENT_TOOLS`:** The tool remains registered on the invoice agent for future Strands Swarm wiring (Phase 2). In M2 Phase 1 (direct tool calls), the agent tool lists are not used -- the pipeline runner calls tools directly. No change needed to `invoice_agent.py` for M2.

**Pre-existing bug:** `mint_nft.py` uses `algosdk.mnemonic` and `algosdk.account` without `import algosdk` at module level inside `_create_asa()`. This will crash in non-demo mode. Must be fixed before implementing 6.2.
8. Publish pipeline_complete event

**Demo mode:** Same flow, tools return pre-computed results (no Bedrock/Algorand calls).

**Error handling:** Try/except around each tool. On failure: set invoice status=failed, publish error event, save partial trace.

### 2. Tool-to-Step Mapping

| Step | Tool | Agent | Invoice Column |
|------|------|-------|----------------|
| 1 | extract_invoice | invoice | extracted_data |
| 2 | validate_fields | invoice | validation_result |
| 3 | validate_gst_compliance | invoice | gst_compliance |
| 4 | verify_gstn | invoice | gstin_verification |
| 5 | check_fraud | invoice | fraud_detection |
| 6 | get_buyer_intel | invoice | buyer_intel |
| 7 | get_credit_score | invoice | credit_score |
| 8 | get_company_info | invoice | company_info |
| 9 | calculate_risk | invoice | risk_assessment |
| 10 | generate_summary | invoice | ai_explanation |
| 11 | cross_validate_outputs | underwriting | underwriting (partial) |
| 12 | approve/reject/flag | underwriting | underwriting (decision) |
| 13 | log_decision | underwriting | underwriting (trace_id) |
| 14 | mint_nft | invoice | nft_records table |

Step 14 only executes if decision=approved.

### 3. Event Bridge (`backend/app/modules/agents/event_bridge.py`)

Publishes step events to Redis for WebSocket consumption.

```python
async def publish_step_event(
    invoice_id: str,
    step: int,
    step_name: str,
    agent: str,
    result: dict,
    elapsed_ms: int,
) -> None:
    # Builds step_complete event matching existing WebSocket schema
    # Calls publish_event(invoice_id, event_data) from redis_bridge
```

Matches the existing `demo_events.py` schema exactly so WebSocket consumers don't change.

### 4. DB Persistence Helper (`backend/app/modules/agents/persistence.py`)

```python
async def persist_tool_result(
    db: AsyncSession,
    invoice_id: UUID,
    step_name: str,
    result: dict,
) -> None:
    # Maps step_name to invoice column, updates via setattr
    # Commits after each step (checkpoint/resume on retry)

async def save_agent_trace(
    db: AsyncSession,
    invoice_id: UUID,
    steps: list[dict],
    handoff_context: dict | None,
) -> None:
    # Creates AgentTrace record with full execution log
```

### 5. Process Endpoint (update existing stub)

`POST /invoices/{invoice_id}/process` in `invoices/router.py`:
- Validate: invoice exists, status=uploaded, user owns it (IDOR check)
- Set status=processing, commit
- Launch `run_invoice_pipeline` as background task
- Return: `{invoice_id, status: "processing", ws_url: "/ws/processing/{id}"}`

### 6. NFT Opt-In Endpoint (6.2)

`POST /invoices/{invoice_id}/nft/opt-in`:
- Validate: invoice approved, NFT minted (nft_record exists with status=minted)
- Validate: user has linked wallet
- Build unsigned ASA opt-in transaction (algosdk AssetTransferTxn, amount=0, receiver=sender)
- Return: `{unsigned_txn: base64, asset_id, message}`
- Frontend signs with Pera/Defly, submits signed txn back

### 7. NFT Claim Endpoint (6.5)

`POST /invoices/{invoice_id}/nft/claim`:
- Accept: `{signed_optin_txn: base64}` from frontend
- Submit opt-in txn to Algorand testnet
- Execute ASA transfer from app wallet to user wallet (inner txn or direct algosdk)
- Update nft_record: status=claimed, opt_in_txn_id, transfer_txn_id, claimed_by_wallet
- Return: `{asset_id, transfer_txn_id, explorer_url, status: "claimed"}`

### 8. Testing Strategy

TDD throughout. Test files:
- `test_pipeline.py` — pipeline runner with mocked tools (verify step order, DB persistence, event publishing, error handling)
- `test_event_bridge.py` — event publishing format, Redis calls
- `test_persistence.py` — JSONB column updates, agent trace creation
- `test_process_endpoint.py` — API endpoint behavior (auth, validation, background task launch)
- `test_nft_optin.py` — opt-in txn building, validation
- `test_nft_claim.py` — claim flow, ASA transfer, status updates

Target: 80%+ coverage on new code.

### 9. Files to Create/Modify

**Create:**
- `backend/app/modules/agents/pipeline.py`
- `backend/app/modules/agents/event_bridge.py`
- `backend/app/modules/agents/persistence.py`
- `backend/tests/test_pipeline.py`
- `backend/tests/test_event_bridge.py`
- `backend/tests/test_persistence.py`
- `backend/tests/test_nft_optin.py`
- `backend/tests/test_nft_claim.py`

**Modify:**
- `backend/app/modules/invoices/router.py` — replace process/opt-in/claim stubs
- `backend/app/modules/agents/invoice_agent.py` — verify tool list correct
- `backend/app/modules/agents/underwriting_agent.py` — verify tool list correct

## Non-Goals

- Frontend work (deferred)
- Real Strands Swarm streaming (Phase 1 uses direct tool calls; Strands wiring in step 5)
- Collection Agent (Round 3)
- Real GSTN/CIBIL/MCA APIs (mock services only)
