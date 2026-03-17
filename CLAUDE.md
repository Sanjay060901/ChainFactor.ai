# ChainFactor AI

## Project Overview

ChainFactor AI is an AI-powered invoice financing platform for Indian SMEs built on the Algorand blockchain. SMEs connect their Algorand wallet, upload an invoice, and an agentic AI system processes it end-to-end: extracting data, validating fields, running 5-layer fraud detection, verifying GSTIN, assessing CIBIL/MCA credit scores, calculating multi-signal risk, making autonomous underwriting decisions, and minting the verified invoice as an NFT on Algorand testnet -- all in under 60 seconds.

Built for the AlgoBharat Hack Series 3.0 hackathon (Future of Finance + Agentic Commerce). Team of 4: Sanjay M (frontend), Manoj RS (backend + AI), Abhishek Reddy (support/DevOps), Jeevidha (support/testing).

**Current state:** New project, planning complete, implementation starting.

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TailwindCSS, TypeScript
- **Wallet**: @txnlab/use-wallet-react + use-wallet-ui (Pera + Defly, Algorand)
- **Auth**: AWS Cognito + SNS (OTP)
- **Backend**: FastAPI, Python 3.11+, Uvicorn
- **Agentic Framework**: Strands Agents SDK (strands-agents) via Amazon Bedrock
- **Multi-Agent**: Strands Swarm (3-agent system with handoffs)
- **AI Models**: Opus 4.6 (underwriting, NL query), Sonnet 4.6 (invoice processing, risk), Haiku 4.5 (collection, lightweight) via Bedrock
- **OCR**: Amazon Textract (primary), Claude vision (fallback)
- **Blockchain**: Algorand Python (ARC4) + AlgoKit 3.0, Algorand Testnet
- **Database**: PostgreSQL 15 on AWS RDS (Free Tier), SQLAlchemy + Alembic
- **Cache**: Redis on AWS ElastiCache
- **Storage**: AWS S3
- **Hosting**: ECS Fargate (backend), S3 + CloudFront (frontend)
- **CI/CD**: GitHub Actions
- **Testing**: pytest (backend), Jest + Playwright (frontend)

## Architecture

6-layer architecture: Client > Edge/CDN > Application > Agent > Data > External Services

### 3-Agent Swarm
- **Invoice Processing Agent (Sonnet 4.6)**: extract_invoice, validate_fields, check_fraud, verify_gstn, get_buyer_intel, get_credit_score, get_company_info, calculate_risk, generate_summary, mint_nft
- **Underwriting Agent (Opus 4.6)**: get_seller_rules, get_invoice_data, approve_invoice, flag_for_review, log_decision
- **Collection Agent (Haiku 4.5)**: get_overdue_invoices, get_buyer_history, generate_reminder, suggest_escalation, scan_portfolio

Flow: Invoice Agent -> handoff -> Underwriting Agent -> handoff back for mint_nft

### Key Decisions
- Backend-side NFT signing (application wallet, not user wallet)
- Redis pub/sub bridges agent callbacks to WebSocket handlers
- Cognito + wallet dual identity (familiar login + blockchain features)
- Synchronous Textract (5MB limit, simpler for hackathon)
- Single FastAPI monolith with clean module separation
- Mock GSTN/CIBIL/MCA APIs (real APIs require government registration)

## Key Files

| Path | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry point, CORS, lifespan (planned) |
| `backend/app/config.py` | Settings from Secrets Manager + env vars (planned) |
| `backend/app/routers/` | API route handlers: auth, invoices, dashboard, collection, wallet, rules, websocket (planned) |
| `backend/app/agents/` | Strands agent definitions: invoice_agent, underwriting_agent, collection_agent, swarm (planned) |
| `backend/app/agents/tools/` | Tool implementations: extraction, validation, fraud, risk, gstn, cibil, mca, nft, collection (planned) |
| `backend/app/models/` | SQLAlchemy models: user, invoice, risk_assessment, underwriting, nft_record, alert (planned) |
| `backend/app/schemas/` | Pydantic request/response schemas (planned) |
| `backend/app/services/` | Business logic: invoice_service, textract_service, algorand_service (planned) |
| `contracts/invoice_nft/contract.py` | ARC4 smart contract in Algorand Python (planned) |
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
- **Key settings**: DATABASE_URL, REDIS_URL, AWS_REGION, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID, S3_BUCKET_NAME, ALGORAND_APP_WALLET_MNEMONIC
- **Environment variables override** all settings (12-factor app pattern)
- **Secrets**: Never in code. API keys and mnemonics in AWS Secrets Manager.
- **.env.example**: Template for local development (committed). `.env`: Actual values (gitignored).

## Project-Specific Rules

- Check `tasks/lessons.md` at session start. Update it after any correction.
- All 3 agents use Strands Agents SDK with `@tool` decorator pattern -- never raw Bedrock API calls
- Mock services (GSTN, CIBIL, MCA) use deterministic rules based on GSTIN prefix -- document the rules in code comments
- Agent reasoning traces must be persisted to `agent_traces` table AND streamed via WebSocket -- never skip either
- Invoice processing is always async (background task) -- the API returns immediately with invoice_id + ws_url
- NFT minting uses the application wallet, NOT the user's connected wallet
- All API endpoints require Cognito JWT except health checks
- Redis is used for: WebSocket pub/sub, session cache, rate limiting, GSTN cache (24h TTL)
- PostgreSQL JSONB columns for: line_items, extracted_data, fraud_flags, buyer_intel, rules_snapshot, custom_rules
- File uploads go directly to S3, never stored on the server filesystem
- Algorand operations target TESTNET only -- never mainnet
- Frontend is statically exported (next export) and served via S3 + CloudFront

## Deployment

- **Strategy**: Per-milestone (3 deployments: Day 8, Day 13, Day 16)
- **Backend**: Docker image -> ECR -> ECS Fargate (0.5 vCPU, 1GB RAM, 2 tasks)
- **Frontend**: next export -> S3 bucket -> CloudFront distribution
- **Database**: RDS PostgreSQL (db.t3.micro, Free Tier)
- **Cache**: ElastiCache Redis (cache.t3.micro)
- **CI/CD**: GitHub Actions -- lint, test, build, deploy on push to main
- **Environments**: Local (Docker Compose) + AWS (staging = production for hackathon)

## Known Gotchas

(Empty for new project -- populated during development. Check tasks/lessons.md for runtime discoveries.)
