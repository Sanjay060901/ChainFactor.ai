# ChainFactor AI — Demo Video Script (4 minutes)

> **Pace:** ~150 words/min. Cues in [brackets] show what's on screen.

---

## 0:00 – 0:25 | The Problem (25s)

[Screen: Title card — "ChainFactor AI" with tagline]

India has 63 million small and medium enterprises — and over **100 billion dollars** locked in unpaid invoices, with payment cycles stretching 45 to 90 days.

Getting those invoices financed today takes 48 to 72 hours of manual paperwork, with no transparency, high interest rates, and zero fraud protection.

We built **ChainFactor AI** to fix that.

---

## 0:25 – 0:55 | What We Built (30s)

[Screen: Architecture diagram or landing page]

ChainFactor AI is an **AI-powered invoice financing platform** on the **Algorand blockchain**. Upload an invoice PDF, and our **multi-agent AI system** processes it end-to-end — extracting data, detecting fraud across 5 layers, verifying GST compliance, scoring risk, making an autonomous underwriting decision, and minting the verified invoice as an **ARC-69 NFT** on Algorand — all **in under 2 minutes**.

Let me show you how it works.

---

## 0:55 – 1:25 | Login + Dashboard (30s)

[Screen: Login page → Dashboard]

We log in with our demo account. The **Dashboard** gives us a portfolio overview — total invoice value, active invoices, average risk score, and approval rate. We can see the risk distribution across our portfolio and monthly volume trends.

There's also a **natural language query** panel — I can ask, "Show me high risk invoices," and the AI responds in plain English.

---

## 1:25 – 2:00 | Upload an Invoice (35s)

[Screen: Invoices → Upload → drag PDF]

Let's process a new invoice. I'll go to **Upload**, drag in a PDF — this is a real Indian GST invoice from a manufacturing company.

[Screen: Processing page starts]

The moment I click Upload, the AI pipeline kicks in. Watch the left panel — each of the **14 steps** appears in real time. This is not a loading spinner. You're watching **two AI agents** work.

---

## 2:00 – 3:00 | The AI Pipeline — The Core (60s)

[Screen: Processing page — steps appearing one by one]

**Agent 1**, our Invoice Processing Agent running on Claude Sonnet, starts with **OCR extraction** — pulling 23 fields from the PDF. Then it **validates** every field, checks **GST compliance** — matching HSN codes and tax rates — and **verifies** both the seller's and buyer's GSTIN on the government registry.

Next comes our **5-layer fraud detection** — checking document integrity, financial consistency, transaction patterns, entity legitimacy, and cross-references. Each layer returns a confidence score.

The agent then pulls **buyer payment history**, runs a **CIBIL credit score** check, verifies the company through **MCA records**, and calculates a **multi-signal risk score** from 0 to 100.

[Screen: Agent handoff visible at step 10→11]

Now watch — the **agent handoff**. Agent 1 passes all its findings to **Agent 2**, the Underwriting Agent. It **cross-validates** every output for consistency, makes an autonomous **approve, reject, or flag** decision, logs its reasoning, and — if approved — **mints an ARC-69 NFT** directly on Algorand testnet.

14 steps. Two agents. One decision. Under 2 minutes.

---

## 3:00 – 3:25 | Invoice Detail + NFT Claim (25s)

[Screen: Invoice detail page → Claim NFT page]

On the invoice detail page, you can see everything — extracted data, fraud layers with confidence scores, risk assessment, GSTIN verification, credit scores, and the final underwriting decision with full reasoning.

Now I'll **claim the NFT**. I connect my **Pera Wallet**, click claim — and the NFT is transferred. Here's the **Pera Explorer** link — you can see our invoice NFT live on Algorand testnet, with the ARC-69 metadata embedded on-chain.

---

## 3:25 – 3:45 | Public Verification (20s)

[Screen: /verify page]

And here's the transparency layer. **Anyone** — a lender, an auditor, a regulator — can go to our **Verify** page, enter the Asset ID, and instantly see the invoice details, risk score, and decision. No login required. Full on-chain verification.

---

## 3:45 – 4:00 | Closing (15s)

[Screen: Architecture diagram or team slide]

ChainFactor AI — **agentic AI** meets **blockchain transparency**. 14 AI tools, 2 autonomous agents, 5-layer fraud detection, real-time streaming, and verifiable NFTs on Algorand. Built for Indian SMEs. Built for the future of finance.

Thank you.

---

**Total: ~590 words | ~4 minutes at natural pace**

### Screen Flow Summary
1. Title card (5s)
2. Landing/architecture (25s)
3. Login → Dashboard + NL query (30s)
4. Upload invoice (20s)
5. Processing pipeline — steps 1-14 (60s) ← **hero moment**
6. Invoice detail page (10s)
7. Claim NFT + Pera Explorer (15s)
8. Verify page (20s)
9. Closing slide (15s)
