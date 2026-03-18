# ChainFactor AI

## Project Overview

ChainFactor AI is an AI-powered invoice financing platform for Indian SMEs built on the Algorand blockchain. SMEs connect their Algorand wallet, upload an invoice, and an agentic AI system processes it end-to-end: extracting data, validating fields, checking GST compliance, running 5-layer fraud detection, verifying GSTIN, assessing CIBIL/MCA credit scores, calculating multi-signal risk, making autonomous underwriting decisions with cross-validation, and minting the verified invoice as an ARC-69 NFT on Algorand testnet -- all in under 2 minutes.

Built for the AlgoBharat Hack Series 3.0 hackathon (Future of Finance + Agentic Commerce). Team of 4: Sanjay M (frontend), Manoj RS (backend + AI), Abhishek Reddy (support/DevOps), Jeevidha (support/testing).

**Current state:** New project, planning complete (comprehensive audit done), implementation starting.

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TailwindCSS, TypeScript
- **Wallet**: @txnlab/use-wallet-react + use-wallet-ui (Pera + Defly, Algorand)
- **Auth**: AWS Cognito + SNS (OTP)
- **Backend**: FastAPI, Python 3.11+, Uvicorn -- modular monolith with strict module boundaries
- **Agentic Framework**: Strands Agents SDK (strands-agents, Apache 2.0) -- official AWS project, Bedrock-native
- **Multi-Agent**: Strands Swarm (3-agent system with tool-based handoffs)
- **AI Models**: Sonnet 4.6 (invoice processing, underwriting, risk), Haiku 4.5 (lightweight tools), Opus 4.6 (NL query only) via Bedrock
- **OCR**: Amazon Textract (primary), Claude vision (fallback)
- **Blockchain**: Algorand Python (ARC4) + AlgoKit 3.0, Algorand Testnet, ARC-69 metadata standard
- **Block Explorer**: Pera Explorer (explorer.perawallet.app) -- NOT AlgoExplorer (shut down)
- **Database**: PostgreSQL 15 on AWS RDS (Free Tier), SQLAlchemy + Alembic
- **Cache**: Redis on AWS ElastiCache
- **Storage**: AWS S3
- **Hosting**: ECS Fargate + ALB (backend + WebSocket), S3 + CloudFront (frontend)
- **CI/CD**: GitHub Actions
- **Testing**: pytest (backend), Jest + Playwright (frontend)

## Architecture

6-layer architecture: Client > Edge/CDN > Application > Agent > Data > External Services

### 3-Agent Swarm
- **Invoice Processing Agent (Sonnet 4.6)**: extract_invoice, validate_fields, validate_gst_compliance, check_fraud, verify_gstn, get_buyer_intel, get_credit_score, get_company_info, calculate_risk, generate_summary, mint_nft
- **Underwriting Agent (Sonnet 4.6)**: cross_validate_outputs, get_seller_rules, get_invoice_data, approve_invoice, reject_invoice, flag_for_review, log_decision
- **Collection Agent (Haiku 4.5)**: DEFERRED to Round 3

Flow: Invoice Agent -> handoff (Strands Swarm tool-based) -> Underwriting Agent -> handoff back for mint_nft

**NL Query Agent (Opus 4.6)**: standalone, not in Swarm, on-demand only

### Key Decisions
- Backend-side NFT signing (application wallet) + ASA opt-in + transfer to user wallet
- ALB + Fargate direct WebSocket (NOT API Gateway -- avoids 29s hard timeout), SSE fallback
- Redis pub/sub bridges Strands stream_async() events to WebSocket handlers
- Strands over CrewAI (native tool callbacks, no LiteLLM layer, AWS-backed)
- Sonnet for underwriting (NOT Opus -- saves $100+, Opus only for NL query)
- 3 agents not 5 (GST compliance = tool, QA = folded into Underwriting prompt)
- Cognito + wallet dual identity (familiar login + blockchain features)
- Synchronous Textract (5MB limit, simpler for hackathon)
- Modular monolith with strict module boundaries (auth, invoices, agents, blockchain, dashboard)
- ARC-69 metadata standard for NFTs
- Mock GSTN/CIBIL/MCA APIs (real APIs require government registration)

## Key Files

| Path | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry point, CORS, lifespan (planned) |
| `backend/app/config.py` | Settings from Secrets Manager + env vars (planned) |
| `backend/app/modules/auth/` | Auth module: Cognito integration, JWT middleware (planned) |
| `backend/app/modules/invoices/` | Invoice module: upload, processing, list (planned) |
| `backend/app/modules/agents/` | Agent module: Strands agents, tools, swarm (planned) |
| `backend/app/modules/blockchain/` | Blockchain module: Algorand service, NFT minting (planned) |
| `backend/app/modules/dashboard/` | Dashboard module: stats, NL query (planned) |
| `backend/app/agents/tools/` | Tool implementations: extraction, validation, fraud, risk, gstn, gst_compliance, cibil, mca, nft, cross_validate (planned) |
| `backend/app/models/` | SQLAlchemy models: user, invoice, risk_assessment, underwriting, nft_record, agent_trace (planned) |
| `backend/app/schemas/` | Pydantic request/response schemas (planned) |
| `contracts/invoice_nft/contract.py` | ARC4 + ARC-69 smart contract in Algorand Python (planned) |
| `frontend/src/app/` | Next.js App Router pages: auth, dashboard, invoices (planned) |
| `frontend/src/components/` | React components: wallet, invoice, dashboard, ui (planned) |
| `frontend/src/hooks/` | Custom hooks: useWebSocket, useInvoiceProcessing, useAuth (planned) |
| `infra/docker-compose.yml` | Local dev: PostgreSQL, Redis, FastAPI, Next.js (planned) |
| `tasks/project-plan.md` | Master project plan with epics, features, milestones |
| `tasks/architecture-raw.md` | Full architecture document (58KB) |

## Commands

```bash
# Local Development
docker-compose up -d                    # Start PostgreSQL + Redis + backend + frontend
cd backend && pip install -r requirements.txt  # Install Python deps
cd backend && uvicorn app.main:app --reload    # Run backend (dev)
cd frontend && npm install              # Install Node deps
cd frontend && npm run dev              # Run frontend (dev)

# Database
cd backend && alembic upgrade head      # Run migrations
cd backend && alembic revision --autogenerate -m "description"  # Create migration

# Testing
cd backend && pytest                    # Backend tests
cd frontend && npm test                 # Frontend tests
cd frontend && npx playwright test      # E2E tests

# Algorand
algokit localnet start                  # Start local Algorand blockchain
cd contracts && algokit deploy           # Deploy smart contract to testnet

# Docker
docker build -t chainfactor-backend ./backend   # Build backend image
docker-compose -f infra/docker-compose.yml up   # Full local stack

# Deployment (via GitHub Actions, or manual)
# verify after first feature is implemented
```

## Configuration

- **Backend config**: `backend/app/config.py` -- reads from env vars, falls back to Secrets Manager
- **Key settings**: DATABASE_URL, REDIS_URL, AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID, S3_BUCKET_NAME, ALGORAND_APP_WALLET_MNEMONIC, DEMO_MODE
- **Environment variables override** all settings (12-factor app pattern)
- **Secrets**: Never in code. API keys and mnemonics in AWS Secrets Manager.
- **.env.example**: Template for local development (committed). `.env`: Actual values (gitignored).
- **DEMO_MODE**: When true, returns pre-computed results for 3 test invoices (Bedrock/Algorand failover)

## Project-Specific Rules

- Check `tasks/lessons.md` at session start. Update it after any correction.
- All agents use Strands Agents SDK with `@tool` decorator pattern -- never raw Bedrock API calls
- Use `Swarm.stream_async()` for real-time events, wire to Redis pub/sub for WebSocket
- Strands hooks: BeforeToolCallEvent / AfterToolCallEvent for per-tool WebSocket streaming
- Swarm agents do NOT share conversation history -- pass context explicitly via handoff
- `handoff_to_agent` is a reserved tool name (auto-injected by Strands Swarm)
- `@tool` decorator does NOT support `pydantic.Field` in `Annotated` -- use docstrings for param descriptions
- Mock services (GSTN, CIBIL, MCA) use deterministic rules based on GSTIN prefix -- document the rules in code comments
- Agent reasoning traces must be persisted to `agent_traces` table AND streamed via WebSocket -- never skip either
- Invoice processing is always async (background task) -- the API returns immediately with invoice_id + ws_url
- NFT minting uses the application wallet, then user opts-in and receives ASA transfer
- All API endpoints require Cognito JWT except health checks
- IDOR prevention: reusable auth dependency verifies invoice.user_id == jwt.sub on every endpoint
- Redis is used for: WebSocket pub/sub, session cache, rate limiting, GSTN cache (24h TTL)
- PostgreSQL JSONB columns for: line_items, extracted_data, fraud_flags, buyer_intel, rules_snapshot, custom_rules
- File uploads go directly to S3, never stored on the server filesystem
- Algorand operations target TESTNET only -- never mainnet
- Use Pera Explorer (explorer.perawallet.app) for block explorer links -- NOT AlgoExplorer (shut down)
- ARC-69 metadata standard for NFT metadata (note field of latest acfg transaction)
- Frontend is statically exported (next export) and served via S3 + CloudFront
- Underwriting Agent uses Sonnet (NOT Opus) -- Opus is reserved for NL query only
- Store completed pipeline step results in DB for checkpoint/resume on retry

## Deployment

- **Strategy**: Per-milestone (3 deployments: Day 8, Day 13, Day 16)
- **Backend**: Docker image -> ECR -> ECS Fargate (0.5 vCPU, 1GB RAM, 2 tasks) behind ALB
- **WebSocket**: ALB direct (NOT API Gateway) -- supports up to 4000s idle timeout, SSE fallback
- **Frontend**: next export -> S3 bucket -> CloudFront distribution
- **Database**: RDS PostgreSQL (db.t3.micro, Free Tier)
- **Cache**: ElastiCache Redis (cache.t3.micro)
- **CI/CD**: GitHub Actions -- lint, test, build, deploy on push to main
- **Environments**: Local (Docker Compose) + AWS (staging = production for hackathon)

## Known Gotchas

- AlgoExplorer is SHUT DOWN -- use Pera Explorer (explorer.perawallet.app) or Allo (allo.info) instead
- Strands Swarm session persistence NOT yet supported -- use own PostgreSQL persistence for state
- Strands Swarm agents do NOT share conversation history -- must pass context explicitly via handoff
- CrewAI was evaluated and REJECTED -- lacks native tool execution callbacks for WebSocket, has LiteLLM indirection layer, version instability
- Bedrock default Sonnet RPM may be low (4-8 RPM) -- request quota increase on Day 1
- ARC4 contracts need inner transactions for ASA creation -- contract must be funded with ALGO for MBR (0.1 ALGO per ASA)
- Cognito JWT: use Authorization header (not cookie) to avoid CSRF issues
- 5-agent architecture was evaluated and REJECTED -- GST compliance is deterministic (tool not agent), QA is folded into Underwriting prompt. Same capability, lower cost, faster.
