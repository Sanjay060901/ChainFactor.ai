# ChainFactor AI — Solution Guide

## 1. What is ChainFactor AI?

ChainFactor AI is an **AI-powered invoice financing platform** built for Indian SMEs on the **Algorand blockchain**. It uses a multi-agent AI system to process invoices end-to-end — extracting data, detecting fraud, verifying GST compliance, scoring risk, making underwriting decisions, and minting verified invoices as NFTs on Algorand testnet — all **in under 2 minutes**.

**Live URL:** https://d20nrao7c3w07a.cloudfront.net

---

## 2. The Problem We Solve.

India's 63 million SMEs have **~$100 billion locked in unpaid invoices** with 45–90 day payment cycles. Current options:

| Traditional Process | ChainFactor AI |
|---|---|
| 48–72 hours to process | Under 2 minutes |
| Manual document review | AI-powered 14-step analysis |
| No transparency | Full audit trail + on-chain verification |
| High rates (18–24%) | Risk-based pricing via AI scoring |
| Paper-based trust | Blockchain-verified NFT proof |

---

## 3. How It Works (Architecture)

```
    USER (Browser)
         │
    ┌────▼─────────────────┐
    │  Next.js Frontend     │   ← Hosted on S3 + CloudFront
    │  (Pera/Defly Wallet)  │
    └────┬─────────────────┘
         │ HTTPS / SSE
    ┌────▼─────────────────┐
    │  FastAPI Backend      │   ← ECS Fargate (AWS)
    │  (Modular Monolith)   │
    │                       │
    │  ┌─────────────────┐  │
    │  │ AI Agent Swarm   │  │
    │  │ (2 Agents, 14    │  │
    │  │  AI tools)       │  │
    │  └────────┬────────┘  │
    └───────────┼───────────┘
                │
    ┌───────────┼───────────────────┐
    │           │                   │
  PostgreSQL  Redis  S3   Algorand Testnet
  (RDS)       (Cache) (PDFs)  (NFT mint)
```

### The 2-Agent Pipeline

**Agent 1 — Invoice Processing Agent (Claude Sonnet 4.6)**
Runs 10 analysis tools in sequence:

| Step | Tool | What It Does |
|------|------|-------------|
| 1 | `extract_invoice` | OCR + AI extraction of 23 fields from PDF |
| 2 | `validate_fields` | Checks all required fields are present and valid |
| 3 | `validate_gst_compliance` | Verifies HSN codes, GST rates, e-invoice rules |
| 4 | `verify_gstn` | Checks seller & buyer GSTIN status (active/inactive) |
| 5 | `check_fraud` | 5-layer fraud detection (document, financial, pattern, entity, cross-ref) |
| 6 | `get_buyer_intel` | Buyer payment history and reliability analysis |
| 7 | `get_credit_score` | CIBIL credit score lookup |
| 8 | `get_company_info` | MCA company verification (incorporation, capital, status) |
| 9 | `calculate_risk` | Multi-signal risk scoring (0–100) |
| 10 | `generate_summary` | AI summary with recommendation |

**→ Agent Handoff →**

**Agent 2 — Underwriting Agent (Claude Sonnet 4.6)**
Makes the final decision:

| Step | Tool | What It Does |
|------|------|-------------|
| 11 | `cross_validate_outputs` | Checks consistency across all tool outputs |
| 12 | `underwriting_decision` | Autonomous approve / reject / flag decision |
| 13 | `log_decision` | Records reasoning trace to database |
| 14 | `mint_nft` | Mints ARC-69 NFT on Algorand testnet |

---

## 4. Step-by-Step User Guide

### 4.1 Create an Account

1. Go to https://d20nrao7c3w07a.cloudfront.net
2. Click **"Get Started"** or navigate to **Register**
3. Fill in:
   - Full Name
   - Company Name
   - GSTIN (15-character GST Identification Number)
   - Phone Number
   - Email Address
   - Password
4. Click **Register**
5. You'll be redirected to the Login page

### 4.2 Login

1. Go to the **Login** page
2. Enter your **Email or Phone** and **Password**
3. Click **Login**

> **Demo Account:** `demo@chainfactor.ai` / `Demo@1234` (pre-loaded with 4 test invoices)

### 4.3 Connect Your Algorand Wallet

1. From the **Navbar**, click **"Connect Wallet"**
2. Choose your wallet:
   - **Pera Wallet** (recommended — mobile + web)
   - **Defly Wallet**
3. Approve the connection in your wallet app
4. Your wallet address appears in the navbar

> **Note:** You need an Algorand Testnet wallet. Get free testnet ALGO from the [Algorand Testnet Faucet](https://bank.testnet.algorand.network/).

### 4.4 Upload an Invoice

1. Go to **Invoices** → **Upload**
2. Drag and drop a PDF invoice (or click to browse)
   - Max file size: 5 MB
   - PDF format only
3. Click **Upload**
4. You'll be redirected to the **Processing** page

### 4.5 Watch AI Processing (Real-Time)

The Processing page shows a **live pipeline visualization**:

- Each of the 14 steps appears in sequence
- A progress bar shows overall completion
- A timer tracks total elapsed time
- Step details show input/output summaries
- At step 10→11, you'll see the **Agent Handoff** from Invoice Processing to Underwriting

The pipeline completes with one of three decisions:
- ✅ **Approved** — Invoice passes all checks, NFT minted
- ⚠️ **Flagged** — Needs manual review (medium risk)
- ❌ **Rejected** — Failed fraud or compliance checks

### 4.6 View Invoice Details

After processing, the **Invoice Detail** page shows:

- **Extracted Data** — All fields extracted from the PDF (seller, buyer, amounts, line items)
- **Fraud Detection** — Results from all 5 fraud layers with confidence scores
- **Risk Assessment** — Multi-signal risk score with AI explanation
- **GST Compliance** — HSN code validation, rate matching
- **GSTIN Verification** — Seller and buyer registration status
- **Credit & Company Info** — CIBIL score, MCA company details
- **Underwriting Decision** — Final decision with rule matched and reasoning

### 4.7 Claim Your NFT

If the invoice is **approved** and an NFT was minted:

1. Navigate to the invoice detail page
2. Click **"Claim NFT"**
3. **Step 1 — Opt-In:** Sign the ASA opt-in transaction in your wallet (costs 0.1 ALGO MBR)
4. **Step 2 — Claim:** The platform transfers the NFT to your wallet
5. View your NFT on [Pera Explorer](https://testnet.explorer.perawallet.app/)

### 4.8 View Audit Trail

Every processed invoice has a full **agent reasoning chain**:

1. Go to invoice detail → click **"Audit Trail"**
2. See every tool execution: step number, tool name, input, output, duration, confidence
3. Agent handoff between Invoice Processing Agent → Underwriting Agent is clearly shown
4. Total pipeline duration displayed

### 4.9 Dashboard

The **Dashboard** gives you a portfolio overview:

- **Total Invoice Value** — Sum of all uploaded invoices
- **Active / Pending Invoices** — Counts by status
- **Average Risk Score** — Portfolio-level risk metric
- **Approval Rate** — Percentage of invoices approved
- **Risk Distribution Donut** — Visual breakdown of Low / Medium / High risk invoices
- **Monthly Volume Bar Chart** — Invoice count per month (last 6 months)
- **Recent Invoices** — Quick access to latest uploads

### 4.10 Natural Language Query

On the Dashboard, use the **"Ask AI"** panel to query your portfolio in plain English:

Example queries:
- "How many invoices do I have?"
- "Show me high risk invoices"
- "What's my total invoice value?"
- "Show recent approved invoices"
- "How many invoices have NFTs minted?"

### 4.11 Auto-Approve Rules

Go to **Rules** to configure automatic approval conditions:

1. Click **"Create Rule"**
2. Set conditions: e.g., `risk_score >= 70` AND `fraud_detection == pass`
3. Set action: `auto_approve` or `auto_reject`
4. Toggle rules on/off as needed

When a new invoice is processed, the Underwriting Agent checks your rules first.

### 4.12 On-Chain Verification (Public)

Anyone can verify an invoice NFT without logging in:

1. Go to https://d20nrao7c3w07a.cloudfront.net/verify
2. Enter the **Algorand Asset ID** or **Invoice Number**
3. See: verification status, invoice details, risk score, decision, and Pera Explorer link

This provides **full transparency** for lenders, auditors, and regulators.

### 4.13 AI Settings (Read-Only)

Go to **Settings** to see the AI agent configuration:

- Model IDs (Sonnet 4.6, Opus 4.6, Haiku 4.5)
- Temperature, max tokens, timeout settings per agent
- Swarm configuration (max handoffs, execution timeout)
- Event types streamed in real-time

---

## 5. Test Invoices (Demo Mode)

The demo account comes with 4 pre-processed invoices representing different scenarios:

| Invoice | Seller | Amount | Risk Score | Decision | Scenario |
|---------|--------|--------|-----------|----------|----------|
| INV-2026-001 | Acme Tech Solutions | ₹2,18,300 | 82 (Low) | ✅ Approved | Clean invoice, auto-approved |
| INV-2026-002 | TechCo Exports | ₹1,47,500 | 45 (Medium) | ⚠️ Flagged | Buyer GSTIN inactive |
| INV-2026-003 | BuildRight Infra | ₹5,31,000 | 91 (Low) | ✅ Minted | Excellent profile, NFT minted |
| INV-2026-004 | FakeCorp Ltd | ₹89,999 | 12 (High) | ❌ Rejected | Multiple fraud signals |

---

## 6. Sample Invoice PDFs for Testing

Five ready-to-upload invoice PDFs are included in `docs/sample_invoices/`. These cover different industries and amounts:

| File | Seller | Buyer | Amount | Industry |
|------|--------|-------|--------|----------|
| `INV_2026_101.pdf` | TechnoSoft Solutions | GlobalTrade Industries | ₹3,07,980 | IT Services |
| `INV_2026_102.pdf` | Precision Engineering Works | Tata Motors Components | ₹4,43,680 | Manufacturing |
| `INV_2026_103.pdf` | Agritech Fresh Exports | Dubai Fresh Market LLC | ₹18,25,000 | Agri Export (Zero GST) |
| `INV_2026_104.pdf` | MedSupply India Healthcare | Apollo Hospitals | ₹16,91,200 | Healthcare |
| `INV_2026_105.pdf` | CreativePixel Digital Agency | Flipkart Internet | ₹12,30,740 | Digital Marketing |

**How to use:**
1. Login to ChainFactor AI
2. Go to **Invoices → Upload**
3. Drag and drop any PDF from the `docs/sample_invoices/` folder
4. Click **Upload**, then watch the AI process it in real-time
5. Each invoice will get a unique risk score and underwriting decision

---

## 7. Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, TypeScript |
| Wallet | @txnlab/use-wallet-react (Pera + Defly) |
| Backend | FastAPI, Python 3.11+, Uvicorn |
| AI Framework | Strands Agents SDK (AWS Bedrock-native) |
| AI Models | Claude Sonnet 4.6 (processing + underwriting), Opus 4.6 (NL query) |
| OCR | Amazon Textract |
| Blockchain | Algorand Testnet, ARC-69 NFT standard |
| Database | PostgreSQL 15 (AWS RDS) |
| Cache | Redis 7 (AWS ElastiCache) |
| Storage | AWS S3 |
| Hosting | ECS Fargate + ALB (backend), S3 + CloudFront (frontend) |
| IaC | Terraform (11 reusable modules) |

---

## 8. Key Innovation Points

1. **Agentic AI** — Not just one model call. A coordinated 2-agent system with 14 specialized tools, autonomous decision-making, and structured handoffs.

2. **5-Layer Fraud Detection** — Document integrity, financial consistency, pattern analysis, entity verification, cross-reference checks — all running in parallel.

3. **On-Chain Transparency** — Every approved invoice becomes a verifiable ARC-69 NFT on Algorand. Anyone can verify authenticity without an account.

4. **Real-Time Streaming** — Watch each AI step complete live via Server-Sent Events. Full visibility into the AI reasoning process.

5. **Complete Audit Trail** — Every tool call, every confidence score, every decision reason is recorded and viewable. Full explainability for regulators.

6. **Auto-Approve Rules** — Sellers configure their own underwriting criteria. The AI respects these rules while adding its own risk assessment.

7. **Natural Language Portfolio Query** — Ask questions about your invoices in plain English. No dashboards to learn.

---

## 9. Team

| Name | Role |
|------|------|
| **Sanjay M** | Frontend Lead |
| **Manoj RS** | Backend + AI + DevOps |
| **Abhishek Reddy** | Testing & Support |
| **Jeevidha** | Smart Contract Support |

**Hackathon:** AlgoBharat Hack Series 3.0 — Future of Finance + Agentic Commerce

---

## 10. Quick Links

| Resource | URL |
|----------|-----|
| Live App | https://d20nrao7c3w07a.cloudfront.net |
| API Docs (Swagger) | https://d20nrao7c3w07a.cloudfront.net/api/v1/docs |
| Health Check | https://d20nrao7c3w07a.cloudfront.net/health |
| Pera Explorer (Testnet) | https://testnet.explorer.perawallet.app |
| NFT Verification | https://d20nrao7c3w07a.cloudfront.net/verify |
