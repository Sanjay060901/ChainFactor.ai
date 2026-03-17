# ChainFactor AI — Project Plan

## Project Vision

ChainFactor AI is an AI-powered invoice financing platform for Indian SMEs built on the Algorand blockchain. SMEs connect their wallet, upload an invoice, get AI-powered extraction and verification in under 30 seconds, receive a risk score, and mint the verified invoice as an NFT on Algorand testnet.

**Problem:** India's 63 million SMEs have ~$100B locked in unpaid invoices (45-90 day cycles). Existing solutions take 48-72 hours at 18-24% rates.

**For:** AlgoBharat Hack Series 3.0 (Future of Finance + Agentic Commerce). End users: Indian SME sellers.

**Success for v1:** One complete end-to-end flow — wallet connect > invoice upload > AI agent processing (14 touchpoints, 5-layer fraud, CIBIL/MCA scoring) > GSTN verification > risk scoring > auto-approve > NFT minting > dashboard + collection agent + NL query. Working prototype with polished demo.

**Constraints:**
- Deadline: April 2, 2026 (Round 2 due April 15)
- Budget: $200
- Team: 4 — Sanjay M (frontend + lead), Manoj RS (backend + AI), Abhishek Reddy & Jeevidha (support)
- Quality: Enterprise-grade security

**Out of scope for v1:** Lender marketplace, real-time auctions, USDC escrow, payment settlement, real GSTN API, CIBIL/MCA integration.

---

## Tech Stack

- **Frontend**: Next.js 14 (App Router) + TailwindCSS -> S3 + CloudFront
- **Wallet**: @txnlab/use-wallet-react + use-wallet-ui (Pera + Defly, Algorand)
- **Auth**: AWS Cognito + SNS (OTP/notifications)
- **Backend**: FastAPI (Python 3.11+) on ECS Fargate
- **Agentic Framework**: Strands Agents SDK (strands-agents) -- Bedrock-native
- **Multi-Agent**: Strands Swarm -- 3-agent system with handoffs
- **OCR Primary**: Amazon Textract
- **AI Models (tiered)**: Opus 4.6 (underwriting decisions, NL query, fraud escalation) + Sonnet 4.6 (invoice processing, risk analysis) + Haiku 4.5 (collection, lightweight tools) via Amazon Bedrock
- **Blockchain**: Algorand Python (ARC4) + AlgoKit 3.0 (Testnet)
- **Database**: PostgreSQL on RDS (Free Tier)
- **Cache**: Redis on ElastiCache
- **Storage**: AWS S3
- **Secrets**: AWS Secrets Manager
- **Monitoring**: CloudWatch
- **CI/CD**: GitHub Actions
- **Containerization**: Docker + docker-compose (local dev)
- **Testing**: pytest (backend), Jest + Playwright (frontend)

---

## Architecture

Full architecture document: tasks/architecture-raw.md

### Component Layers

1. **Client Layer**: Next.js 14 + Wallet SDK + WebSocket Client
2. **Edge/CDN Layer**: CloudFront (static) + ALB (API)
3. **Application Layer**: FastAPI on ECS Fargate (monolith with clean module separation)
4. **Agent Layer**: Strands Swarm (3 agents with handoff orchestration)
5. **Data Layer**: PostgreSQL (RDS) + Redis (ElastiCache) + S3
6. **External Services**: Textract, Bedrock, Algorand Testnet, Cognito, SNS

### 3-Agent Swarm Architecture

**Agent 1: Invoice Processing Agent (Sonnet 4.6)**
Tools: extract_invoice, validate_fields, check_fraud, verify_gstn, get_buyer_intel, calculate_risk, generate_summary, mint_nft

**Agent 2: Underwriting Agent (Opus 4.6)**
Tools: get_seller_rules, get_invoice_data, approve_invoice, flag_for_review, log_decision

**Agent 3: Collection Agent (Haiku 4.5)**
Tools: get_overdue_invoices, get_buyer_history, generate_reminder, suggest_escalation, scan_portfolio

Flow: Invoice Agent -> handoff -> Underwriting Agent -> handoff back for mint_nft -> Collection Agent (on-demand/scheduled)

### Key Architectural Decisions (ADRs)

1. **Backend-side NFT signing** (not user wallet) -- enables fully automated real-time flow
2. **Redis pub/sub for WebSocket bridge** -- decouples agent callbacks from WS handlers
3. **Strands Agents SDK over direct Bedrock API** -- built-in tool dispatch, Swarm orchestration
4. **Cognito + wallet dual identity** -- familiar login for Indian SMEs + wallet for blockchain
5. **Synchronous Textract** -- simpler for hackathon, 5MB limit acceptable
6. **Single FastAPI monolith** -- one deployment, clean module separation, ideal for hackathon pace

### Real-Time Agent Trace (WebSocket)

Agent tool callbacks -> Redis PUBLISH -> FastAPI WS handler -> Client
- Reconnection with replay from agent_traces DB table
- Message format: { type, agent, tool, status, message, data, timestamp, step_number }

### Security

- Cognito JWT on every request
- Wallet ownership verified via challenge-response signing
- Rate limiting (Redis-based, 100 req/min)
- Pydantic input validation
- S3 private bucket with presigned URLs
- TLS everywhere, CSP headers, parameterized queries

### Cost Estimate (~$140-185/month, within $200)

| Service | Est. Cost |
|---------|-----------|
| ECS Fargate (2 tasks) | ~$30 |
| RDS PostgreSQL | $0 (Free Tier) |
| ElastiCache Redis | ~$12 |
| S3 + CloudFront | <$1 |
| Cognito + SNS | ~$5 |
| Textract | ~$5 |
| Bedrock (Sonnet) | ~$80-120 |
| Bedrock (Haiku) | ~$5-10 |
| Secrets Manager | ~$1 |

---

## Epics and Features

### Epic 1: Project Foundation and Infrastructure (6 features)
- 1.1 Monorepo Scaffold (S, Manoj, P0)
- 1.2 Backend Skeleton (M, Manoj, P0)
- 1.3 Frontend Skeleton (M, Sanjay, P0)
- 1.4 Database Schema + Migrations (M, Manoj, P0)
- 1.5 Docker Compose Local Dev (S, Manoj, P0)
- 1.6 AWS Infrastructure Setup (M, Abhishek, P0)

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

### Epic 4: AI Agent Processing Pipeline (16 features)
- 4.1 Strands Agent Framework Setup (L, Manoj, P0)
- 4.2 WebSocket Server (L, Manoj, P0)
- 4.3 WebSocket Client + Processing UI (L, Sanjay, P0)
- 4.4 Tool: extract_invoice - Textract + Claude fallback (L, Manoj, P0)
- 4.5 Tool: validate_fields (M, Manoj, P0)
- 4.6 Tool: verify_gstn - Mock GSTN API (S, Manoj, P0)
- 4.7 Tool: check_fraud - 5-layer detection (L, Manoj, P0)
- 4.8 Tool: get_buyer_intel (M, Manoj, P0)
- 4.8b Tool: get_credit_score - Mock CIBIL (S, Manoj, P1)
- 4.8c Tool: get_company_info - Mock MCA (S, Manoj, P1)
- 4.9 Tool: calculate_risk - multi-signal AI scoring (L, Manoj, P0)
- 4.10 Invoice Processing Agent Assembly (M, Manoj, P0)
- 4.11 Underwriting Agent + Tools (L, Manoj, P0)
- 4.12 Swarm Orchestration (L, Manoj, P0)
- 4.13 Invoice Detail UI (L, Sanjay, P0)

### Epic 5: Dashboard and Portfolio (6 features)
- 5.1 Dashboard Summary Backend (M, Manoj, P1)
- 5.2 Dashboard Summary UI (M, Sanjay, P1)
- 5.3 Alerts Backend (S, Manoj, P2)
- 5.4 Alerts UI (S, Sanjay, P2)
- 5.5 NL Query Agent + Backend - Opus (M, Manoj, P1)
- 5.6 NL Query Chat UI (S, Sanjay, P1)

### Epic 6: Algorand NFT Minting (4 features)
- 6.1 Smart Contract ARC4 (L, Jeevidha+Manoj, P0)
- 6.2 Tool: mint_nft (L, Manoj, P0)
- 6.3 NFT Display UI (M, Sanjay, P0)
- 6.4 Wallet NFT List (S, Sanjay+Manoj, P2)

### Epic 7: Seller Rules and Collection (5 features)
- 7.1 Seller Rules CRUD (S, Manoj, P1)
- 7.2 Seller Rules UI (M, Sanjay, P1)
- 7.3 Collection Agent + Tools (L, Manoj, P2)
- 7.4 Collection UI (M, Sanjay, P2)
- 7.5 Scheduled Portfolio Scan - Cron (S, Manoj, P1)

### Epic 8: Polish, Testing and Deployment (4 features)
- 8.1 Backend Tests (L, Abhishek, P1)
- 8.2 Frontend Tests (L, Jeevidha, P1)
- 8.3 AWS Deployment (L, Abhishek+Manoj, P1)
- 8.4 Demo Polish + Sample Data (M, Sanjay, P1)

### Summary: 8 Epics, 43 Features (25 P0, 14 P1, 4 P2)

---

## Milestones

### Milestone 1: Core Pipeline (Days 1-8 / March 17-24)
**Goal:** Login, connect wallet, upload invoice, watch AI extract + validate + verify in real-time.
**Features:** 1.1-1.6, 2.1-2.5, 3.1-3.2, 4.1-4.6 (19 features, all P0)
**Demo:** Login > Connect wallet > Upload PDF > Real-time extraction + validation via WebSocket

### Milestone 2: Full Agent Pipeline + NFT (Days 9-13 / March 25-29)
**Goal:** All 3 agents with Swarm, 5-layer fraud, CIBIL/MCA, auto-approve, NFT on Algorand.
**Features:** 4.7-4.13, 4.8b, 4.8c, 6.1-6.3, 3.3-3.4, 7.1-7.2 (16 features, P0+P1)
**Demo:** Full 14 AI touchpoints > Auto-approve > NFT minted > AlgoExplorer link

### Milestone 3: Dashboard, Collection, Deploy & Polish (Days 14-16 / March 30 - April 1)
**Goal:** Dashboard, collection agent, NL query, scheduled scan, deployed on AWS.
**Features:** 5.1-5.6, 7.3-7.5, 6.4, 8.1-8.4 (14 features, P1+P2)
**Demo:** Complete product on AWS with dashboard + alerts + collection + NL query

### Buffer: April 2
Bug fixes, demo rehearsal, documentation, video recording.

---

## Deployment Strategy

**Strategy: Per-milestone (3 deployments)**

| Deploy | When | What | Purpose |
|--------|------|------|---------|
| Deploy 1 | Day 8 (March 24) | M1: Auth + Upload + Extraction | Validate AWS infra, catch issues early |
| Deploy 2 | Day 13 (March 29) | M2: Full pipeline + NFT | Critical checkpoint -- core demo flow on AWS |
| Deploy 3 | Day 16 (April 1) | M3: Dashboard + Collection + Polish | Final production deploy for judges |

**Environments:**
- Local: Docker Compose (daily dev)
- AWS (staging = production): ECS Fargate, RDS, ElastiCache, S3+CloudFront, Cognito

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
8. 4.4 extract_invoice | 4.5 validate_fields | 4.6 verify_gstn
--> DEPLOY 1 to AWS

### Milestone 2: Full Pipeline + NFT (Days 9-13)
9. 4.7 check_fraud 5-layer | 6.1 Smart Contract (parallel)
10. 4.8 buyer_intel | 4.8b Mock CIBIL | 4.8c Mock MCA | 4.13 Invoice Detail UI (parallel)
11. 4.9 calculate_risk | 4.10 Agent Assembly
12. 4.11 Underwriting Agent | 4.12 Swarm | 6.3 NFT Display UI (parallel)
13. 6.2 mint_nft | 3.3 Invoice List BE | 3.4 Invoice List UI | 7.1 Rules CRUD | 7.2 Rules UI
--> DEPLOY 2 to AWS

### Milestone 3: Dashboard + Collection + Deploy (Days 14-16)
14. 5.1 Dashboard BE | 5.2 Dashboard UI | 7.3 Collection Agent | 8.1 BE Tests | 8.2 FE Tests (parallel)
15. 7.4 Collection UI | 5.3 Alerts BE | 5.4 Alerts UI | 5.5 NL Query Agent | 5.6 NL Query UI | 7.5 Scheduled Scan | 6.4 Wallet NFT List
16. 8.3 AWS Deploy | 8.4 Demo Polish
--> DEPLOY 3 (final) to AWS

### April 2: Buffer
Bug fixes, demo rehearsal x3, README, video recording

---

## Feature Status

| Feature | Status |
|---------|--------|
| All 43 features | not started |

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
