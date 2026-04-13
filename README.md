# ChainFactor AI

> AI-powered invoice financing for Indian SMEs on the Algorand blockchain.

[![AlgoBharat Hack Series 3.0](https://img.shields.io/badge/Hackathon-AlgoBharat%203.0-blue)]()
[![Algorand](https://img.shields.io/badge/Blockchain-Algorand%20Testnet-black)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

## The Problem

India's 63 million SMEs have **~$100 billion locked in unpaid invoices** with 45-90 day payment cycles. Existing invoice financing solutions take 48-72 hours and charge 18-24% rates, leaving most SMEs underserved.

## The Solution

ChainFactor AI processes invoices **end-to-end in under 2 minutes** using a multi-agent AI system on the Algorand blockchain:

1. **Connect** your Algorand wallet (Pera / Defly)
2. **Upload** an invoice PDF
3. **Watch AI agents** process it in real-time (14 steps across 2 agents)
4. **Receive** a verified invoice NFT (ARC-69) on Algorand testnet

### What Happens Under the Hood

```
Invoice PDF
    |
    v
[Invoice Processing Agent - Sonnet 4.6]
    |-- Extract data (Textract + Claude vision)
    |-- Validate 23 fields
    |-- Check GST compliance (HSN codes, rates, e-invoice)
    |-- 5-layer fraud detection
    |-- Verify GSTIN
    |-- Buyer payment intelligence
    |-- CIBIL + MCA credit scores
    |-- Multi-signal risk scoring
    |-- Generate AI explanation
    |
    v  (Agent Handoff)
    |
[Underwriting Agent - Sonnet 4.6]
    |-- Cross-validate all outputs
    |-- Match seller auto-approve rules
    |-- Autonomous decision (approve / reject / flag)
    |
    v
[Mint ARC-69 NFT on Algorand Testnet]
    |
    v
User claims NFT to their wallet
```

## Key Features

- **Agentic AI Processing** -- 3-agent system (Strands Agents SDK + Swarm) with 14 AI touchpoints
- **5-Layer Fraud Detection** -- Document integrity, financial consistency, pattern analysis, entity verification, cross-reference
- **GST Compliance** -- HSN code validation, rate matching, e-invoice verification
- **Real-Time Streaming** -- Watch each AI step complete via WebSocket with live updates
- **Blockchain Verification** -- Every approved invoice minted as an ARC-69 NFT on Algorand testnet
- **Auto-Approve Rules** -- Sellers define custom conditions for automatic approval
- **Natural Language Query** -- Ask questions about your invoices in plain English
- **Full Audit Trail** -- Complete agent reasoning chain for every decision

## Architecture

```
                    ┌──────────────────────┐
                    │   Next.js 14 (S3 +   │
                    │    CloudFront CDN)    │
                    └──────────┬───────────┘
                               │
                    ┌──────────v───────────┐
                    │    ALB (WebSocket +   │
                    │      HTTP routing)    │
                    └──────────┬───────────┘
                               │
                    ┌──────────v───────────┐
                    │  FastAPI on ECS      │
                    │  Fargate (Modular    │
                    │  Monolith)           │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │ Strands Swarm  │  │
                    │  │ (2 AI Agents)  │  │
                    │  └───────┬────────┘  │
                    └──────────┼───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────v──┐   ┌────────v───┐   ┌────────v───┐
    │ PostgreSQL │   │   Redis    │   │    S3      │
    │ (RDS)      │   │(ElastiCache│   │ (Invoices) │
    └────────────┘   └────────────┘   └────────────┘

    External: Bedrock (us-east-1) | Textract | Cognito | Algorand Testnet
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), TailwindCSS, TypeScript |
| **Wallet** | @txnlab/use-wallet-react (Pera + Defly) |
| **Auth** | AWS Cognito + SNS (OTP) |
| **Backend** | FastAPI, Python 3.11+, Uvicorn |
| **AI Agents** | Strands Agents SDK + Swarm (Bedrock-native) |
| **AI Models** | Sonnet 4.6 (processing + underwriting), Haiku 4.5 (tools), Opus 4.6 (NL query) |
| **OCR** | Amazon Textract (primary), Claude vision (fallback) |
| **Blockchain** | Algorand Python (algopy), py-algorand-sdk, ARC-69 NFTs |
| **Database** | PostgreSQL 15 (RDS), SQLAlchemy + Alembic |
| **Cache** | Redis 7 (ElastiCache) |
| **Storage** | AWS S3 |
| **IaC** | Terraform (enterprise-grade, 11 reusable modules) |
| **CI/CD** | GitHub Actions |
| **Region** | ap-south-1 (Mumbai) -- all services; us-east-1 -- Bedrock only |

## Project Structure

```
chainfactor-ai/
├── backend/                    # FastAPI modular monolith
│   ├── app/
│   │   ├── main.py            # App entry point, CORS, health check
│   │   ├── config.py          # pydantic-settings (env vars)
│   │   ├── database.py        # Async SQLAlchemy engine
│   │   ├── models/            # SQLAlchemy models (6 tables)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── api/v1/            # Versioned API router
│   │   ├── modules/           # Feature modules (auth, invoices, agents, blockchain, dashboard, rules)
│   │   └── agents/            # Strands agents + 11 AI tools
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest test suite
│   ├── Dockerfile             # Multi-stage build (builder -> runtime)
│   └── requirements.txt       # Pinned Python dependencies
├── frontend/                   # Next.js 14 App Router
│   ├── src/
│   │   ├── app/               # Pages (auth, dashboard, invoices, rules)
│   │   ├── components/        # React components (providers, navbar, NFTCard, AIPanel)
│   │   ├── hooks/             # Custom hooks (useAuth, useProcessing, useInvoiceId)
│   │   └── lib/               # API client, constants
│   ├── Dockerfile             # Multi-stage build (deps -> dev -> production)
│   └── package.json
├── contracts/                  # Algorand smart contracts (ARC4 + ARC-69)
│   └── invoice_nft/           # 7 ABI methods, fully implemented
├── infra/
│   ├── docker-compose.yml     # Local dev: PostgreSQL + Redis + backend + frontend
│   └── terraform/             # Enterprise IaC
│       ├── backends/bootstrap/ # S3 state bucket + DynamoDB lock table
│       ├── environments/staging/
│       ├── modules/            # 11 reusable modules
│       └── shared/
└── tasks/                      # Project management
    ├── project-plan.md        # Master plan (42 features, 8 epics, 3 milestones)
    ├── wireframes.md          # ASCII wireframes + full API contracts
    ├── architecture-raw.md    # Full architecture document
    └── lessons.md             # Lessons learned
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- AWS CLI (configured with credentials)
- AlgoKit 2.x (for smart contract development)

### Local Development

```bash
# 1. Clone the repo
git clone https://github.com/Manoj-777/chainfactor-ai.git
cd chainfactor-ai

# 2. Start infrastructure (PostgreSQL + Redis + backend + frontend)
cd infra && docker compose up -d

# -- OR run services individually --

# 3a. Backend
cd backend
cp .env.example .env          # Fill in your values
pip install -r requirements.txt
python -m alembic upgrade head # Run database migrations
uvicorn app.main:app --reload  # http://localhost:8000

# 3b. Frontend
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login with phone/email |
| POST | `/api/v1/auth/verify-otp` | Verify OTP code |
| POST | `/api/v1/wallet/link` | Link Algorand wallet |
| POST | `/api/v1/invoices/upload` | Upload invoice PDF |
| GET | `/api/v1/invoices` | List user's invoices |
| GET | `/api/v1/invoices/{id}` | Invoice detail with AI analysis |
| GET | `/api/v1/invoices/{id}/stream` | SSE stream of processing steps |
| POST | `/api/v1/invoices/{id}/nft/opt-in` | Opt-in to ASA |
| POST | `/api/v1/invoices/{id}/nft/claim` | Claim NFT transfer |
| GET | `/api/v1/invoices/{id}/audit-trail` | Full agent reasoning chain |
| GET | `/api/v1/dashboard/summary` | Dashboard statistics |
| POST | `/api/v1/dashboard/nl-query` | Natural language query |
| GET | `/api/v1/rules` | List auto-approve rules |
| POST | `/api/v1/rules` | Create new rule |
| GET | `/api/v1/verify/nft/{asset_id}` | Public NFT verification (no auth) |
| GET | `/api/v1/settings/ai-config` | AI agent configuration |

## Database Schema

```
users ──< invoices ──< agent_traces
  |           |
  |           └── nft_records (1:1)
  |
  ├──< rules
  └── user_settings (1:1)
```

6 tables with UUID primary keys, JSONB columns for AI pipeline results, and full audit trail support.

## Infrastructure

Enterprise-grade Terraform with 11 reusable modules:

| Module | Resources |
|--------|-----------|
| networking | VPC, subnets, NAT Gateway, route tables |
| compute | ECS Fargate cluster, task definition, service, auto-scaling |
| database | RDS PostgreSQL (db.t3.micro, Free Tier) |
| cache | ElastiCache Redis (cache.t3.micro) |
| storage | S3 buckets (invoices + frontend static) |
| cdn | CloudFront distribution with OAC |
| load_balancer | ALB with 4000s WebSocket timeout |
| auth | Cognito User Pool + App Client |
| secrets | Secrets Manager (DB password, Algorand mnemonic, app config) |
| iam | Least-privilege ECS task roles |
| monitoring | CloudWatch alarms (CPU, memory) |

```bash
# One-time: Bootstrap remote state
cd infra/terraform/backends/bootstrap
terraform init && terraform apply

# Deploy staging
cd infra/terraform/environments/staging
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Demo Mode

When no `S3_BUCKET_NAME` is configured, the backend automatically uses the demo pipeline. Returns pre-computed results for **4 test invoices** with realistic data and simulated processing delays:

| Invoice | Status | Risk Score | Scenario |
|---------|--------|-----------|----------|
| INV-2026-001 | Approved | 82 (Low) | Clean invoice, auto-approved |
| INV-2026-002 | Flagged | 45 (Medium) | Buyer GSTIN inactive |
| INV-2026-003 | Minted | 91 (Low) | Excellent profile, NFT minted |
| INV-2026-004 | Rejected | 12 (High) | Fraud signals detected |

Demo login: `demo@chainfactor.ai` / `Demo@1234`

**Live deployment**: https://d20nrao7c3w07a.cloudfront.net

## Team

| Name | Role |
|------|------|
| **Sanjay M** | Frontend Lead |
| **Manoj RS** | Backend + AI + DevOps |
| **Abhishek Reddy** | Testing Support |
| **Jeevidha** | Smart Contract Support |

## Hackathon

**AlgoBharat Hack Series 3.0** -- Future of Finance + Agentic Commerce track

Built to demonstrate how agentic AI + blockchain can transform invoice financing for Indian SMEs, reducing processing time from 48-72 hours to under 2 minutes while providing full transparency through on-chain verification.

## License

MIT
