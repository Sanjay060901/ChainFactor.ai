# ChainFactor AI -- Project Plan

## Project Vision

ChainFactor AI is an AI-powered invoice financing platform for Indian SMEs built on the Algorand blockchain. SMEs connect their wallet, upload an invoice, and an agentic AI system processes it end-to-end in under 2 minutes: extracting data, validating fields, checking GST compliance, running 5-layer fraud detection, verifying GSTIN, assessing CIBIL/MCA credit scores, calculating multi-signal risk, making autonomous underwriting decisions with cross-validation, and minting the verified invoice as an ARC-69 NFT on Algorand testnet.

**Problem:** India's 63 million SMEs have ~$100B locked in unpaid invoices (45-90 day cycles). Existing solutions take 48-72 hours at 18-24% rates.

**For:** AlgoBharat Hack Series 3.0 (Future of Finance + Agentic Commerce). End users: Indian SME sellers.

**Success for v1:** One complete end-to-end flow -- wallet connect > invoice upload > AI agent processing (14 touchpoints, 5-layer fraud, GST compliance, CIBIL/MCA scoring) > GSTN verification > risk scoring > auto-approve with cross-validation > NFT minting (ARC-69) > user claims NFT > dashboard + NL query. Working prototype with polished demo + pitch deck.

**Constraints:**
- Deadline: April 2, 2026 (Round 2 due April 15)
- Budget: $200
- Team: 4 -- Sanjay M (frontend + lead), Manoj RS (backend + AI), Abhishek Reddy & Jeevidha (support)
- Quality: Enterprise-grade security

**Out of scope for v1:** Lender marketplace, real-time auctions, USDC escrow, payment settlement, real GSTN/CIBIL/MCA APIs, collection agent (moved to Round 3).

---

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + TailwindCSS -> S3 + CloudFront
- **Wallet**: @txnlab/use-wallet-react + use-wallet-ui (Pera + Defly, Algorand)
- **Auth**: AWS Cognito + SNS (OTP/notifications)
- **Backend**: FastAPI (Python 3.11+) on ECS Fargate -- modular monolith with strict module boundaries
- **Agentic Framework**: Strands Agents SDK (strands-agents, Apache 2.0) -- official AWS project, Bedrock-native
- **Multi-Agent**: Strands Swarm -- 3-agent system with tool-based handoffs
- **OCR Primary**: Amazon Textract
- **AI Models (tiered)**: Sonnet 4.6 (invoice processing, underwriting, risk analysis) + Haiku 4.5 (lightweight tools) + Opus 4.6 (NL query only -- low-volume, on-demand) via Amazon Bedrock
- **Blockchain**: Algorand Python (ARC4) + AlgoKit 2.x (Testnet), ARC-69 metadata standard
- **Block Explorer**: Pera Explorer (explorer.perawallet.app) or Allo (allo.info)
- **Database**: PostgreSQL on RDS (Free Tier)
- **Cache**: Redis on ElastiCache
- **Storage**: AWS S3
- **Secrets**: AWS Secrets Manager
- **Monitoring**: CloudWatch + OpenTelemetry (via Strands built-in)
- **CI/CD**: GitHub Actions
- **Containerization**: Docker + docker-compose (local dev)
- **Testing**: pytest (backend), Jest + Playwright (frontend)

---

## Architecture

Full architecture document: tasks/architecture-raw.md

### Component Layers

1. **Client Layer**: Next.js 14 + Wallet SDK + WebSocket Client
2. **Edge/CDN Layer**: CloudFront (static) + ALB (API + WebSocket)
3. **Application Layer**: FastAPI on ECS Fargate (modular monolith: auth, invoices, agents, blockchain modules)
4. **Agent Layer**: Strands Swarm (3 agents with tool-based handoff orchestration)
5. **Data Layer**: PostgreSQL (RDS) + Redis (ElastiCache) + S3
6. **External Services**: Textract, Bedrock, Algorand Testnet, Cognito, SNS

### 3-Agent Swarm Architecture

**Agent 1: Invoice Processing Agent (Sonnet 4.6)**
Tools: extract_invoice, validate_fields, validate_gst_compliance, check_fraud, verify_gstn, get_buyer_intel, get_credit_score, get_company_info, calculate_risk, generate_summary, mint_nft

**Agent 2: Underwriting Agent (Sonnet 4.6)**
Tools: cross_validate_outputs, get_seller_rules, get_invoice_data, approve_invoice, reject_invoice, flag_for_review, log_decision
System prompt includes: "Cross-validate all inputs before deciding. Verify consistency between extracted data, fraud signals, GSTN verification, and credit scores. Flag anomalies."

**Agent 3: Collection Agent (Haiku 4.5) -- DEFERRED to Round 3**
Tools: get_overdue_invoices, get_buyer_history, generate_reminder, suggest_escalation, scan_portfolio

Flow: Invoice Agent -> handoff (via Strands Swarm) -> Underwriting Agent -> handoff back for mint_nft

**NL Query Agent (Opus 4.6) -- standalone, not in Swarm**
On-demand natural language query over portfolio data. Low-volume, high-reasoning.

### Key Architectural Decisions (ADRs)

1. **Backend-side NFT signing** (not user wallet) -- enables fully automated real-time flow
2. **Redis pub/sub for WebSocket bridge** -- decouples agent callbacks from WS handlers
3. **Strands Agents SDK over CrewAI** -- native Bedrock (no LiteLLM layer), native tool execution callbacks for WebSocket, AWS-backed (official AWS project), supports stream_async() on Swarm
4. **Cognito + wallet dual identity** -- familiar login for Indian SMEs + wallet for blockchain
5. **Synchronous Textract** -- simpler for hackathon, 5MB limit acceptable
6. **Modular monolith** -- single FastAPI deployment with strict module boundaries (auth, invoices, agents, blockchain, dashboard), each module could become a microservice later
7. **ALB + Fargate direct WebSocket** -- avoids API Gateway 29s hard timeout, ALB supports up to 4000s idle timeout, SSE as fallback
8. **Sonnet for underwriting** (not Opus) -- Opus overkill for rule-based decisions, saves ~$100+ in Bedrock costs, Opus reserved for NL query only
9. **3 agents not 5** -- GST compliance is deterministic rules (tool, not agent), QA validation folded into Underwriting Agent prompt. Same capability, 40-50% lower cost, 20s faster per invoice
10. **ARC-69 metadata standard** -- required for Pera Explorer/marketplace compatibility, metadata in note field of latest acfg transaction
11. **ASA opt-in + transfer** -- application wallet mints, user claims NFT via opt-in, then transfer
12. **Demo mode with pre-computed results** -- failover for 3 test invoices if Bedrock/Algorand is down during demo

### Real-Time Agent Trace (WebSocket via ALB)

Strands `Swarm.stream_async()` -> yields per-event updates (multi_agent_node_start, multi_agent_node_stream, multi_agent_handoff, multi_agent_node_stop) -> Redis PUBLISH -> FastAPI WS handler -> Client
- Hooks: BeforeToolCallEvent / AfterToolCallEvent for granular per-tool streaming
- Reconnection with replay from agent_traces DB table
- Message format: { type, agent, tool, status, message, data, timestamp, step_number }
- SSE fallback endpoint for environments where WebSocket is blocked

### Security

- Cognito JWT on every request (Authorization header with short-lived tokens + refresh token in httpOnly cookie)
- Wallet ownership verified via challenge-response signing
- Rate limiting (Redis-based, 100 req/min)
- Pydantic input validation
- S3 private bucket with presigned URLs
- TLS everywhere, CSP headers, parameterized queries
- IDOR prevention: reusable auth dependency verifies invoice.user_id == jwt.sub on every endpoint
- NL query agent: input sanitization to prevent SQL injection through natural language
- Cognito account lockout: 5 failed attempts -> temporary lockout (enabled in pool config)

### Cost Estimate (~$109-144/month, within $200)

| Service | Est. Cost |
|---------|-----------|
| ECS Fargate (2 tasks) | ~$30 |
| RDS PostgreSQL | $0 (Free Tier) |
| ElastiCache Redis | ~$12 |
| S3 + CloudFront | <$1 |
| Cognito + SNS | ~$5 |
| Textract | ~$5 |
| Bedrock (Sonnet -- all agents) | ~$50-80 |
| Bedrock (Opus -- NL query only) | ~$5-10 |
| Secrets Manager | ~$1 |

---

## Epics and Features

### Epic 1: Project Foundation and Infrastructure (6 features)
- 1.1 Monorepo Scaffold (S, Manoj, P0)
- 1.2 Backend Skeleton (M, Manoj, P0)
- 1.3 Frontend Skeleton (M, Sanjay, P0)
- 1.4 Database Schema + Migrations (M, Manoj, P0)
- 1.5 Docker Compose Local Dev (S, Manoj, P0)
- 1.6 AWS Infrastructure Setup (M, Manoj, P0)

### Epic 2: Authentication and Wallet (5 features)
- 2.1 Cognito Auth Backend (L, Manoj, P0)
- 2.2 Auth UI Login/Register (L, Sanjay, P0)
- 2.3 Wallet Connect Integration (M, Sanjay, P0)
- 2.4 Wallet Linking Backend (M, Manoj, P0)
- 2.5 Wallet Linking Frontend (S, Sanjay, P0)

### Epic 3: Invoice Upload and Storage (4 features)
- 3.1 Invoice Upload Backend (M, Manoj, P0)
- 3.2 Invoice Upload UI (M, Sanjay, P0)
- 3.3 Invoice List Backend (M, Manoj, P0)
- 3.4 Invoice List UI (M, Sanjay, P1)

### Epic 4: AI Agent Processing Pipeline (17 features)
- 4.1 Strands Agent Framework Setup (L, Manoj, P0)
- 4.2 WebSocket Server via ALB (L, Manoj, P0)
- 4.3 WebSocket Client + Processing UI (L, Sanjay, P0)
- 4.4 Tool: extract_invoice - Textract + Claude fallback (L, Manoj, P0)
- 4.5 Tool: validate_fields (M, Manoj, P0)
- 4.5b Tool: validate_gst_compliance - HSN/SAC rates, e-invoice, format rules (M, Manoj, P0)
- 4.6 Tool: verify_gstn - Mock GSTN API (S, Manoj, P0)
- 4.7 Tool: check_fraud - 5-layer detection (L, Manoj, P0)
- 4.8 Tool: get_buyer_intel (M, Manoj, P0)
- 4.8b Tool: get_credit_score - Mock CIBIL (S, Manoj, P1)
- 4.8c Tool: get_company_info - Mock MCA (S, Manoj, P1)
- 4.9 Tool: calculate_risk - multi-signal AI scoring (L, Manoj, P0)
- 4.10 Invoice Processing Agent Assembly (M, Manoj, P0)
- 4.11 Underwriting Agent + Tools (incl. cross_validate_outputs) (L, Manoj, P0)
- 4.12 Swarm Orchestration (L, Manoj, P0)
- 4.13 Invoice Detail UI (L, Sanjay, P0)
- 4.14 Audit Trail View - formatted agent_traces display (M, Sanjay, P1)

### Epic 5: Dashboard and Portfolio (4 features)
- 5.1 Dashboard Summary Backend (M, Manoj, P1)
- 5.2 Dashboard Summary UI with charts (M, Sanjay, P1)
- 5.5 NL Query Agent + Backend - Opus (M, Manoj, P1)
- 5.6 NL Query Chat UI (S, Sanjay, P1)

### Epic 6: Algorand NFT Minting (4 features)
- 6.1 Smart Contract ARC4 + ARC-69 metadata (L, Jeevidha+Manoj, P0)
- 6.2 Tool: mint_nft + ASA opt-in + transfer to user wallet (L, Manoj, P0)
- 6.3 NFT Display UI with Pera Explorer link (M, Sanjay, P0)
- 6.5 Claim NFT flow - user opts-in and receives ASA transfer (M, Sanjay+Manoj, P0)

### Epic 7: Seller Rules (2 features)
- 7.1 Seller Rules CRUD (S, Manoj, P1)
- 7.2 Seller Rules UI (M, Sanjay, P1)

### Epic 8: Polish, Testing and Deployment (6 features)
- 8.1 Critical Path Backend Tests (L, Abhishek, P1)
- 8.2 Critical Path E2E Tests - Playwright (L, Jeevidha, P1)
- 8.3 AWS Deployment (L, Manoj, P1)
- 8.4 Demo Mode - pre-computed results for 3 test invoices (M, Manoj, P1)
- 8.5 Demo Script + 5-Slide Pitch Deck (M, Sanjay, P1)
- 8.6 Demo Polish + Sample Data Seed Script (M, Sanjay, P1)

### Summary: 8 Epics, 42 Features (25 P0, 17 P1, 0 P2)

---

## Milestones

### Milestone 1: Core Pipeline (Days 1-8 / March 17-24)
**Goal:** Login, connect wallet, upload invoice, watch AI extract + validate + verify in real-time.
**Features:** 1.1-1.6, 2.1-2.5, 3.1-3.2, 4.1-4.6 (20 features, all P0)
**Demo:** Login > Connect wallet > Upload PDF > Real-time extraction + validation + GST compliance via WebSocket

### Milestone 2: Full Agent Pipeline + NFT (Days 9-13 / March 25-29)
**Goal:** All agents with Swarm, 5-layer fraud, CIBIL/MCA, auto-approve with cross-validation, NFT on Algorand with ARC-69. Day 13 is INTEGRATION-ONLY (no new features).
**Features:** 4.7-4.14, 4.8b, 4.8c, 6.1-6.3, 6.5, 3.3-3.4, 7.1-7.2 (16 features, P0+P1)
**Demo:** Full 14 AI touchpoints > Cross-validated auto-approve > NFT minted > User claims NFT > Pera Explorer link

### Milestone 3: Dashboard, Deploy & Polish (Days 14-16 / March 30 - April 1)
**Goal:** Dashboard with charts, NL query, tests, demo mode, deployed on AWS.
**Features:** 5.1-5.2, 5.5-5.6, 8.1-8.6 (10 features, all P1)
**Demo:** Complete product on AWS with dashboard + NL query + polished demo

### Buffer: April 2
Bug fixes, demo rehearsal x3, video recording, pitch deck final review, Bedrock quota verification.

---

## Deployment Strategy

**Strategy: Per-milestone (3 deployments)**

| Deploy | When | What | Purpose |
|--------|------|------|---------|
| Deploy 1 | Day 8 (March 24) | M1: Auth + Upload + Extraction | Validate AWS infra, catch issues early |
| Deploy 2 | Day 13 (March 29) | M2: Full pipeline + NFT | Critical checkpoint -- core demo flow on AWS |
| Deploy 3 | Day 16 (April 1) | M3: Dashboard + Polish | Final production deploy for judges |

**Environments:**
- Local: Docker Compose (daily dev)
- AWS (staging = production): ECS Fargate + ALB, RDS, ElastiCache, S3+CloudFront, Cognito

Daily development happens locally. AWS deployments happen at milestone boundaries only.

---

## Implementation Order

### Milestone 1: Core Pipeline (Days 1-8)
1. 1.1 Monorepo Scaffold
2. 1.2 Backend Skeleton | 1.3 Frontend Skeleton | 1.6 AWS Infra (parallel)
3. 1.4 Database Schema | 1.5 Docker Compose
4. 2.1 Cognito Auth BE | 2.2 Auth UI | 2.3 Wallet Connect (parallel)
5. 2.4 Wallet Linking BE | 2.5 Wallet Linking FE
6. 3.1 Invoice Upload BE | 3.2 Invoice Upload UI | 4.1 Agent Framework (parallel)
7. 4.2 WebSocket Server | 4.3 WebSocket Client (parallel)
8. 4.4 extract_invoice | 4.5 validate_fields | 4.5b validate_gst_compliance | 4.6 verify_gstn
--> DEPLOY 1 to AWS

### Milestone 2: Full Pipeline + NFT (Days 9-12 build + Day 13 integration)
9. 4.7 check_fraud 5-layer | 6.1 Smart Contract ARC4+ARC-69 (parallel)
10. 4.8 buyer_intel | 4.8b Mock CIBIL | 4.8c Mock MCA | 4.13 Invoice Detail UI (parallel)
11. 4.9 calculate_risk | 4.10 Agent Assembly | 4.14 Audit Trail View
12. 4.11 Underwriting Agent (incl. cross_validate) | 4.12 Swarm | 6.2 mint_nft + ASA transfer | 6.3 NFT Display | 6.5 Claim NFT | 3.3 Invoice List BE | 3.4 Invoice List UI | 7.1 Rules CRUD | 7.2 Rules UI
13. INTEGRATION DAY -- end-to-end testing, bug fixes, no new features
--> DEPLOY 2 to AWS

### Milestone 3: Dashboard + Deploy + Polish (Days 14-16)
14. 5.1 Dashboard BE | 5.2 Dashboard UI | 8.1 BE Tests | 8.2 E2E Tests (parallel)
15. 5.5 NL Query Agent | 5.6 NL Query UI | 8.4 Demo Mode
16. 8.3 AWS Deploy | 8.5 Demo Script + Pitch Deck | 8.6 Demo Polish + Seed Script
--> DEPLOY 3 (final) to AWS

### April 2: Buffer
Bug fixes, demo rehearsal x3, video recording, pitch deck review, Bedrock quota check

---

## Feature Status

| Feature | Status |
|---------|--------|
| All 42 features | not started |

---

## Deferred to Round 3 (May 20)

| Feature | Why Deferred |
|---------|-------------|
| Real GSTN API integration | Requires government registration, not accessible for hackathon |
| Real CIBIL API integration | Requires RBI-registered entity, using mock instead |
| Real MCA API integration | Requires government portal access, using mock instead |
| Lender Marketplace | Major feature: lenders browse and fund invoices with USDC |
| Real-Time Auctions | Lenders bid competitively, needs marketplace first |
| USDC Escrow Contract | Atomic transfer on full funding, smart contract complexity |
| Payment Settlement | Buyer pays, USDC distributed to lenders |
| Supply Chain Network Effects | Buyer on-time payments benefit all suppliers, needs multi-party data |
| Advanced ML-based Fraud Models | Need training data, currently using Claude-powered 5-layer detection |
| On-Chain Credit Scores (real) | Immutable buyer payment history, needs real transaction data |
| Collection Agent + UI | Impressive but not in demo critical path, 1 backend dev constraint |
| Alerts Backend + UI | Nice-to-have, not core flow |
| Wallet NFT List | User sees NFT on invoice detail page already |
| Scheduled Portfolio Scan | Depends on Collection Agent |
| 5-Agent Architecture | GST compliance is deterministic (tool not agent), QA is folded into underwriting |

---

## Strands SDK Key Notes

- Official AWS project: authors = AWS, opensource@amazon.com, Apache 2.0
- Swarm auto-injects `handoff_to_agent` tool -- reserved name
- Agents in Swarm do NOT share conversation history -- pass context explicitly via handoff
- Session persistence NOT yet supported for Swarm agents -- use own PostgreSQL persistence
- `@tool` decorator does NOT support `pydantic.Field` in `Annotated` -- use docstrings for param descriptions
- Use `Swarm.stream_async()` for real-time events: multi_agent_node_start, multi_agent_node_stream, multi_agent_handoff
- Hooks: BeforeToolCallEvent / AfterToolCallEvent for per-tool WebSocket streaming
- Default model is Bedrock Sonnet in us-west-2 if not specified

---

## Demo Preparation

- **Demo mode**: Pre-computed results for 3 specific test invoices, bypasses Bedrock, streams via WebSocket with 500ms artificial delays
- **Demo script**: 5-7 minutes, exact click sequence: connect wallet (30s) -> login (30s) -> set rules (30s) -> upload invoice (30s) -> watch AI process (60s) -> show NFT on Pera Explorer (30s) -> show dashboard (30s) -> ask NL question (30s) -> upload fake invoice, watch rejection (60s)
- **Pitch deck**: 5 slides -- Problem -> Solution -> Demo -> Architecture -> Roadmap
- **Video**: 3-5 minute recording of the demo flow
- **Competitive positioning**: Compare to KredX, M1xchange, TReDS -- emphasize speed (2 min vs 48-72 hours) and AI autonomy

---

## Pre-Build Action Items

| # | Action | Owner | When |
|---|--------|-------|------|
| 1 | Request Bedrock Sonnet quota increase in target region | Manoj | Day 1 |
| 2 | Fund ARC4 contract account on Algorand testnet (faucet, 20+ ALGO for MBR) | Jeevidha | Day 9 |
| 3 | Set up AlgoKit localnet + ARC4 template | Jeevidha | Day 1-2 |
| 4 | Cognito User Pool with account lockout enabled | Manoj | Day 1-2 |
| 5 | S3 bucket + IAM roles + Secrets Manager setup | Manoj | Day 1-3 |

---

## Change Log

- [2026-03-17] Initial project plan created -- vision, tech stack, architecture confirmed
- [2026-03-17] Tech stack updated: Strands Agents SDK (Bedrock-native) instead of Claude Agent SDK
- [2026-03-17] AI model tiering added: Opus (underwriting, NL query) + Sonnet (processing) + Haiku (collection, lightweight)
- [2026-03-17] AI touchpoints expanded from 2 to 14 (fraud 5-layer, CIBIL mock, MCA mock, NL query)
- [2026-03-17] Resilience additions: circuit breakers, auto-scaling, deep health checks, Redis fallback
- [2026-03-17] Epics and features confirmed: 8 epics, 43 features
- [2026-03-17] Milestones confirmed: M1 (Days 1-8), M2 (Days 9-13), M3 (Days 14-16), Buffer (April 2)
- [2026-03-17] Deferred features documented for Round 3 (May 20)
- [2026-03-18] COMPREHENSIVE AUDIT -- 4 parallel research agents analyzed framework, agents, architecture, plan gaps
- [2026-03-18] Framework confirmed: Strands Agents SDK (NOT CrewAI) -- CrewAI lacks native tool execution callbacks for WebSocket, has LiteLLM indirection, version instability
- [2026-03-18] Agent count confirmed: 3 agents (NOT 5) -- GST compliance absorbed as tool, QA absorbed into Underwriting prompt. Same capability, 40-50% lower cost, 20s faster
- [2026-03-18] Underwriting model changed: Sonnet 4.6 (NOT Opus) -- Opus reserved for NL query only. Saves ~$100+ in Bedrock costs
- [2026-03-18] Architecture: modular monolith with strict module boundaries (NOT microservices, NOT flat monolith)
- [2026-03-18] WebSocket: ALB + Fargate direct (NOT API Gateway) -- avoids 29s hard timeout
- [2026-03-18] NFT: ARC-69 metadata standard adopted, ASA opt-in + transfer flow added, AlgoExplorer replaced with Pera Explorer (AlgoExplorer shut down)
- [2026-03-18] Features cut (P2 -> deferred): Alerts BE/UI, Collection Agent/UI, Wallet NFT List, Scheduled Scan (5 cut)
- [2026-03-18] Features added: validate_gst_compliance tool, Audit Trail View, Demo Mode, Demo Script + Pitch Deck, Claim NFT flow, Demo Polish split (4 added)
- [2026-03-18] Net: 43 -> 42 features (5 cut, 4 added). All remaining features are P0 or P1 (zero P2)
- [2026-03-18] Day 13 designated as INTEGRATION-ONLY day (no new features)
- [2026-03-18] Cost estimate revised: $109-144/month (down from $140-185) due to Sonnet-only agents
- [2026-03-18] Strands SDK technical notes added (session persistence, handoff context, reserved names)
- [2026-03-18] Demo preparation section added (demo mode, demo script, pitch deck, video plan)
- [2026-03-18] Pre-build action items added (Bedrock quota, testnet funding, Cognito lockout)
- [2026-03-18] FRAMEWORK DEEP EVALUATION -- AutoGen and LangGraph evaluated as alternatives to Strands
- [2026-03-18] AutoGen REJECTED: conversation-based model (shared message thread wastes tokens), indirect Bedrock (via anthropic SDK), coarse tool callbacks, 3 separate packages, tiktoken for Claude token counting
- [2026-03-18] LangGraph REJECTED: best streaming of all frameworks but indirect Bedrock (via langchain-aws), no Bedrock examples in repo, verbose tool definitions (node functions), graph abstraction overkill for 2-agent sequential pipeline
- [2026-03-18] Strands Agents SDK CONFIRMED as FINAL choice after evaluating all 4 frameworks (Strands, CrewAI, LangGraph, AutoGen). No further framework evaluation needed.
- [2026-03-18] Agent count CONFIRMED as FINAL: 2 pipeline agents (Invoice Processing + Underwriting) + 1 standalone (NL Query) = 3 total. Agent vs tool decision framework documented in lessons.md.
- [2026-03-18] DevOps + deployment reassigned: Manoj owns AWS infra (1.6) and deployment (8.3) instead of Abhishek. Abhishek's role narrowed to backend testing (8.1) only.
- [2026-03-18] ALGORAND STACK VERIFICATION -- 3 parallel agents verified entire blockchain stack. AlgoKit 3.0 corrected to 2.x (no 3.0 exists). SDK versions pinned: algopy v3.5.0, puyapy v5.8.0, py-algorand-sdk v2.11.1, algosdk v3 (JS). Pera≠MyAlgo corrected. Testnet endpoints confirmed (Algonode). Static export risk flagged (unverified with use-wallet-react).
