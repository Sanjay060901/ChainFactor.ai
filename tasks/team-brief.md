# ChainFactor AI - Team Brief

**Hackathon:** AlgoBharat Hack Series 3.0 (Future of Finance + Agentic Commerce)
**Prize Pool:** USD 30,000
**Our Deadline:** April 2, 2026 (submission: April 15)
**Budget:** $200
**Features:** 42 across 8 epics

---

## What Are We Building?

An AI-powered invoice financing platform for Indian SMEs on Algorand blockchain.

**One-line pitch:** "Upload an invoice, AI verifies it in under 2 minutes, and it becomes a blockchain asset you own."

**Why it matters:** 63 million Indian SMEs have $100B locked in unpaid invoices. Current solutions take 48-72 hours. We do it in under 2 minutes with autonomous AI agents.

---

## The Demo (What Judges Will See)

1. Connect Pera wallet + login
2. Set auto-approve rules ("approve invoices under 5L with risk > 60")
3. Upload an invoice PDF
4. Watch AI agents process it in real-time (14 steps visible on screen)
5. See: extraction, GST compliance check, validation, 5-layer fraud check, GSTIN verified, CIBIL/MCA score, cross-validation, risk score with AI explanation, financing recommendation
6. Agent auto-approves and mints ARC-69 NFT on Algorand
7. User claims NFT (opt-in + transfer)
8. Click Pera Explorer link - see it on-chain
9. Upload a fake invoice - watch it get REJECTED with reasoning
10. Dashboard with portfolio stats, NL query ("show me high-risk invoices this week")
11. Show Audit Trail - full agent reasoning chain for any invoice

**Demo mode available:** Pre-computed results for 3 test invoices as failover if Bedrock/Algorand is slow.

---

## Team Assignments

### Sanjay M (Frontend + Team Lead)
**Stack:** Next.js 14, TailwindCSS, TypeScript, @txnlab/use-wallet-react

**Your features (~18):**

| Milestone | What You Build | Days |
|-----------|---------------|------|
| M1 (Days 1-8) | Frontend scaffold, login/register UI, wallet connect, wallet linking UI, invoice upload UI, WebSocket client + real-time processing view | 1-7 |
| M2 (Days 9-13) | Invoice detail page (all AI results), NFT display card with Pera Explorer link, Claim NFT UI, invoice list, seller rules settings page, audit trail view | 9-12 |
| M3 (Days 14-16) | Dashboard with stats/charts (risk distribution, volume, approval rate), NL query chat bar, demo script + pitch deck, demo polish + seed script | 14-16 |

**Key things to know:**
- Wallet: Use `@txnlab/use-wallet-react` (official Algorand lib, supports Pera + Defly)
- Auth: AWS Cognito handles login/OTP. JWT in Authorization header (not cookies).
- WebSocket: Connect to `WSS /ws/processing/{invoice_id}` via ALB after upload. Display each agent step as it arrives. SSE fallback available.
- Block explorer: Use Pera Explorer (explorer.perawallet.app) -- AlgoExplorer is shut down
- Static export: `next export` -> files go to S3 + CloudFront
- Claim NFT: UI for user to opt-in to ASA and receive NFT transfer from application wallet

---

### Manoj RS (Backend + AI)
**Stack:** FastAPI, Python 3.11+, Strands Agents SDK, Amazon Textract, Bedrock (Claude), AlgoKit

**Your features (~29):**

| Milestone | What You Build | Days |
|-----------|---------------|------|
| M1 (Days 1-8) | Monorepo scaffold, FastAPI skeleton, DB schema (9 tables), Docker Compose, **AWS infra setup (Cognito, S3, Secrets Manager, Bedrock quota, IAM, ALB)**, Cognito auth backend, wallet linking backend, invoice upload + S3, Strands agent framework, WebSocket server (via ALB), 4 agent tools (extract, validate, GST compliance, GSTN) | 1-8 |
| M2 (Days 9-12) | 5-layer fraud detection tool, buyer intel tool, mock CIBIL + MCA tools, multi-signal risk scoring tool, Invoice Processing Agent assembly, Underwriting Agent + tools (incl. cross_validate_outputs), Swarm orchestration, mint_nft + ASA transfer tool, invoice list API, seller rules API | 9-12 |
| M3 (Days 14-16) | Dashboard API, NL query agent (Opus), demo mode (pre-computed results), **AWS deployment (ECS Fargate + ALB, RDS, ElastiCache, S3+CloudFront, GitHub Actions CI/CD)** | 14-16 |

**Key things to know:**
- Agents use Strands SDK with `@tool` decorator (NOT raw Bedrock API calls, NOT CrewAI)
- 2 agents in Swarm pipeline: Processing (Sonnet) -> Underwriting (Sonnet). NL Query (Opus) is standalone.
- Collection Agent is DEFERRED to Round 3
- Use `Swarm.stream_async()` for real-time events -> Redis pub/sub -> WebSocket
- Hooks: BeforeToolCallEvent / AfterToolCallEvent for per-tool streaming
- Swarm agents do NOT share conversation history -- pass context explicitly via handoff
- `handoff_to_agent` is reserved (auto-injected by Strands)
- NFT minting: application wallet mints, then ASA opt-in + transfer to user
- ARC-69 metadata standard for NFTs
- Mock GSTN/CIBIL/MCA: deterministic responses based on GSTIN prefix
- Demo mode: pre-computed results for 3 test invoices, bypasses Bedrock

---

### Abhishek Reddy (Support - Backend Testing)
**Your features (1 + ongoing support):**

| What | Days |
|------|------|
| Critical Path Backend Tests: pytest suite for critical path tools + API endpoints | Days 14-15 |

**Key things to know:**
- Focus on testing the critical demo path: upload -> extraction -> validation -> fraud -> risk -> underwriting -> NFT mint
- Mock Bedrock responses in tests (do NOT call real Bedrock in CI -- slow and expensive)
- Use `unittest.mock` to simulate agent tool outputs
- Test both happy path (valid invoice -> approved -> NFT) and reject path (fake invoice -> rejected)
- AWS infra and deployment is handled by Manoj

---

### Jeevidha (Support - Smart Contract + Frontend Testing)
**Your features (2 + ongoing support):**

| What | Days |
|------|------|
| Smart Contract: ARC4 + ARC-69 Algorand Python contract for Invoice NFTs, ASA opt-in + transfer support, compile + deploy to testnet via AlgoKit | Days 9-10 |
| Frontend E2E Tests: Playwright for critical path (login -> upload -> processing -> claim NFT -> Pera Explorer) | Days 14-15 |

**Key things to know:**
- Smart contract uses **Algorand Python** (`algorand-python` v3.5.0, import as `algopy`). NOT PyTeal -- it's deprecated.
- Compiler: `puyapy` v5.8.0 (compiles algopy to TEAL)
- Contract pattern: `class InvoiceNFT(ARC4Contract):` with `@arc4.abimethod` decorators
- AlgoKit 2.x (v2.10.2) for development + deployment. Use `algokit init -t python` as starting point.
- **ARC-69 metadata standard**: NFT metadata goes in the `note` field of the latest `acfg` transaction. Required field: `"standard": "arc69"`.
- Contract has: `create_invoice_nft()` method with ARC-69 metadata (invoice summary, risk score, doc hash)
- ASA creation uses inner transactions: `itxn.AssetConfig()` for create, `itxn.AssetTransfer()` for transfer
- Contract needs funding for MBR: 0.1 ALGO base + 0.1 ALGO per ASA created (get from testnet faucet)
- **ASA configuration**: manager + clawback = application address, freeze = zero (no freeze authority)
- Target: Algorand TESTNET only (never mainnet)
- Testnet endpoints: `https://testnet-api.algonode.cloud` (Algod), `https://testnet-idx.algonode.cloud` (Indexer) -- free, no token
- Use `algokit localnet start` for local development
- Block explorer: Pera Explorer (`https://testnet.explorer.perawallet.app/`) -- AlgoExplorer is shut down
- **Fallback plan**: If ARC4 contract isn't ready by Day 12, switch to direct ASA creation via py-algorand-sdk (simpler, same NFT result)

---

## Tech Stack Quick Reference

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, TypeScript |
| Wallet | @txnlab/use-wallet-react (Pera + Defly) |
| Auth | AWS Cognito + SNS |
| Backend | FastAPI, Python 3.11+ (modular monolith) |
| AI Agents | Strands Agents SDK (Bedrock-native, official AWS) |
| AI Models | Sonnet 4.6 (processing + underwriting) / Opus 4.6 (NL query only) / Haiku 4.5 (future) via Bedrock |
| OCR | Amazon Textract (primary) + Claude vision (fallback) |
| Blockchain | Algorand Python ARC4 + ARC-69 + AlgoKit 2.x (Testnet) |
| Explorer | Pera Explorer (explorer.perawallet.app) |
| Database | PostgreSQL (RDS) |
| Cache | Redis (ElastiCache) |
| Storage | S3 |
| Hosting | ECS Fargate + ALB (backend) + S3+CloudFront (frontend) |

---

## Agent Architecture (How It Works)

```
User uploads invoice
        |
        v
[Invoice Processing Agent] (Sonnet 4.6)
  - Extracts data from PDF (Textract + Claude fallback)
  - Validates fields (math, consistency)
  - Validates GST compliance (HSN/SAC rates, e-invoice rules)
  - Runs 5-layer fraud detection
  - Verifies GSTIN (mock API)
  - Gets CIBIL credit score (mock)
  - Gets MCA company info (mock)
  - Generates buyer intelligence brief
  - Calculates multi-signal risk score + AI explanation
  - Generates invoice summary for NFT
        |
        | HANDOFF (via Strands Swarm)
        v
[Underwriting Agent] (Sonnet 4.6)
  - Cross-validates all prior outputs for consistency
  - Checks seller's auto-approve rules
  - Makes autonomous approve/reject/flag decision
  - Logs reasoning trace
        |
        | HANDOFF back (if approved)
        v
[Invoice Processing Agent] mints ARC-69 NFT on Algorand
        |
        v
User claims NFT (opt-in + transfer)
        |
        v
NFT on Algorand Testnet + Pera Explorer link

[NL Query Agent] (Opus 4.6) - standalone, on-demand
  - "Show me high-risk invoices this week"
  - Natural language queries over portfolio data
```

All steps are visible to the user in real-time via WebSocket (through ALB).

---

## Timeline

```
Week 1 (March 17-24): MILESTONE 1 - Core Pipeline
  - Project setup, auth, wallet, upload, agent framework, WebSocket, first 4 tools
  - DEPLOY 1 to AWS on Day 8

Week 2 (March 25-29): MILESTONE 2 - Full Pipeline + NFT
  - Remaining tools, agents, Swarm orchestration, smart contract, NFT minting + claim
  - Day 13 = INTEGRATION DAY (no new features, end-to-end testing only)
  - DEPLOY 2 to AWS on Day 13

Week 2.5 (March 30 - April 1): MILESTONE 3 - Dashboard + Polish
  - Dashboard, NL query, tests, demo mode, final deployment
  - DEPLOY 3 (final) on Day 16

April 2: Buffer day - bug fixes, demo rehearsal x3, video recording, pitch deck review
```

---

## What We Are NOT Building (Deferred to Round 3 - May 20)

- Real GSTN/CIBIL/MCA API integration (using mocks)
- Lender marketplace (lenders browse and fund invoices)
- Real-time auctions (competitive bidding)
- USDC escrow and payment settlement
- Supply chain network effects
- Advanced ML fraud models (using Claude-powered detection)
- Collection Agent + UI (impressive but not core demo path)
- Alerts system (nice-to-have)

---

## Getting Started (Day 1)

1. Clone the repo: `git clone https://github.com/Manoj-777/chainfactor-ai.git`
2. Run `docker-compose up -d` (starts PostgreSQL + Redis)
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
4. Frontend: `cd frontend && npm install && npm run dev`
5. Algorand: `algokit localnet start`

**Questions?** Check `tasks/project-plan.md` for the full plan or `tasks/architecture-raw.md` for deep architecture details.
