# ChainFactor AI - Team Brief

**Hackathon:** AlgoBharat Hack Series 3.0 (Future of Finance + Agentic Commerce)
**Prize Pool:** USD 30,000
**Our Deadline:** April 2, 2026 (submission: April 15)
**Budget:** $200

---

## What Are We Building?

An AI-powered invoice financing platform for Indian SMEs on Algorand blockchain.

**One-line pitch:** "Upload an invoice, AI verifies it in 30 seconds, and it becomes a blockchain asset."

**Why it matters:** 63 million Indian SMEs have $100B locked in unpaid invoices. Current solutions take 48-72 hours. We do it in under 60 seconds with AI agents.

---

## The Demo (What Judges Will See)

1. Connect Pera wallet + login
2. Set auto-approve rules ("approve invoices under 5L with risk > 60")
3. Upload an invoice PDF
4. Watch 3 AI agents process it in real-time (14 steps visible on screen)
5. See: extraction, validation, 5-layer fraud check, GSTIN verified, CIBIL/MCA score, risk score with AI explanation, financing recommendation
6. Agent auto-approves and mints NFT on Algorand
7. Click AlgoExplorer link - see it on-chain
8. Upload a fake invoice - watch it get REJECTED
9. Dashboard with portfolio stats, alerts, collection agent, chat query

---

## Team Assignments

### Sanjay M (Frontend + Team Lead)
**Stack:** Next.js 14, TailwindCSS, TypeScript, @txnlab/use-wallet-react

**Your features (17 total):**

| Milestone | What You Build | Days |
|-----------|---------------|------|
| M1 (Days 1-8) | Frontend scaffold, login/register UI, wallet connect, wallet linking UI, invoice upload UI, WebSocket client + real-time processing view | 1-7 |
| M2 (Days 9-13) | Invoice detail page (all AI results displayed), NFT display card, invoice list, seller rules settings page | 9-13 |
| M3 (Days 14-16) | Dashboard with stats/charts, collection UI, alerts panel, NL query chat bar, demo polish | 14-16 |

**Key things to know:**
- Wallet: Use `@txnlab/use-wallet-react` (official Algorand lib, supports Pera + Defly)
- Auth: AWS Cognito handles login/OTP. Store JWT in httpOnly cookies.
- WebSocket: Connect to `WSS /ws/processing/{invoice_id}` after upload. Display each agent step as it arrives.
- Static export: `next export` -> files go to S3 + CloudFront

---

### Manoj RS (Backend + AI)
**Stack:** FastAPI, Python 3.11+, Strands Agents SDK, Amazon Textract, Bedrock (Claude), AlgoKit

**Your features (31 total):**

| Milestone | What You Build | Days |
|-----------|---------------|------|
| M1 (Days 1-8) | Monorepo scaffold, FastAPI skeleton, DB schema (9 tables), Docker Compose, Cognito auth backend, wallet linking backend, invoice upload + S3, Strands agent framework, WebSocket server, 3 agent tools (extract, validate, GSTN) | 1-8 |
| M2 (Days 9-13) | 5-layer fraud detection tool, buyer intel tool, mock CIBIL + MCA tools, multi-signal risk scoring tool, Invoice Processing Agent assembly, Underwriting Agent + tools, Swarm orchestration, mint_nft tool, invoice list API, seller rules API | 9-13 |
| M3 (Days 14-16) | Dashboard API, Collection Agent + tools, alerts API, NL query agent (Opus), scheduled portfolio scan, deployment support | 14-16 |

**Key things to know:**
- Agents use Strands SDK with `@tool` decorator (NOT raw Bedrock API calls)
- 3 agents in a Swarm: Processing (Sonnet) -> Underwriting (Opus) -> Collection (Haiku)
- Agent callbacks publish to Redis -> WebSocket forwards to frontend
- NFT minting uses an application wallet (not user's wallet)
- Mock GSTN/CIBIL/MCA: deterministic responses based on GSTIN prefix

---

### Abhishek Reddy (Support - DevOps + Backend Testing)
**Your features (3 + ongoing support):**

| What | Days |
|------|------|
| AWS Infrastructure Setup: Cognito User Pool, S3 bucket, Secrets Manager, Bedrock model access, IAM roles | Days 1-3 |
| Backend Tests: pytest suite for all 21 agent tools + API endpoints, 80% coverage target | Days 14-15 |
| AWS Deployment: Dockerize backend, ECS Fargate setup, RDS, ElastiCache, S3+CloudFront, GitHub Actions CI/CD | Day 16 |

**Key things to know:**
- AWS services needed: Cognito, S3, Secrets Manager, Bedrock, Textract, ECS Fargate, RDS, ElastiCache, CloudFront, CloudWatch
- Backend runs in Docker container on ECS Fargate (0.5 vCPU, 1GB RAM, 2 tasks)
- Frontend is static files on S3 behind CloudFront
- All secrets go in AWS Secrets Manager (never in code or env files)

---

### Jeevidha (Support - Smart Contract + Frontend Testing)
**Your features (2 + ongoing support):**

| What | Days |
|------|------|
| Smart Contract: ARC4 Algorand Python contract for Invoice NFTs, compile + deploy to testnet via AlgoKit | Days 9-10 |
| Frontend Tests: Jest unit tests + Playwright E2E for critical path (login -> upload -> processing -> NFT) | Days 14-15 |

**Key things to know:**
- Smart contract uses Algorand Python (NOT PyTeal - it's deprecated)
- AlgoKit 3.0 for development + deployment
- Contract has: `create_invoice_nft()` method with metadata (invoice summary, risk score, doc hash)
- Target: Algorand TESTNET only (never mainnet)
- Use `algokit localnet start` for local development

---

## Tech Stack Quick Reference

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, TypeScript |
| Wallet | @txnlab/use-wallet-react (Pera + Defly) |
| Auth | AWS Cognito + SNS |
| Backend | FastAPI, Python 3.11+ |
| AI Agents | Strands Agents SDK (Bedrock-native) |
| AI Models | Opus 4.6 / Sonnet 4.6 / Haiku 4.5 via Bedrock |
| OCR | Amazon Textract (primary) + Claude vision (fallback) |
| Blockchain | Algorand Python ARC4 + AlgoKit 3.0 (Testnet) |
| Database | PostgreSQL (RDS) |
| Cache | Redis (ElastiCache) |
| Storage | S3 |
| Hosting | ECS Fargate (backend) + S3+CloudFront (frontend) |

---

## 3-Agent Architecture (How It Works)

```
User uploads invoice
        |
        v
[Invoice Processing Agent] (Sonnet 4.6)
  - Extracts data from PDF (Textract + Claude fallback)
  - Validates fields (math, consistency)
  - Runs 5-layer fraud detection
  - Verifies GSTIN (mock API)
  - Gets CIBIL credit score (mock)
  - Gets MCA company info (mock)
  - Generates buyer intelligence brief
  - Calculates multi-signal risk score + AI explanation
  - Generates invoice summary for NFT
        |
        | HANDOFF
        v
[Underwriting Agent] (Opus 4.6)
  - Checks seller's auto-approve rules
  - Makes autonomous approve/reject/flag decision
  - Logs reasoning trace
        |
        | HANDOFF (if approved)
        v
[Invoice Processing Agent] mints NFT on Algorand
        |
        v
NFT on Algorand Testnet + AlgoExplorer link

[Collection Agent] (Haiku 4.5) - runs separately
  - Generates payment reminders on demand
  - Scans portfolio daily for overdue invoices
  - Suggests escalation strategies
```

All steps are visible to the user in real-time via WebSocket.

---

## Timeline

```
Week 1 (March 17-24): MILESTONE 1 - Core Pipeline
  - Project setup, auth, wallet, upload, agent framework, WebSocket, first 3 tools
  - DEPLOY 1 to AWS on Day 8

Week 2 (March 25-29): MILESTONE 2 - Full Pipeline + NFT
  - Remaining tools, all 3 agents, Swarm orchestration, smart contract, NFT minting
  - DEPLOY 2 to AWS on Day 13

Week 2.5 (March 30 - April 1): MILESTONE 3 - Dashboard + Polish
  - Dashboard, collection agent, NL query, tests, final deployment
  - DEPLOY 3 (final) on Day 16

April 2: Buffer day - bug fixes, demo rehearsal, documentation
```

---

## What We Are NOT Building (Deferred to Round 3 - May 20)

- Real GSTN/CIBIL/MCA API integration (using mocks)
- Lender marketplace (lenders browse and fund invoices)
- Real-time auctions (competitive bidding)
- USDC escrow and payment settlement
- Supply chain network effects
- Advanced ML fraud models (using Claude-powered detection)

---

## Getting Started (Day 1)

1. Clone the repo
2. Run `docker-compose up -d` (starts PostgreSQL + Redis)
3. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
4. Frontend: `cd frontend && npm install && npm run dev`
5. Algorand: `algokit localnet start`

**Questions?** Check `tasks/project-plan.md` for the full plan or `tasks/architecture-raw.md` for deep architecture details.
