This is a greenfield project. The workspace is empty aside from a placeholder database file. I will now produce the full architecture document.

---

# ChainFactor AI -- System Architecture Document

**Version**: 1.0
**Date**: 2026-03-17
**Project**: AlgoBharat Hack Series 3.0 -- AI-Powered Invoice Financing on Algorand
**Team**: 4 members (1 frontend dev, 1 backend+AI dev, 2 supporting)
**Deadline**: April 2, 2026
**Budget**: $200

---

## 1. Component Diagram

The system is organized into six major layers. Each component has a single, well-defined responsibility.

```
+===========================================================================+
|                          CLIENT LAYER                                      |
|                                                                            |
|  +---------------------+    +---------------------+   +----------------+   |
|  |  Next.js 14 App     |    |  @txnlab/use-wallet |   | use-wallet-ui  |   |
|  |  (App Router)       |    |  -react             |   | (Pera/Defly)   |   |
|  |  TailwindCSS        |    |  Wallet Context      |   | Connect Modal  |   |
|  +----------+----------+    +----------+----------+   +-------+--------+   |
|             |                          |                      |            |
|             +-------+------------------+----------------------+            |
|                     |                                                      |
|          +----------v-----------+                                          |
|          |  WebSocket Client    |  (real-time agent reasoning trace)       |
|          +----------+-----------+                                          |
+===========================================================================+
              |  HTTPS / WSS
              v
+===========================================================================+
|                        EDGE / CDN LAYER                                    |
|                                                                            |
|  +------------------------------+    +-------------------------------+     |
|  |  CloudFront Distribution     |    |  API Gateway (HTTP + WS)     |     |
|  |  (static assets from S3)     |    |  Cognito Authorizer          |     |
|  +------------------------------+    +-------------------------------+     |
+===========================================================================+
              |
              v
+===========================================================================+
|                       APPLICATION LAYER (ECS Fargate)                       |
|                                                                            |
|  +-----------------------------------------------------------------------+ |
|  |                      FastAPI Application                              | |
|  |                                                                       | |
|  |  +------------------+  +------------------+  +---------------------+  | |
|  |  |  Auth Router     |  |  Invoice Router  |  |  Dashboard Router  |  | |
|  |  |  /auth/*         |  |  /invoices/*     |  |  /dashboard/*      |  | |
|  |  +------------------+  +------------------+  +---------------------+  | |
|  |                                                                       | |
|  |  +------------------+  +------------------+  +---------------------+  | |
|  |  |  Wallet Router   |  |  Agent Router    |  |  Collection Router |  | |
|  |  |  /wallet/*       |  |  /agents/*       |  |  /collection/*     |  | |
|  |  +------------------+  +------------------+  +---------------------+  | |
|  |                                                                       | |
|  |  +------------------+  +------------------+                           | |
|  |  |  WebSocket Mgr   |  |  Background Task |                          | |
|  |  |  /ws/processing  |  |  Queue (asyncio) |                          | |
|  |  +------------------+  +------------------+                           | |
|  +-----------------------------------------------------------------------+ |
+===========================================================================+
              |
              v
+===========================================================================+
|                         AGENT LAYER (Strands Swarm)                        |
|                                                                            |
|  +--------------------+  +--------------------+  +--------------------+    |
|  | Invoice Processing |  | Underwriting Agent |  | Collection Agent  |    |
|  | Agent              |  |                    |  |                    |    |
|  | (Sonnet 4.6)       |  | (Sonnet 4.6)      |  | (Sonnet 4.6)      |    |
|  |                    |  |                    |  |                    |    |
|  | Tools:             |  | Tools:             |  | Tools:            |    |
|  | - extract_invoice  |  | - get_seller_rules |  | - get_overdue     |    |
|  | - validate_fields  |  | - get_invoice_data |  | - get_buyer_hist  |    |
|  | - check_fraud      |  | - approve_invoice  |  | - gen_reminder    |    |
|  | - verify_gstn      |  | - flag_for_review  |  | - suggest_escal   |    |
|  | - get_buyer_intel  |  | - log_decision     |  | - scan_portfolio  |    |
|  | - calculate_risk   |  |                    |  |                    |    |
|  | - generate_summary |  |                    |  |                    |    |
|  | - mint_nft         |  |                    |  |                    |    |
|  +--------------------+  +--------------------+  +--------------------+    |
|                                                                            |
|  Swarm Orchestrator: handoff(invoice_agent -> underwriting_agent)          |
|                      handoff(underwriting_agent -> collection_agent)       |
+===========================================================================+
              |
              v
+===========================================================================+
|                       DATA & STORAGE LAYER                                 |
|                                                                            |
|  +----------------+  +----------------+  +----------------+                |
|  | PostgreSQL     |  | Redis          |  | S3             |                |
|  | (RDS Free Tier)|  | (ElastiCache)  |  | (Documents)    |                |
|  |                |  |                |  |                |                |
|  | - Users        |  | - Sessions     |  | - Invoice PDFs |                |
|  | - Invoices     |  | - Rate limits  |  | - Extracted    |                |
|  | - Risk scores  |  | - Agent state  |  |   JSON results |                |
|  | - Decisions    |  | - WS channels  |  | - NFT metadata |                |
|  | - NFT records  |  |                |  |                |                |
|  +----------------+  +----------------+  +----------------+                |
+===========================================================================+
              |
              v
+===========================================================================+
|                    EXTERNAL SERVICES LAYER                                  |
|                                                                            |
|  +----------------+  +----------------+  +----------------+                |
|  | Amazon Textract|  | Amazon Bedrock |  | Algorand       |                |
|  | (OCR)          |  | (Claude 4.6)   |  | (Testnet)      |                |
|  +----------------+  +----------------+  +----------------+                |
|                                                                            |
|  +----------------+  +----------------+  +----------------+                |
|  | AWS Cognito    |  | AWS SNS        |  | GSTN API       |                |
|  | (Auth)         |  | (OTP)          |  | (Verification) |                |
|  +----------------+  +----------------+  +----------------+                |
+===========================================================================+
```

---

## 2. Data Flow

### 2.1 Invoice Processing Flow (Primary Happy Path)

```
User                Frontend              Backend (FastAPI)          Agents (Strands)           External
  |                    |                       |                          |                        |
  |--Connect Wallet--->|                       |                          |                        |
  |<--Wallet Addr------|                       |                          |                        |
  |                    |                       |                          |                        |
  |--Login (Cognito)-->|---Cognito Auth------->|                          |                        |
  |<--JWT Token--------|<--JWT + Refresh-------|                          |                        |
  |                    |                       |                          |                        |
  |--Upload Invoice--->|---POST /invoices----->|                          |                        |
  |                    |  (multipart + JWT)     |                          |                        |
  |                    |                       |--Upload to S3----------->|                     S3 |
  |                    |                       |<--S3 key + presigned-----|                        |
  |                    |                       |                          |                        |
  |                    |<--invoice_id + 202----|                          |                        |
  |                    |                       |                          |                        |
  |--Open WS---------->|===WSS /ws/process/{id}|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |--Start Invoice Agent---->|                        |
  |                    |                       |                          |                        |
  |                    |                       |                          |--Textract(S3 key)-->Textract
  |                    |                       |                          |<--Extracted fields--|   |
  |                    |                       |<--STEP: "Extracting..."--|                        |
  |<--WS: step event---|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |                          |--validate_fields()     |
  |                    |                       |<--STEP: "Validating..."--|                        |
  |<--WS: step event---|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |                          |--verify_gstn()-------->GSTN
  |                    |                       |                          |<--GST status-----------|
  |                    |                       |<--STEP: "GSTN verified"--|                        |
  |<--WS: step event---|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |                          |--check_fraud(DB)       |
  |                    |                       |                          |--get_buyer_intel()     |
  |                    |                       |                          |--calculate_risk()      |
  |                    |                       |<--STEP: risk_score=72---|                        |
  |<--WS: step event---|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |          SWARM HANDOFF: Invoice -> Underwriting   |
  |                    |                       |                          |                        |
  |                    |                       |                          |--get_seller_rules()    |
  |                    |                       |                          |--approve_invoice()     |
  |                    |                       |<--STEP: "Approved"-------|                        |
  |<--WS: step event---|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |                          |--generate_summary()    |
  |                    |                       |                          |--mint_nft()----------->Algorand
  |                    |                       |                          |<--NFT asset ID---------|
  |                    |                       |<--STEP: "NFT minted"----|                        |
  |<--WS: step event---|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |                    |                       |--Persist all to DB------>|                     RDS|
  |                    |                       |<--DONE: final result-----|                        |
  |<--WS: complete-----|<=====================|                          |                        |
  |                    |                       |                          |                        |
  |--GET /invoices/{id}|---GET + JWT---------->|--Query DB-------------->|                        |
  |<--Full invoice data|<--JSON response-------|<--Invoice record---------|                        |
```

### 2.2 Data Storage Strategy

| Data Type | Primary Store | Cache | Rationale |
|-----------|--------------|-------|-----------|
| User profiles | PostgreSQL | Redis (session) | Relational, auth-linked |
| Invoice metadata | PostgreSQL | Redis (hot invoices) | Queryable, joins with users |
| Invoice documents (PDF/image) | S3 | CloudFront | Binary, large, infrequent read |
| Textract raw output | S3 (JSON) | None | Audit trail, large payload |
| Extracted structured data | PostgreSQL (JSONB) | None | Queryable fields |
| Risk scores + AI explanations | PostgreSQL | None | Historical, reportable |
| Agent reasoning traces | PostgreSQL (JSONB) | Redis (during processing) | Replay, audit |
| NFT records | PostgreSQL + Algorand | None | Blockchain is source of truth |
| WebSocket channel state | Redis | N/A | Ephemeral, pub/sub |
| Seller underwriting rules | PostgreSQL | Redis | Frequently read, rarely written |

---

## 3. API Design

### 3.1 REST Endpoints

All endpoints require `Authorization: Bearer <cognito_jwt>` unless marked public.

#### Authentication

```
POST   /api/v1/auth/register          -- Register with phone/email + wallet
POST   /api/v1/auth/verify-otp        -- Verify SNS OTP
POST   /api/v1/auth/login             -- Cognito-based login
POST   /api/v1/auth/refresh           -- Refresh JWT tokens
POST   /api/v1/auth/link-wallet       -- Link Algorand wallet to Cognito user
GET    /api/v1/auth/me                -- Current user profile
```

#### Invoices

```
POST   /api/v1/invoices               -- Upload invoice (multipart/form-data)
  Body: { file: binary, wallet_address: string }
  Response: { invoice_id: uuid, status: "queued", ws_url: "/ws/processing/{id}" }

GET    /api/v1/invoices                -- List invoices (paginated)
  Query: ?page=1&limit=20&status=approved&sort=-created_at
  Response: { data: Invoice[], meta: { total, page, limit } }

GET    /api/v1/invoices/{id}           -- Get invoice detail
  Response: { data: InvoiceDetail }

GET    /api/v1/invoices/{id}/trace     -- Get agent reasoning trace
  Response: { data: AgentTrace[] }

POST   /api/v1/invoices/{id}/retry     -- Retry failed processing
  Response: { status: "queued" }
```

#### Dashboard

```
GET    /api/v1/dashboard/summary       -- Portfolio summary
  Response: { total_invoices, total_value, approved_count, risk_distribution, ... }

GET    /api/v1/dashboard/alerts        -- Proactive portfolio alerts
  Response: { data: Alert[] }
```

#### Underwriting Rules

```
GET    /api/v1/rules                   -- Get seller's auto-approve rules
PUT    /api/v1/rules                   -- Update auto-approve rules
  Body: { max_amount: number, min_risk_score: number, allowed_buyers: string[], ... }
```

#### Collection

```
GET    /api/v1/collection/overdue      -- Overdue invoices
POST   /api/v1/collection/{id}/remind  -- Trigger AI reminder generation
GET    /api/v1/collection/{id}/history -- Collection action history
```

#### Wallet

```
POST   /api/v1/wallet/verify           -- Verify wallet ownership (sign challenge)
  Body: { wallet_address: string, signed_message: string, challenge: string }

GET    /api/v1/wallet/nfts             -- List NFTs minted for user
GET    /api/v1/wallet/balance          -- Algorand testnet balance
```

#### Natural Language Query (stretch goal)

```
POST   /api/v1/query                   -- Natural language portfolio query
  Body: { question: "How many invoices were flagged this week?" }
  Response: { answer: string, data: any }
```

### 3.2 WebSocket Endpoint

```
WSS /ws/processing/{invoice_id}?token={jwt}
```

**Message Format (server to client)**:

```json
{
  "type": "step" | "error" | "complete",
  "agent": "invoice_processing" | "underwriting" | "collection",
  "tool": "extract_invoice" | "validate_fields" | ...,
  "status": "running" | "success" | "failed",
  "message": "Extracting invoice data from uploaded document...",
  "data": { ... },
  "timestamp": "2026-03-17T10:30:00Z",
  "step_number": 3,
  "total_steps_estimate": 8
}
```

**Message types**:
- `step` -- Agent is executing a tool. Sent each time a tool starts and completes.
- `error` -- A tool or agent failed. Includes error context and whether processing continues or aborts.
- `complete` -- All agents finished. Includes final invoice status, risk score, NFT info.

---

## 4. Agent Interaction Flow (Strands Swarm)

### 4.1 Swarm Architecture

Strands Swarm orchestrates the 3 agents via explicit handoffs. Each agent runs as a Strands Agent with a defined tool set and system prompt. The Swarm coordinator manages the conversation state and tool call routing.

```
                    +-------------------------+
                    |    Swarm Orchestrator    |
                    |    (strands.swarm)       |
                    +------------+------------+
                                 |
                    Receives: invoice_id, s3_key, user_id
                                 |
                    +------------v------------+
                    |  Invoice Processing     |
                    |  Agent                  |
                    |                         |
                    |  System Prompt:         |
                    |  "You are an invoice    |
                    |  processing specialist."|
                    |                         |
                    |  Tool execution order:  |
                    |  1. extract_invoice     |
                    |  2. validate_fields     |
                    |  3. verify_gstn         |
                    |  4. check_fraud         |
                    |  5. get_buyer_intel     |
                    |  6. calculate_risk      |
                    |  7. generate_summary    |
                    +------------+------------+
                                 |
                    handoff_to_underwriting()
                    passes: extracted_data, risk_score, fraud_flags
                                 |
                    +------------v------------+
                    |  Underwriting Agent     |
                    |                         |
                    |  System Prompt:         |
                    |  "You are a financing   |
                    |  underwriter."          |
                    |                         |
                    |  Tool execution order:  |
                    |  1. get_invoice_data    |
                    |  2. get_seller_rules    |
                    |  3. approve_invoice OR  |
                    |     flag_for_review     |
                    |  4. log_decision        |
                    +------------+------------+
                                 |
                    If approved: handoff back to Invoice Agent for mint_nft
                    If rejected: return result, no handoff
                                 |
                    +------------v------------+
                    |  mint_nft tool          |
                    |  (Invoice Agent)        |
                    |  - Build ARC4 txn       |
                    |  - Submit to Algorand   |
                    |  - Return asset ID      |
                    +-------------------------+
```

### 4.2 Strands Agent Configuration (Pseudocode)

```
Invoice Processing Agent:
  model: bedrock/anthropic.claude-sonnet-4-6-v1
  tools: [extract_invoice, validate_fields, check_fraud, verify_gstn,
          get_buyer_intel, calculate_risk, generate_summary, mint_nft]
  callback: on_tool_use -> push to WebSocket channel via Redis pub/sub

Underwriting Agent:
  model: bedrock/anthropic.claude-sonnet-4-6-v1
  tools: [get_seller_rules, get_invoice_data, approve_invoice,
          flag_for_review, log_decision]
  callback: on_tool_use -> push to WebSocket channel via Redis pub/sub

Collection Agent:
  model: bedrock/anthropic.claude-sonnet-4-6-v1
  tools: [get_overdue_invoices, get_buyer_history, generate_reminder,
          suggest_escalation, scan_portfolio]
  callback: on_tool_use -> push to WebSocket channel via Redis pub/sub

Swarm:
  agents: [invoice_agent, underwriting_agent, collection_agent]
  handoffs:
    invoice_agent -> underwriting_agent (when extraction + risk complete)
    underwriting_agent -> invoice_agent (when approved, for NFT minting)
  max_handoffs: 3
```

### 4.3 Callback Mechanism for Real-Time Streaming

Strands Agents SDK supports a callback/event handler pattern. Each time an agent invokes a tool or produces intermediate reasoning, a callback fires. The backend captures these callbacks and routes them to the WebSocket.

```
Agent Tool Call
    |
    v
Strands callback(event) fires
    |
    v
Backend formats event -> AgentStepMessage
    |
    v
Redis PUBLISH channel:invoice:{invoice_id}
    |
    v
FastAPI WebSocket handler subscribed to channel
    |
    v
WebSocket pushes message to connected client
```

This Redis pub/sub decoupling is necessary because the agent runs in a background asyncio task (or a separate thread), while the WebSocket handler runs in the FastAPI event loop. Redis bridges the two cleanly.

### 4.4 Collection Agent (Scheduled + On-Demand)

The Collection Agent operates differently from the other two:

- **Scheduled**: A CloudWatch Events rule triggers a Lambda (or ECS scheduled task) daily to invoke the Collection Agent with `scan_portfolio`. The agent identifies overdue invoices and generates proactive alerts stored in PostgreSQL.
- **On-demand**: When a user clicks "Send Reminder" in the dashboard, the `/collection/{id}/remind` endpoint invokes the Collection Agent for a specific invoice.

---

## 5. Database Schema

### 5.1 Entity-Relationship Overview

```
users 1---* invoices 1---1 risk_assessments
  |                   1---1 underwriting_decisions
  |                   1---1 nft_records
  |                   1---* agent_traces
  |                   1---* collection_actions
  |
  1---1 seller_rules
  1---* alerts
```

### 5.2 Table Definitions

```sql
-- Users table (linked to Cognito sub)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub     VARCHAR(128) UNIQUE NOT NULL,
    wallet_address  VARCHAR(58) UNIQUE,          -- Algorand address (58 chars)
    email           VARCHAR(255),
    phone           VARCHAR(20),
    company_name    VARCHAR(255),
    gstn            VARCHAR(15),                 -- 15-char GSTN
    role            VARCHAR(20) DEFAULT 'seller', -- seller | buyer | admin
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Invoices table
CREATE TABLE invoices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    status          VARCHAR(30) NOT NULL DEFAULT 'uploaded',
        -- uploaded | processing | extracted | validated | risk_scored |
        -- approved | rejected | flagged | nft_minted | funded | overdue | paid
    s3_key          VARCHAR(512) NOT NULL,       -- S3 path to original document
    s3_extracted    VARCHAR(512),                -- S3 path to Textract JSON output
    
    -- Extracted fields (denormalized for query performance)
    invoice_number  VARCHAR(100),
    invoice_date    DATE,
    due_date        DATE,
    seller_gstn     VARCHAR(15),
    buyer_gstn      VARCHAR(15),
    buyer_name      VARCHAR(255),
    total_amount    DECIMAL(15, 2),
    currency        VARCHAR(3) DEFAULT 'INR',
    line_items      JSONB,                       -- Array of {description, qty, rate, amount}
    
    -- AI-generated fields
    quality_score   SMALLINT,                    -- 0-100, document quality assessment
    extracted_data  JSONB,                       -- Full structured extraction
    validation_errors JSONB,                     -- Array of validation issues found
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoices_user_id ON invoices(user_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_buyer_gstn ON invoices(buyer_gstn);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);

-- Risk assessments (1:1 with invoice)
CREATE TABLE risk_assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID UNIQUE NOT NULL REFERENCES invoices(id),
    risk_score      SMALLINT NOT NULL,           -- 0-100 (higher = less risky)
    risk_grade      VARCHAR(1),                  -- A, B, C, D, F
    fraud_flags     JSONB,                       -- Array of fraud indicators
    buyer_intel     JSONB,                       -- Buyer intelligence brief
    ai_explanation  TEXT,                        -- Natural language risk explanation
    financing_rec   JSONB,                       -- {recommended: bool, rate: %, term: days, amount: decimal}
    invoice_summary TEXT,                        -- AI-generated summary for NFT metadata
    model_version   VARCHAR(50),                 -- Track which model version scored this
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Underwriting decisions (1:1 with invoice)
CREATE TABLE underwriting_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID UNIQUE NOT NULL REFERENCES invoices(id),
    decision        VARCHAR(20) NOT NULL,        -- approved | rejected | flagged_review
    auto_approved   BOOLEAN DEFAULT FALSE,       -- Was this auto-approved by rules?
    rules_snapshot  JSONB,                       -- Snapshot of rules at decision time
    reasoning       TEXT,                        -- Agent's reasoning for decision
    decided_at      TIMESTAMPTZ DEFAULT NOW()
);

-- NFT records (1:1 with invoice)
CREATE TABLE nft_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID UNIQUE NOT NULL REFERENCES invoices(id),
    asset_id        BIGINT NOT NULL,             -- Algorand ASA ID
    txn_id          VARCHAR(52) NOT NULL,        -- Algorand transaction ID
    creator_address VARCHAR(58) NOT NULL,
    metadata_hash   VARCHAR(64),                 -- SHA-256 of NFT metadata
    metadata_url    VARCHAR(512),                -- S3 URL to NFT metadata JSON
    algo_explorer_url VARCHAR(512),              -- Direct link to AlgoExplorer
    minted_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Agent reasoning traces
CREATE TABLE agent_traces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id),
    agent_name      VARCHAR(50) NOT NULL,        -- invoice_processing | underwriting | collection
    tool_name       VARCHAR(50) NOT NULL,
    step_number     SMALLINT NOT NULL,
    status          VARCHAR(20) NOT NULL,        -- started | success | failed
    input_summary   JSONB,                       -- Summarized tool input (no PII)
    output_summary  JSONB,                       -- Summarized tool output
    reasoning       TEXT,                        -- Agent reasoning text
    duration_ms     INTEGER,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_traces_invoice ON agent_traces(invoice_id);

-- Seller underwriting rules
CREATE TABLE seller_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id),
    max_invoice_amount  DECIMAL(15, 2),
    min_risk_score      SMALLINT,                -- Minimum acceptable risk score
    allowed_buyer_gstns JSONB,                   -- Array of GSTN strings, null = all
    max_days_overdue    SMALLINT,
    auto_approve_enabled BOOLEAN DEFAULT FALSE,
    custom_rules        JSONB,                   -- Extensible rules object
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Collection actions
CREATE TABLE collection_actions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id),
    action_type     VARCHAR(30) NOT NULL,        -- reminder_sent | escalated | paid_confirmed
    channel         VARCHAR(20),                 -- email | sms | whatsapp
    content         TEXT,                        -- Generated reminder text
    ai_suggestion   TEXT,                        -- Escalation suggestion from agent
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_collection_invoice ON collection_actions(invoice_id);

-- Portfolio alerts
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    alert_type      VARCHAR(30) NOT NULL,        -- overdue_risk | concentration_risk | payment_received
    severity        VARCHAR(10) NOT NULL,        -- info | warning | critical
    title           VARCHAR(255) NOT NULL,
    message         TEXT NOT NULL,
    related_invoice_id UUID REFERENCES invoices(id),
    read            BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_user ON alerts(user_id, read);
```

---

## 6. External Integrations

### 6.1 Integration Map

| Service | Purpose | Integration Method | Error Strategy |
|---------|---------|-------------------|----------------|
| **Amazon Textract** | OCR extraction from invoice PDF/image | `boto3` `analyze_document` (sync) or `start_document_analysis` (async) | Retry 2x with exponential backoff; fallback to Claude vision |
| **Amazon Bedrock** | Claude Sonnet 4.6 for agents | Strands SDK uses Bedrock natively | Retry 1x; if model unavailable, queue and retry in 30s |
| **Algorand Testnet** | NFT minting (ARC4 smart contract) | `algokit` + `algosdk` via AlgoNode API | Retry 2x; if network down, mark as `pending_mint` |
| **AWS Cognito** | User authentication, JWT issuance | Cognito User Pool + `python-jose` for JWT validation | Standard OAuth2 error handling |
| **AWS SNS** | OTP delivery (SMS) | `boto3` `publish` | Retry 1x; rate limit OTP requests to 1/min |
| **GSTN API** | GST number verification | HTTP GET to government API | Cache results 24h in Redis; timeout after 5s, proceed with warning |
| **AWS S3** | Document and metadata storage | `boto3` `upload_fileobj` / `get_object` | Retry with SDK defaults |
| **AWS Secrets Manager** | Runtime secret retrieval | `boto3` at startup; cached in memory | Fail startup if secrets unavailable |
| **CloudWatch** | Logging, metrics, alarms | `boto3` / structured logging to stdout (Fargate forwards) | Fire-and-forget for metrics |

### 6.2 Textract Integration Detail

```
Upload Flow:
1. Frontend sends file to backend via multipart POST
2. Backend uploads to S3 bucket: s3://chainfactor-invoices/{user_id}/{invoice_id}/original.pdf
3. Backend calls Textract AnalyzeDocument (sync for <5MB, async for larger)
4. Textract returns structured blocks (WORD, LINE, TABLE, KEY_VALUE_SET)
5. Backend stores raw Textract JSON to S3: .../textract_output.json
6. Invoice Processing Agent tool `extract_invoice` parses Textract output into structured fields
7. If Textract confidence < 70% on key fields, Claude vision fallback is invoked
```

### 6.3 Algorand Integration Detail

```
NFT Minting Flow:
1. Backend holds an application wallet (mnemonic in Secrets Manager)
2. Smart contract: ARC4-compliant Algorand Python contract for invoice NFTs
3. mint_nft tool:
   a. Build metadata JSON (invoice summary, risk score, hash of original doc)
   b. Upload metadata to S3 (or IPFS if time permits)
   c. Construct ASA creation transaction via AlgoKit
   d. Sign with application wallet (backend-side signing)
   e. Submit to Algorand Testnet via AlgoNode
   f. Return asset_id and txn_id
4. Frontend displays AlgoExplorer link: https://testnet.algoexplorer.io/asset/{asset_id}

Important: The user's wallet is NOT used for signing the mint transaction. The application
wallet mints the NFT and optionally opts-in the user's wallet to receive it. This avoids
requiring the user to sign blockchain transactions during processing, which would break
the real-time flow.
```

---

## 7. WebSocket Design

### 7.1 Connection Lifecycle

```
1. Client uploads invoice -> receives invoice_id
2. Client opens WSS connection:
   WSS /ws/processing/{invoice_id}?token={jwt}

3. Server validates JWT, checks invoice ownership
4. Server subscribes to Redis channel: "ws:invoice:{invoice_id}"
5. Agent processing runs in background task
6. Each agent tool callback publishes to Redis channel
7. WebSocket handler receives Redis messages, forwards to client
8. On completion, server sends "complete" message and closes gracefully
9. Client can reconnect if disconnected (replays missed events from DB)
```

### 7.2 FastAPI WebSocket Handler (Design)

```
WebSocket Manager:
  - Maintains dict of {invoice_id: set[WebSocket]} for fan-out
  - Uses Redis pub/sub for cross-process communication
  - Heartbeat every 30s to detect dead connections
  - Auto-cleanup on disconnect
  - JWT validation on connect (reject unauthorized)

Message Protocol:
  Server -> Client:
    { type, agent, tool, status, message, data, timestamp, step_number, total_steps_estimate }

  Client -> Server:
    { type: "ping" }          -- Keepalive
    { type: "cancel" }        -- Request cancellation (best-effort)

  Server -> Client (on cancel):
    { type: "cancelled", message: "Processing cancelled by user" }
```

### 7.3 Reconnection and Replay

If a client disconnects and reconnects:
1. Server checks `agent_traces` table for all events for that `invoice_id`
2. Sends all past events as a burst (with `replay: true` flag)
3. Then resumes live streaming from Redis pub/sub
4. Client UI can deduplicate by `step_number`

### 7.4 Alternative: API Gateway WebSocket

If ECS Fargate proves difficult for long-lived WebSocket connections (ALB idle timeout is 4000s max), an alternative is to use API Gateway WebSocket APIs:

- API Gateway manages connections
- Lambda or Fargate posts to connections via `@connections` API
- More scalable but adds complexity

For hackathon scope, direct WebSocket on Fargate behind ALB is sufficient with a 5-minute ALB idle timeout (invoice processing should complete within 2 minutes).

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
+--------+     +----------+     +---------+     +----------+
| Client | --> | Cognito  | --> | Backend | --> | Database |
+--------+     +----------+     +---------+     +----------+

1. User signs up with email/phone
2. Cognito sends OTP via SNS
3. User verifies OTP
4. Cognito issues JWT (access_token, id_token, refresh_token)
5. Frontend stores tokens in httpOnly secure cookie (NOT localStorage)
6. Every API request includes Authorization: Bearer <access_token>
7. Backend validates JWT against Cognito JWKS (cached)
8. Backend extracts cognito_sub and loads user from DB
```

### 8.2 Wallet-Identity Linking

```
1. User connects Pera/Defly wallet in frontend
2. Frontend sends wallet_address to POST /api/v1/wallet/verify
3. Backend generates a random challenge string, stores in Redis with 5min TTL
4. Frontend prompts user to sign the challenge with their wallet
5. User signs in Pera/Defly
6. Frontend sends {wallet_address, signed_message, challenge} to backend
7. Backend verifies signature using algosdk.verify_bytes
8. If valid: link wallet_address to user record in DB
9. One user -> one wallet (enforced by UNIQUE constraint)
```

### 8.3 API Protection Layers

| Layer | Mechanism | Implementation |
|-------|-----------|---------------|
| Transport | TLS 1.3 | CloudFront + ALB terminate TLS |
| Authentication | Cognito JWT | Middleware validates on every request |
| Authorization | Role-based | User can only access own invoices |
| Rate Limiting | Token bucket | Redis-based, 100 req/min per user |
| Input Validation | Pydantic models | All request bodies validated |
| File Upload | Type + size check | Accept only PDF/PNG/JPG, max 10MB |
| CORS | Strict origin | Only CloudFront domain allowed |
| SQL Injection | Parameterized queries | SQLAlchemy ORM, never raw string interpolation |
| XSS | CSP headers + sanitization | Next.js built-in + Content-Security-Policy |
| Secrets | Secrets Manager | No secrets in code, env vars, or Docker images |

### 8.4 Data Protection

- **At rest**: RDS encryption enabled (default on Free Tier), S3 server-side encryption (SSE-S3)
- **In transit**: TLS everywhere (HTTPS, WSS, database SSL connections)
- **PII handling**: GSTN, phone numbers, company names stored encrypted at application level (optional for hackathon, noted as production requirement)
- **Invoice documents**: S3 bucket is private, accessed only via pre-signed URLs (15-min expiry) or backend-side reads

---

## 9. Infrastructure Diagram

```
                                    INTERNET
                                       |
                            +----------v----------+
                            |    Route 53 (DNS)   |
                            +----------+----------+
                                       |
                        +--------------+--------------+
                        |                             |
              +---------v---------+         +---------v---------+
              |   CloudFront      |         |   API Gateway     |
              |   (Static Assets) |         |   (optional, or   |
              |                   |         |    ALB directly)   |
              +---------+---------+         +---------+---------+
                        |                             |
              +---------v---------+         +---------v---------+
              |   S3 Bucket       |         |   Application     |
              |   (Next.js build) |         |   Load Balancer   |
              +-------------------+         +---------+---------+
                                                      |
                                            +---------v---------+
                                            |   ECS Fargate     |
                                            |   Cluster         |
                                            |                   |
                                            | +---------------+ |
                                            | | FastAPI       | |
                                            | | Container     | |
                                            | | (2 tasks,     | |
                                            | |  0.5 vCPU,    | |
                                            | |  1GB RAM each)| |
                                            | +-------+-------+ |
                                            +---------+---------+
                                                      |
                    +---------------------------------+----------------------------+
                    |                    |                    |                    |
          +---------v------+   +---------v------+   +--------v-------+   +-------v--------+
          |   RDS          |   |  ElastiCache   |   |   S3 Bucket    |   |  Secrets       |
          |   PostgreSQL   |   |  Redis         |   |   (Documents)  |   |  Manager       |
          |   (db.t3.micro)|   |  (t3.micro)    |   |                |   |                |
          +----------------+   +----------------+   +----------------+   +----------------+

                    +----------------------------+----------------------------+
                    |                            |                            |
          +---------v------+           +---------v------+           +--------v-------+
          |   Amazon       |           |   Amazon       |           |   Algorand     |
          |   Textract     |           |   Bedrock      |           |   Testnet      |
          |                |           |   (Claude)     |           |   (AlgoNode)   |
          +----------------+           +----------------+           +----------------+

          +----------------+           +----------------+
          |   AWS Cognito  |           |   CloudWatch   |
          |   User Pool    |           |   (Logs +      |
          |   + SNS (OTP)  |           |    Metrics)    |
          +----------------+           +----------------+
```

### 9.1 Cost Estimation ($200 Budget)

| Service | Estimated Monthly Cost | Notes |
|---------|----------------------|-------|
| ECS Fargate (2 tasks, 0.5 vCPU, 1GB) | ~$30 | Spot instances if available |
| RDS PostgreSQL (db.t3.micro) | $0 | Free Tier (750 hrs/month) |
| ElastiCache Redis (cache.t3.micro) | ~$12 | Smallest instance |
| S3 | <$1 | Minimal storage for hackathon |
| CloudFront | $0 | Free Tier (1TB/month) |
| Cognito | $0 | Free Tier (50K MAU) |
| Textract | ~$5 | ~300 pages at $1.50/1000 |
| Bedrock (Claude Sonnet 4.6) | ~$80-120 | ~500 invoice processings, 3 agents each |
| Bedrock (Claude Haiku 4.5) | ~$5-10 | Lightweight tasks |
| SNS (SMS OTP) | ~$5 | Limited demo usage |
| Secrets Manager | ~$1 | 2-3 secrets |
| **Total** | **~$140-185** | Within $200 budget |

### 9.2 Cost Optimization

- Use Haiku 4.5 instead of Sonnet 4.6 for the Collection Agent (less critical reasoning needed)
- Cache GSTN verification results aggressively (24h in Redis)
- Use Textract sync API to avoid S3 event + SNS costs of async
- Minimal CloudWatch log retention (7 days)
- ElastiCache could be replaced with in-process caching (dict/TTLCache) for hackathon if budget is tight, saving ~$12

---

## 10. Architectural Risks and Decisions

### ADR-001: Backend-Side NFT Signing vs. User Wallet Signing

**Context**: NFT minting requires a transaction signature. Two options: (a) the backend application wallet signs, or (b) the user signs via their connected Pera/Defly wallet.

**Decision**: Backend application wallet signs the mint transaction.

**Consequences**:
- **Positive**: No user interaction required during processing, enabling fully automated real-time flow. Simpler UX. No need for WalletConnect transaction approval mid-stream.
- **Positive**: Processing can happen asynchronously even if the user closes the browser.
- **Negative**: The NFT is minted by the application, not the user. Requires a subsequent opt-in + asset transfer for the user to "own" the NFT.
- **Negative**: Application wallet holds testnet ALGO and must be funded.
- **Alternatives**: User-signed minting (more decentralized but breaks real-time flow); deferred minting after user approval (adds a step).

**Status**: Accepted

---

### ADR-002: Redis Pub/Sub for WebSocket Bridge vs. In-Process Queue

**Context**: Agent tool callbacks and WebSocket handlers run in different execution contexts (background task vs. ASGI event loop). Need a bridge.

**Decision**: Use Redis pub/sub to bridge agent callbacks to WebSocket handlers.

**Consequences**:
- **Positive**: Decoupled architecture. Works across multiple Fargate tasks (horizontal scaling).
- **Positive**: If WebSocket disconnects, events are still published and can be stored for replay.
- **Negative**: Adds Redis dependency for real-time features.
- **Negative**: Redis pub/sub is fire-and-forget; if no subscriber is listening, messages are lost (mitigated by also persisting to `agent_traces` table).
- **Alternatives**: In-process asyncio.Queue (simpler but single-process only); Server-Sent Events instead of WebSocket (simpler but one-directional).

**Status**: Accepted

---

### ADR-003: Strands Agents SDK with Bedrock vs. Direct Bedrock API

**Context**: Could invoke Claude on Bedrock directly via boto3, or use the Strands Agents SDK which provides tool management, conversation state, and the Swarm orchestrator.

**Decision**: Use Strands Agents SDK with Strands Swarm for multi-agent orchestration.

**Consequences**:
- **Positive**: Built-in tool dispatch, conversation management, and handoff protocol. Less boilerplate.
- **Positive**: Native Bedrock integration (no API key management for Claude).
- **Positive**: Swarm handles agent-to-agent context passing.
- **Negative**: Newer SDK; less community documentation and fewer examples.
- **Negative**: Vendor lock-in to AWS Bedrock (acceptable for AWS-centric hackathon).
- **Alternatives**: LangGraph (more mature but heavier); CrewAI (Python-native but less Bedrock integration); direct boto3 Bedrock calls (full control but more code).

**Status**: Accepted

---

### ADR-004: Cognito + Wallet Dual Identity vs. Wallet-Only Auth

**Context**: Could authenticate purely via Algorand wallet signature (Web3 native) or use traditional Cognito auth with wallet as a linked identity.

**Decision**: Cognito as primary auth with wallet linking.

**Consequences**:
- **Positive**: Familiar phone/email login for Indian SME users who may not understand wallet-based auth.
- **Positive**: Cognito provides JWT, MFA, account recovery out of the box.
- **Positive**: Wallet is optional for viewing but required for NFT features.
- **Negative**: Two identity systems to maintain (Cognito sub + wallet address).
- **Negative**: Users must connect wallet separately after login.
- **Alternatives**: Wallet-only auth (pure Web3, but poor UX for target market); combined auth where wallet sign-in creates a Cognito identity (complex to implement).

**Status**: Accepted

---

### ADR-005: Synchronous Textract vs. Asynchronous Textract

**Context**: Textract offers sync (`AnalyzeDocument`) for documents under 5MB and async (`StartDocumentAnalysis` + polling/SNS notification) for larger documents.

**Decision**: Use synchronous Textract for the hackathon. Documents over 5MB are rejected with an error message asking the user to compress.

**Consequences**:
- **Positive**: Dramatically simpler implementation. No need for SNS topics, Lambda handlers, or polling.
- **Positive**: Faster response time (no queue delay).
- **Negative**: 5MB limit. Some scanned invoices may exceed this.
- **Negative**: Textract sync has a 10-second timeout; complex documents may fail.
- **Alternatives**: Async Textract with SNS notification (production-ready but more infra); pre-processing to compress/resize before Textract (adds a step).

**Status**: Accepted

---

### ADR-006: Monolith FastAPI vs. Microservices

**Context**: Could split the backend into separate services (invoice service, agent service, collection service) or keep everything in one FastAPI application.

**Decision**: Single FastAPI monolith with clean module separation.

**Consequences**:
- **Positive**: Single deployment, single container, simple debugging. Ideal for hackathon pace.
- **Positive**: No inter-service communication overhead or service mesh complexity.
- **Positive**: Shared database connection pool, shared Redis connection.
- **Negative**: Horizontal scaling scales everything together (cannot scale agents independently).
- **Negative**: Single point of failure.
- **Alternatives**: Microservices (production pattern but overkill for hackathon); Lambda functions per agent (serverless but cold start issues with large SDKs).

**Status**: Accepted

---

### 10.1 Key Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Bedrock Claude latency spikes | Medium | High | Set 60s timeout per agent; retry once; show "processing" UX |
| Textract fails on low-quality scans | High | Medium | Claude vision fallback; quality score threshold warning |
| Algorand Testnet instability | Low | Medium | Retry 3x; deferred minting queue; show "pending" status |
| Budget overrun on Bedrock calls | Medium | High | Haiku 4.5 for Collection Agent; prompt caching; token limits per request |
| Strands SDK bugs (newer library) | Medium | Medium | Pin exact version; have fallback plan to direct Bedrock calls for critical path |
| WebSocket connection drops on mobile | High | Low | Reconnection with replay; polling fallback endpoint |
| ECS Fargate cold start | Medium | Low | Keep minimum 1 task running; health check endpoint |

### 10.2 Scalability Boundaries (Post-Hackathon)

The architecture as designed handles approximately:
- **50 concurrent users**: Fargate 2-task setup
- **200 invoices/day**: Textract and Bedrock rate limits
- **500 WebSocket connections**: ALB + Redis pub/sub

To scale beyond hackathon:
1. Move agents to dedicated ECS service (separate scaling)
2. Add SQS queue between upload and processing (decouple)
3. Switch to async Textract with SNS
4. Add read replicas for PostgreSQL
5. Move to API Gateway WebSocket for connection management
6. Add CDN caching for dashboard API responses

---

## 11. Project Structure (Recommended)

```
chainfactor-ai/
├── frontend/                        # Next.js 14 App
│   ├── src/
│   │   ├── app/                     # App Router pages
│   │   │   ├── (auth)/              # Login, register
│   │   │   ├── dashboard/           # Portfolio dashboard
│   │   │   ├── invoices/            # Invoice upload, detail
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── wallet/              # Wallet connect, status
│   │   │   ├── invoice/             # Upload form, processing view
│   │   │   ├── dashboard/           # Charts, alerts, tables
│   │   │   └── ui/                  # Shared UI components
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts      # WebSocket connection + reconnect
│   │   │   ├── useInvoiceProcessing.ts
│   │   │   └── useAuth.ts
│   │   ├── lib/
│   │   │   ├── api.ts               # API client (fetch wrapper)
│   │   │   ├── auth.ts              # Cognito helpers
│   │   │   └── wallet.ts            # Algorand wallet utilities
│   │   └── types/
│   │       └── index.ts             # Shared TypeScript types
│   ├── public/
│   ├── next.config.js
│   └── package.json
│
├── backend/                         # FastAPI Application
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, lifespan
│   │   ├── config.py                # Settings from Secrets Manager + env
│   │   ├── dependencies.py          # Dependency injection (DB, Redis, etc.)
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── invoices.py
│   │   │   ├── dashboard.py
│   │   │   ├── collection.py
│   │   │   ├── wallet.py
│   │   │   ├── rules.py
│   │   │   └── websocket.py
│   │   │
│   │   ├── services/                # Business logic
│   │   │   ├── invoice_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── wallet_service.py
│   │   │   ├── textract_service.py
│   │   │   ├── algorand_service.py
│   │   │   └── collection_service.py
│   │   │
│   │   ├── agents/                  # Strands Agents
│   │   │   ├── invoice_agent.py     # Agent definition + tools
│   │   │   ├── underwriting_agent.py
│   │   │   ├── collection_agent.py
│   │   │   ├── swarm.py             # Swarm orchestrator setup
│   │   │   └── tools/               # Tool implementations
│   │   │       ├── extraction.py
│   │   │       ├── validation.py
│   │   │       ├── fraud.py
│   │   │       ├── risk.py
│   │   │       ├── gstn.py
│   │   │       ├── nft.py
│   │   │       └── collection.py
│   │   │
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── invoice.py
│   │   │   ├── risk_assessment.py
│   │   │   ├── underwriting.py
│   │   │   ├── nft_record.py
│   │   │   └── alert.py
│   │   │
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── invoice.py
│   │   │   ├── auth.py
│   │   │   ├── dashboard.py
│   │   │   └── websocket.py
│   │   │
│   │   ├── middleware/
│   │   │   ├── auth.py              # JWT validation middleware
│   │   │   └── rate_limit.py        # Redis-based rate limiter
│   │   │
│   │   └── utils/
│   │       ├── s3.py
│   │       ├── redis.py
│   │       └── algorand.py
│   │
│   ├── alembic/                     # Database migrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── contracts/                       # Algorand Smart Contracts
│   ├── invoice_nft/
│   │   ├── contract.py              # ARC4 contract in Algorand Python
│   │   └── deploy.py               # AlgoKit deployment script
│   └── algokit.toml
│
├── infra/                           # Infrastructure
│   ├── docker-compose.yml           # Local dev (Postgres, Redis, LocalStack)
│   ├── ecs-task-definition.json
│   └── cloudformation/              # Or Terraform
│       ├── vpc.yml
│       ├── ecs.yml
│       ├── rds.yml
│       └── cognito.yml
│
├── .github/
│   └── workflows/
│       ├── ci.yml                   # Lint, test, build
│       └── deploy.yml               # Deploy to AWS
│
├── tasks/                           # Task tracking
│   ├── todo.md
│   └── lessons.md
│
├── CLAUDE.md                        # Project-level Claude instructions
└── README.md
```

---

## 12. Implementation Priority (2-Week Sprint)

Given the April 2 deadline (~16 days from now), here is the recommended build order:

### Week 1: Core Pipeline (March 17-23)

| Day | Backend Dev | Frontend Dev |
|-----|------------|-------------|
| 1-2 | Project scaffolding, Docker compose, RDS setup, Cognito config | Next.js setup, TailwindCSS, wallet integration, auth flow |
| 3-4 | Invoice upload endpoint, S3 integration, Textract service | Invoice upload UI, file validation, auth-protected routes |
| 5-6 | Invoice Processing Agent (Strands), all 7 tools, WebSocket handler | WebSocket client, real-time processing view with step display |
| 7 | Underwriting Agent, handoff from Invoice Agent, auto-approve rules | Dashboard skeleton, invoice list, status display |

### Week 2: Complete + Polish (March 24-30)

| Day | Backend Dev | Frontend Dev |
|-----|------------|-------------|
| 8-9 | NFT minting (Algorand contract + AlgoKit deploy + mint_nft tool) | NFT display, AlgoExplorer links, underwriting rules UI |
| 10-11 | Collection Agent, scheduled scan, portfolio alerts | Collection dashboard, alerts panel, reminder trigger UI |
| 12-13 | End-to-end testing, error handling hardening, rate limiting | Polish UI, loading states, error states, mobile responsive |
| 14 | Deploy to AWS, CI/CD pipeline, demo data seeding | Final integration testing, demo walkthrough prep |

### Buffer (March 31 - April 1)
- Bug fixes
- Demo rehearsal
- Documentation
- Video recording if required

---

## 13. Critical Path Dependencies

```
Cognito Setup ─────────────────────┐
                                   ├──> Auth middleware ──> All protected endpoints
Wallet SDK integration ────────────┘

S3 bucket creation ────> Textract integration ────> Invoice Processing Agent
                                                           |
                                                           v
                                                    Underwriting Agent
                                                           |
                                                           v
                                              Algorand contract deploy ──> NFT minting

Redis setup ──> WebSocket handler ──> Real-time processing view

PostgreSQL + Alembic migrations ──> All data persistence
```

The critical path is: **S3 -> Textract -> Invoice Agent -> Underwriting Agent -> NFT Minting**. This is the core demo flow and must be completed first. Everything else (collection agent, dashboard, alerts) is additive.

---

This architecture document covers all ten requested areas. The key design philosophy is: a single FastAPI monolith with clean internal separation, Strands Swarm for multi-agent orchestration with Redis-bridged WebSocket streaming, Cognito for auth with wallet linking, and backend-side NFT minting for uninterrupted real-time processing.

The architecture fits within the $200 budget, can be built by 2 primary developers in 2 weeks, and provides clear scalability paths for post-hackathon growth.