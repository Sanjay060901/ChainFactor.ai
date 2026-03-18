# ChainFactor AI - UI Wireframes + API Contracts

## Development Method: Skeleton-First (Wireframe Method)

**Approach:** Build all pages and API endpoints as stubs first (Pass 1), then fill in real logic (Pass 2).
- Frontend builds against stub APIs with placeholder data
- Backend returns hardcoded responses matching the contract
- Demo Mode (Feature 8.4) is effectively built-in from day 1
- Integration happens by swapping stub data source with real API calls

---

## Screen 1: Login / Register

**Route:** `/auth/login` and `/auth/register`

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│              ┌──────────────────────┐                │
│              │   ChainFactor AI     │                │
│              │   ⬡ (Algorand logo)  │                │
│              └──────────────────────┘                │
│                                                      │
│              ┌──────────────────────┐                │
│              │  [Login] [Register]  │  ← Tab toggle  │
│              ├──────────────────────┤                │
│              │                      │                │
│              │  Phone / Email       │                │
│              │  ┌──────────────┐   │                │
│              │  │ +91 ________│   │                │
│              │  └──────────────┘   │                │
│              │                      │                │
│              │  Password            │                │
│              │  ┌──────────────┐   │                │
│              │  │ ************ │   │                │
│              │  └──────────────┘   │                │
│              │                      │                │
│              │  ┌──────────────┐   │                │
│              │  │   Sign In    │   │  ← Primary btn │
│              │  └──────────────┘   │                │
│              │                      │                │
│              │  ── or ──           │                │
│              │                      │                │
│              │  ┌──────────────┐   │                │
│              │  │  OTP Login   │   │  ← Secondary   │
│              │  └──────────────┘   │                │
│              │                      │                │
│              └──────────────────────┘                │
│                                                      │
│         "AI-powered invoice financing for SMEs"      │
└──────────────────────────────────────────────────────┘
```

**Register tab adds:** Name, Company Name, GSTIN fields

**API Contract:**
```
POST /api/v1/auth/register
  Body: { phone, email, password, name, company_name, gstin }
  Response: { user_id, message: "OTP sent" }

POST /api/v1/auth/login
  Body: { phone_or_email, password }
  Response: { access_token, refresh_token, user: { id, name, email, phone } }

POST /api/v1/auth/verify-otp
  Body: { phone, otp_code }
  Response: { access_token, refresh_token, user: { id, name, email, phone } }

POST /api/v1/auth/refresh
  Body: { refresh_token }
  Response: { access_token, refresh_token }
```

---

## Screen 2: Dashboard (Home)

**Route:** `/dashboard`

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐│
│  │ Total Value  │ │ Active      │ │ Avg Risk    │ │ Approval  ││
│  │ ₹45,20,000  │ │ 12 invoices │ │ Score: 72   │ │ Rate: 85% ││
│  │ ↑ 12% MTD   │ │ 3 pending   │ │ ↓ from 78   │ │ ↑ from 80 ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘│
│                                                                  │
│  ┌──────────────────────────┐  ┌───────────────────────────────┐│
│  │   Risk Distribution      │  │   Monthly Volume              ││
│  │   ■■■■■■■ Low (60%)     │  │   ┌──┐                        ││
│  │   ■■■ Medium (25%)       │  │   │  │ ┌──┐                   ││
│  │   ■■ High (15%)          │  │ ┌─┤  │ │  │ ┌──┐             ││
│  │                          │  │ │ │  │ │  │ │  │ ┌──┐        ││
│  │   [Donut chart]          │  │ └─┴──┴─┴──┴─┴──┴─┴──┘        ││
│  │                          │  │  Jan  Feb  Mar  Apr           ││
│  └──────────────────────────┘  └───────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │ 💬 Ask anything: ┌──────────────────────────────┐ [Ask]     ││
│  │                   │ Show me high-risk invoices...│           ││
│  │                   └──────────────────────────────┘           ││
│  │                                                              ││
│  │ Response: "You have 3 high-risk invoices this week:          ││
│  │ INV-007 (₹8L, risk 45), INV-012 (₹3L, risk 38)..."        ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Recent Invoices                               [View All →]     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Invoice   │ Seller      │ Amount │ Risk │ Status  │ Date   │ │
│  ├───────────┼─────────────┼────────┼──────┼─────────┼────────┤ │
│  │ INV-001   │ Acme Ltd    │ ₹5.2L  │ 82 ✓│ Approved│ Mar 18 │ │
│  │ INV-002   │ TechCo      │ ₹3.1L  │ 45 ⚠│ Flagged │ Mar 17 │ │
│  │ INV-003   │ BuildRight  │ ₹8.0L  │ 91 ✓│ Minted  │ Mar 16 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

**Wallet status shown in header:**
```
│  👤 Manoj  [🔗 ALGO...X4F2]  ← Wallet connected indicator
```

**API Contract:**
```
GET /api/v1/dashboard/summary
  Response: {
    total_value: 4520000,
    active_invoices: 12,
    pending_invoices: 3,
    avg_risk_score: 72,
    approval_rate: 85.0,
    risk_distribution: { low: 60, medium: 25, high: 15 },
    monthly_volume: [
      { month: "Jan", count: 8, value: 2400000 },
      { month: "Feb", count: 11, value: 3100000 },
      ...
    ]
  }

GET /api/v1/invoices?limit=5&sort=-created_at
  Response: { invoices: [...], total: 42, page: 1, limit: 5 }

POST /api/v1/dashboard/nl-query
  Body: { query: "show me high-risk invoices this week" }
  Response: { answer: "You have 3 high-risk...", data: [...] }
```

---

## Screen 3: Invoice Upload

**Route:** `/invoices/upload`

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Upload Invoice                                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │              ┌──────────────────────┐                        ││
│  │              │                      │                        ││
│  │              │    📄 Drop PDF here  │                        ││
│  │              │                      │                        ││
│  │              │   or click to browse │                        ││
│  │              │                      │                        ││
│  │              │   Max 5MB, PDF only  │                        ││
│  │              │                      │                        ││
│  │              └──────────────────────┘                        ││
│  │                                                              ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ── After file selected ──                                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  📄 invoice_march_2026.pdf (1.2 MB)            [✕ Remove]   ││
│  │                                                              ││
│  │  Preview:                                                    ││
│  │  ┌──────────────────┐                                       ││
│  │  │  [PDF thumbnail]  │                                       ││
│  │  │                   │                                       ││
│  │  └──────────────────┘                                       ││
│  │                                                              ││
│  │           ┌────────────────────────┐                         ││
│  │           │  🚀 Process Invoice    │  ← Primary action      ││
│  │           └────────────────────────┘                         ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**API Contract:**
```
POST /api/v1/invoices/upload
  Body: multipart/form-data { file: PDF }
  Headers: Authorization: Bearer <jwt>
  Response: {
    invoice_id: "uuid",
    status: "processing",
    ws_url: "/ws/processing/{invoice_id}",
    created_at: "2026-03-18T10:00:00Z"
  }
```

---

## Screen 4: Real-Time Processing (STAR SCREEN)

**Route:** `/invoices/{id}/processing`
**Navigated to automatically after upload.**

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Processing Invoice INV-2026-001                    ⏱ 00:47      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 64% (9/14 steps)          │
│                                                                  │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐│
│  │  Agent Pipeline              │  │  Live Details              ││
│  │                              │  │                            ││
│  │  ✅ 1. Extract Invoice Data  │  │  Current: Fraud Detection  ││
│  │     Textract + Claude OCR    │  │                            ││
│  │     → 23 fields extracted    │  │  Layer 3/5: Pattern        ││
│  │                              │  │  Analysis                  ││
│  │  ✅ 2. Validate Fields       │  │                            ││
│  │     Math checks passed       │  │  "Checking invoice amount  ││
│  │     → All 23 fields valid    │  │  against historical        ││
│  │                              │  │  patterns for seller       ││
│  │  ✅ 3. GST Compliance        │  │  GSTIN 27AABCU..."        ││
│  │     HSN codes verified       │  │                            ││
│  │     → e-invoice compliant    │  │  ┌─────────────────────┐  ││
│  │                              │  │  │ Flags found: 0      │  ││
│  │  ✅ 4. GSTIN Verification    │  │  │ Confidence: 94%     │  ││
│  │     GSTIN: 27AABCU9603R1ZM  │  │  └─────────────────────┘  ││
│  │     → Active, matched        │  │                            ││
│  │                              │  │                            ││
│  │  🔄 5. Fraud Detection       │  │                            ││
│  │     5-layer scan in progress │  │                            ││
│  │     → Layer 3 of 5...        │  │                            ││
│  │                              │  │                            ││
│  │  ⏳ 6. Buyer Intelligence    │  │                            ││
│  │  ⏳ 7. CIBIL Credit Score    │  │                            ││
│  │  ⏳ 8. MCA Company Info      │  │                            ││
│  │  ⏳ 9. Risk Calculation      │  │                            ││
│  │  ⏳ 10. Generate Summary     │  │                            ││
│  │  ── Agent Handoff ──         │  │                            ││
│  │  ⏳ 11. Cross-Validation     │  │                            ││
│  │  ⏳ 12. Underwriting Decision│  │                            ││
│  │  ⏳ 13. Log Decision         │  │                            ││
│  │  ⏳ 14. Mint NFT             │  │                            ││
│  │                              │  │                            ││
│  └──────────────────────────────┘  └────────────────────────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**States per step:** ⏳ Pending → 🔄 In Progress → ✅ Complete → ❌ Failed

**After completion (approved):**
```
│  ✅ Processing Complete!  Invoice APPROVED            ⏱ 01:42   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%               │
│                                                                  │
│  Risk Score: 82/100 (Low Risk)    Decision: AUTO-APPROVED        │
│                                                                  │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  View Details →    │  │  Claim NFT 🎫     │                    │
│  └───────────────────┘  └───────────────────┘                    │
```

**After completion (rejected):**
```
│  ❌ Processing Complete!  Invoice REJECTED            ⏱ 01:15   │
│                                                                  │
│  Risk Score: 23/100 (High Risk)    Decision: REJECTED            │
│  Reason: "Duplicate invoice detected. Invoice number INV-2026-   │
│  001 was already processed on March 15, 2026. Amount mismatch    │
│  of ₹1.2L between submitted and original."                      │
│                                                                  │
│  ┌───────────────────┐  ┌───────────────────┐                    │
│  │  View Details →    │  │  View Audit Trail │                    │
│  └───────────────────┘  └───────────────────┘                    │
```

**WebSocket Contract:**
```
WSS /ws/processing/{invoice_id}

Server sends events:
{
  "type": "step_start" | "step_progress" | "step_complete" | "step_error" | "pipeline_complete",
  "step": 1-14,
  "step_name": "extract_invoice",
  "agent": "invoice_processing" | "underwriting",
  "status": "in_progress" | "complete" | "error",
  "detail": "Extracting text from PDF using Textract...",
  "result": { ... },  // populated on step_complete
  "progress": 0.64,   // overall pipeline progress
  "elapsed_ms": 47000
}

Final event:
{
  "type": "pipeline_complete",
  "decision": "approved" | "rejected" | "flagged",
  "risk_score": 82,
  "reason": "...",
  "nft_asset_id": 12345678,  // if approved
  "invoice_id": "uuid"
}
```

**SSE Fallback:**
```
GET /api/v1/invoices/{invoice_id}/stream
  Response: text/event-stream (same event format as WebSocket)
```

---

## Screen 5: Invoice Detail

**Route:** `/invoices/{id}`

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ← Back to Invoices                                              │
│                                                                  │
│  Invoice INV-2026-001                                            │
│  Status: ✅ Approved    NFT: Minted (ASA #12345678)             │
│                                                                  │
│  ┌─── Extracted Data ───────────────────────────────────────────┐│
│  │ Seller: Acme Technologies Pvt Ltd    GSTIN: 27AABCU9603R1ZM ││
│  │ Buyer: TechBuild Solutions           GSTIN: 29AABCT1234R1ZX ││
│  │ Invoice #: INV-2026-001             Date: 2026-03-15        ││
│  │ Amount: ₹5,20,000    Tax: ₹93,600 (18% GST)                ││
│  │ Total: ₹6,13,600     Due: 2026-04-14 (Net 30)              ││
│  │                                                              ││
│  │ Line Items:                                                  ││
│  │ ┌──────────────┬────────┬─────┬───────┬─────────┐          ││
│  │ │ Description  │ HSN    │ Qty │ Rate  │ Amount  │          ││
│  │ │ Cloud Server │ 998314 │ 12  │ 25000 │ 300000  │          ││
│  │ │ Support Hrs  │ 998313 │ 40  │ 5500  │ 220000  │          ││
│  │ └──────────────┴────────┴─────┴───────┴─────────┘          ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─── AI Analysis ─────────────────────────────────────────────┐│
│  │                                                              ││
│  │  ┌── Risk Score ──┐  ┌── GST Compliance ──┐                 ││
│  │  │                │  │                     │                 ││
│  │  │   82 / 100     │  │  ✅ Compliant       │                 ││
│  │  │   LOW RISK     │  │  HSN codes valid    │                 ││
│  │  │                │  │  Rates match slab   │                 ││
│  │  │  [█████████░]  │  │  e-invoice: yes     │                 ││
│  │  │                │  │                     │                 ││
│  │  └────────────────┘  └─────────────────────┘                 ││
│  │                                                              ││
│  │  ┌── Fraud Detection ──────────────────────────────────┐    ││
│  │  │  Layer 1: Document Integrity     ✅ Pass            │    ││
│  │  │  Layer 2: Financial Consistency  ✅ Pass            │    ││
│  │  │  Layer 3: Pattern Analysis       ✅ Pass            │    ││
│  │  │  Layer 4: Entity Verification    ✅ Pass            │    ││
│  │  │  Layer 5: Cross-Reference        ✅ Pass            │    ││
│  │  │  Flags: 0    Confidence: 97%                        │    ││
│  │  └─────────────────────────────────────────────────────┘    ││
│  │                                                              ││
│  │  ┌── GSTIN ──┐  ┌── CIBIL ──┐  ┌── MCA ─────────────┐     ││
│  │  │ Verified ✅│  │ Score:750 │  │ Active company      │     ││
│  │  │ Active    │  │ Good      │  │ Inc: 2015           │     ││
│  │  │ Matched   │  │           │  │ Paid-up: ₹10Cr     │     ││
│  │  └───────────┘  └───────────┘  └─────────────────────┘     ││
│  │                                                              ││
│  │  ┌── Buyer Intelligence ──────────────────────────────┐     ││
│  │  │  Payment history: Reliable (avg 28 days)           │     ││
│  │  │  Previous invoices: 8 (all paid)                   │     ││
│  │  │  Industry: Technology Services                     │     ││
│  │  └────────────────────────────────────────────────────┘     ││
│  │                                                              ││
│  │  ┌── AI Risk Explanation ─────────────────────────────┐     ││
│  │  │  "This invoice presents low risk. The seller has   │     ││
│  │  │  an active GSTIN with consistent filing history.   │     ││
│  │  │  The buyer has a CIBIL score of 750 and has paid   │     ││
│  │  │  all 8 previous invoices on time. GST rates match  │     ││
│  │  │  the applicable slab for HSN 998314. No fraud      │     ││
│  │  │  indicators detected across all 5 layers."         │     ││
│  │  └────────────────────────────────────────────────────┘     ││
│  │                                                              ││
│  │  ┌── Underwriting Decision ───────────────────────────┐     ││
│  │  │  Decision: AUTO-APPROVED                           │     ││
│  │  │  Rule matched: "Approve invoices under ₹10L with   │     ││
│  │  │  risk score > 60"                                  │     ││
│  │  │  Cross-validation: PASSED (all outputs consistent) │     ││
│  │  └────────────────────────────────────────────────────┘     ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐                          │
│  │  Claim NFT 🎫  │  │  Audit Trail 📋│                          │
│  └────────────────┘  └────────────────┘                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**API Contract:**
```
GET /api/v1/invoices/{invoice_id}
  Response: {
    id: "uuid",
    invoice_number: "INV-2026-001",
    status: "approved" | "rejected" | "flagged" | "processing" | "pending",
    created_at: "...",

    // Extracted data
    extracted_data: {
      seller: { name, gstin, address },
      buyer: { name, gstin, address },
      invoice_number, invoice_date, due_date,
      subtotal, tax_amount, tax_rate, total_amount,
      line_items: [{ description, hsn_code, quantity, rate, amount }]
    },

    // AI analysis results
    validation: { is_valid: true, errors: [], warnings: [] },
    gst_compliance: { is_compliant: true, details: {...} },
    fraud_detection: {
      overall: "pass",
      confidence: 97,
      flags: [],
      layers: [
        { name: "Document Integrity", result: "pass", detail: "..." },
        { name: "Financial Consistency", result: "pass", detail: "..." },
        { name: "Pattern Analysis", result: "pass", detail: "..." },
        { name: "Entity Verification", result: "pass", detail: "..." },
        { name: "Cross-Reference", result: "pass", detail: "..." }
      ]
    },
    gstin_verification: { verified: true, status: "active", details: {...} },
    buyer_intel: { payment_history: "reliable", avg_days: 28, previous_count: 8 },
    credit_score: { score: 750, rating: "good" },
    company_info: { status: "active", incorporated: "2015", paid_up_capital: 100000000 },
    risk_assessment: {
      score: 82,
      level: "low",
      explanation: "This invoice presents low risk..."
    },

    // Underwriting
    underwriting: {
      decision: "approved",
      rule_matched: "Approve invoices under ₹10L with risk score > 60",
      cross_validation: "passed",
      reasoning: "..."
    },

    // NFT
    nft: {
      asset_id: 12345678,
      status: "minted" | "claimed" | null,
      explorer_url: "https://testnet.explorer.perawallet.app/asset/12345678/",
      metadata: { standard: "arc69", ... }
    }
  }
```

---

## Screen 6: Claim NFT

**Route:** `/invoices/{id}/claim` (or modal on Invoice Detail)

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Claim Your Invoice NFT                                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │   ┌────────────────────────────────┐                         ││
│  │   │  ┌──────────────────────────┐  │                         ││
│  │   │  │   ChainFactor AI         │  │                         ││
│  │   │  │   INVOICE NFT            │  │                         ││
│  │   │  │                          │  │                         ││
│  │   │  │   INV-2026-001           │  │  ← NFT Card            ││
│  │   │  │   Acme Tech → TechBuild  │  │                         ││
│  │   │  │   ₹6,13,600              │  │                         ││
│  │   │  │                          │  │                         ││
│  │   │  │   Risk: 82 (Low)         │  │                         ││
│  │   │  │   Status: APPROVED       │  │                         ││
│  │   │  │                          │  │                         ││
│  │   │  │   ASA #12345678          │  │                         ││
│  │   │  │   ⬡ Algorand Testnet     │  │                         ││
│  │   │  └──────────────────────────┘  │                         ││
│  │   └────────────────────────────────┘                         ││
│  │                                                              ││
│  │   Step 1: Opt-in to Asset                                    ││
│  │   ┌────────────────────────────────────────────┐             ││
│  │   │  This will increase your minimum balance   │             ││
│  │   │  by 0.1 ALGO. Your wallet will sign an     │             ││
│  │   │  opt-in transaction.                       │             ││
│  │   │                                            │             ││
│  │   │  ┌──────────────────────────┐              │             ││
│  │   │  │  Opt-in to ASA (0.1 ALGO)│  ← Pera signs            ││
│  │   │  └──────────────────────────┘              │             ││
│  │   └────────────────────────────────────────────┘             ││
│  │                                                              ││
│  │   Step 2: Receive NFT Transfer     ← After opt-in           ││
│  │   ┌────────────────────────────────────────────┐             ││
│  │   │  ┌──────────────────────────┐              │             ││
│  │   │  │  Claim NFT               │  ← Triggers transfer     ││
│  │   │  └──────────────────────────┘              │             ││
│  │   └────────────────────────────────────────────┘             ││
│  │                                                              ││
│  │   ── After claim ──                                          ││
│  │                                                              ││
│  │   ✅ NFT Claimed Successfully!                               ││
│  │                                                              ││
│  │   ┌────────────────────────────────────────┐                 ││
│  │   │  🔗 View on Pera Explorer              │                 ││
│  │   └────────────────────────────────────────┘                 ││
│  │                                                              ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

**API Contract:**
```
POST /api/v1/invoices/{invoice_id}/nft/opt-in
  Body: { wallet_address: "ALGO...", signed_txn: "base64..." }
  Response: { txn_id: "...", status: "opted_in" }

POST /api/v1/invoices/{invoice_id}/nft/claim
  Body: { wallet_address: "ALGO..." }
  Response: {
    txn_id: "...",
    asset_id: 12345678,
    status: "claimed",
    explorer_url: "https://testnet.explorer.perawallet.app/asset/12345678/"
  }
```

---

## Screen 7: Seller Rules (Auto-Approve Settings)

**Route:** `/rules`

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Auto-Approve Rules                                              │
│  Set conditions for automatic invoice approval.                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  Rule 1                                         [🗑 Delete]  ││
│  │                                                              ││
│  │  IF invoice amount  [is less than ▼]  ₹ [5,00,000]         ││
│  │  AND risk score     [is greater than ▼]   [60]              ││
│  │  AND fraud flags    [equals ▼]            [0]               ││
│  │  THEN → Auto-approve                                        ││
│  │                                                              ││
│  │  Status: ✅ Active                              [Toggle ⚪]  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  Rule 2                                         [🗑 Delete]  ││
│  │                                                              ││
│  │  IF invoice amount  [is less than ▼]  ₹ [10,00,000]        ││
│  │  AND risk score     [is greater than ▼]   [80]              ││
│  │  AND CIBIL score    [is greater than ▼]   [700]             ││
│  │  THEN → Auto-approve                                        ││
│  │                                                              ││
│  │  Status: ✅ Active                              [Toggle ⚪]  ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────┐                                        │
│  │  + Add New Rule      │                                        │
│  └─────────────────────┘                                        │
│                                                                  │
│  ── Default Behavior ──                                          │
│  When no rules match: [Flag for manual review ▼]                 │
│  Options: Flag for manual review / Reject / Always approve       │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  Save     │                                                    │
│  └──────────┘                                                    │
└──────────────────────────────────────────────────────────────────┘
```

**API Contract:**
```
GET /api/v1/rules
  Response: {
    rules: [
      {
        id: "uuid",
        conditions: [
          { field: "amount", operator: "lt", value: 500000 },
          { field: "risk_score", operator: "gt", value: 60 },
          { field: "fraud_flags", operator: "eq", value: 0 }
        ],
        action: "auto_approve",
        is_active: true,
        created_at: "..."
      }
    ],
    default_action: "flag_for_review"
  }

POST /api/v1/rules
  Body: { conditions: [...], action: "auto_approve" }
  Response: { id: "uuid", ... }

PUT /api/v1/rules/{rule_id}
  Body: { conditions: [...], action: "...", is_active: true }
  Response: { id: "uuid", ... }

DELETE /api/v1/rules/{rule_id}
  Response: { deleted: true }

PUT /api/v1/rules/default-action
  Body: { default_action: "flag_for_review" }
  Response: { default_action: "flag_for_review" }
```

---

## Screen 8: Audit Trail

**Route:** `/invoices/{id}/audit` (or tab on Invoice Detail)

```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 Manoj │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ← Back to Invoice INV-2026-001                                  │
│                                                                  │
│  Audit Trail - Full Agent Reasoning Chain                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │  🤖 Invoice Processing Agent (Sonnet 4.6)                   ││
│  │  Started: 2026-03-18 10:00:00    Duration: 1m 12s           ││
│  │                                                              ││
│  │  ┌─ Step 1: extract_invoice ─────────── 3.2s ──────────────┐││
│  │  │ Input: invoice_march_2026.pdf (1.2 MB)                  │││
│  │  │ Method: Amazon Textract (primary)                       │││
│  │  │ Output: 23 fields extracted, 2 line items               │││
│  │  │ Confidence: 98.2%                                       │││
│  │  └─────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  ┌─ Step 2: validate_fields ─────────── 1.1s ──────────────┐││
│  │  │ Checks: math_correct, dates_valid, amounts_consistent   │││
│  │  │ Result: ALL PASS (23/23 fields)                         │││
│  │  └─────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  ┌─ Step 3: validate_gst_compliance ──── 0.8s ─────────────┐││
│  │  │ HSN 998314: valid (IT Services), Rate 18%: correct      │││
│  │  │ HSN 998313: valid (Management Consulting), Rate 18%: ok │││
│  │  │ e-invoice: required (turnover > ₹5Cr), present: yes     │││
│  │  │ Result: GST COMPLIANT                                   │││
│  │  └─────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  ... (Steps 4-10 in same format) ...                        ││
│  │                                                              ││
│  │  ── HANDOFF → Underwriting Agent ──                          ││
│  │  Context passed: extracted_data, risk_score, fraud_result,  ││
│  │  gst_compliance, gstin_status, credit_score, company_info   ││
│  │                                                              ││
│  │  🤖 Underwriting Agent (Sonnet 4.6)                         ││
│  │  Started: 2026-03-18 10:01:12    Duration: 0m 30s           ││
│  │                                                              ││
│  │  ┌─ Step 11: cross_validate_outputs ──── 2.4s ─────────────┐││
│  │  │ Checking: amount consistency across all tool outputs     │││
│  │  │ Checking: GSTIN match across extraction and verification │││
│  │  │ Checking: risk score inputs match tool outputs           │││
│  │  │ Result: ALL CONSISTENT (0 discrepancies)                │││
│  │  └─────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  ┌─ Step 12: underwriting_decision ──── 1.8s ──────────────┐││
│  │  │ Rule evaluated: "amount < 5L AND risk > 60 AND flags=0" │││
│  │  │ Match: YES (amount=₹6.1L NO... checking next rule)      │││
│  │  │ Rule evaluated: "amount < 10L AND risk > 80 AND CIBIL>7"│││
│  │  │ Match: YES                                              │││
│  │  │ Decision: AUTO-APPROVED                                 │││
│  │  │ Reasoning: "Invoice meets Rule 2 criteria. Risk score   │││
│  │  │ of 82 exceeds threshold of 80. CIBIL score 750 exceeds │││
│  │  │ threshold. All fraud checks passed. Recommending        │││
│  │  │ approval with standard terms."                          │││
│  │  └─────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  ── HANDOFF → Invoice Processing Agent (mint) ──             ││
│  │                                                              ││
│  │  ┌─ Step 14: mint_nft ──────────────── 4.2s ───────────────┐││
│  │  │ Standard: ARC-69                                        │││
│  │  │ ASA ID: 12345678                                        │││
│  │  │ Txn: https://testnet.explorer.perawallet.app/tx/ABC...  │││
│  │  │ Metadata: { invoice_id, risk_score, doc_hash, ... }     │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**API Contract:**
```
GET /api/v1/invoices/{invoice_id}/audit-trail
  Response: {
    invoice_id: "uuid",
    total_duration_ms: 102000,
    agents: [
      {
        name: "Invoice Processing Agent",
        model: "sonnet-4.6",
        started_at: "...",
        duration_ms: 72000,
        steps: [
          {
            step_number: 1,
            tool_name: "extract_invoice",
            started_at: "...",
            duration_ms: 3200,
            input_summary: "invoice_march_2026.pdf (1.2 MB)",
            output_summary: "23 fields extracted, 2 line items",
            result: { ... },
            status: "success"
          },
          ...
        ]
      },
      {
        name: "Underwriting Agent",
        model: "sonnet-4.6",
        started_at: "...",
        duration_ms: 30000,
        steps: [...]
      }
    ],
    handoffs: [
      {
        from: "Invoice Processing Agent",
        to: "Underwriting Agent",
        context_keys: ["extracted_data", "risk_score", "fraud_result", ...]
      }
    ]
  }
```

---

## Shared Components

### Navigation Bar
```
┌──────────────────────────────────────────────────────────────────┐
│  ⬡ ChainFactor AI    [Dashboard] [Invoices] [Rules]    👤 🔗    │
│                                                         name wallet│
└──────────────────────────────────────────────────────────────────┘

- Logo links to /dashboard
- Active tab is highlighted
- Wallet indicator: 🔗 shows truncated address if connected, "Connect" button if not
- User avatar/name dropdown: Profile, Disconnect Wallet, Logout
```

### Invoice List (embedded in Dashboard + standalone)
```
Route: /invoices

┌────────────────────────────────────────────────────────────────┐
│  Invoices                                    [+ Upload New]    │
│                                                                │
│  Filter: [All ▼] [Date range] [Risk: All ▼]  Search: [____]  │
│                                                                │
│  ┌──────────┬───────────┬────────┬──────┬─────────┬──────────┐│
│  │ Invoice  │ Seller    │ Amount │ Risk │ Status  │ Actions  ││
│  ├──────────┼───────────┼────────┼──────┼─────────┼──────────┤│
│  │ INV-001  │ Acme Tech │ ₹5.2L  │ 82 ✓│ Minted  │ [View]   ││
│  │ INV-002  │ TechCo    │ ₹3.1L  │ 45 ⚠│ Flagged │ [View]   ││
│  │ INV-003  │ BuildRt   │ ₹8.0L  │ 91 ✓│ Claimed │ [View]   ││
│  │ INV-004  │ FakeCorp  │ ₹2.1L  │ 12 ❌│ Rejected│ [View]   ││
│  └──────────┴───────────┴────────┴──────┴─────────┴──────────┘│
│                                                                │
│  Showing 1-10 of 42          [← Prev]  [1] 2 3 4  [Next →]   │
└────────────────────────────────────────────────────────────────┘

GET /api/v1/invoices?page=1&limit=10&status=all&risk_level=all&sort=-created_at&search=
  Response: {
    invoices: [...],
    total: 42,
    page: 1,
    limit: 10,
    pages: 5
  }
```

---

## Wallet Connection API

```
POST /api/v1/wallet/link
  Body: { wallet_address: "ALGO...", signed_message: "base64..." }
  Headers: Authorization: Bearer <jwt>
  Response: { linked: true, wallet_address: "ALGO..." }

GET /api/v1/wallet/status
  Headers: Authorization: Bearer <jwt>
  Response: { linked: true, wallet_address: "ALGO...", algo_balance: 10.5 }

DELETE /api/v1/wallet/link
  Headers: Authorization: Bearer <jwt>
  Response: { linked: false }
```
