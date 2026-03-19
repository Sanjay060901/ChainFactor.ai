# ChainFactor AI - Current TODO

> Track active work items at feature AND milestone level.
> See `project-plan.md` for the full 42-feature plan.
> See `dev-pipeline.md` for the per-feature workflow + milestone checkpoint process.

---

## Milestone 1 (Day 8) — Core Pipeline
**Status: COMPLETE**
**Tag:** `milestone-1` (when tagged)

- [x] Epic 1: 1.1-1.6 (scaffold, skeleton, DB, Docker, Terraform, README)
- [x] Epic 2: 2.1, 2.4, 2.5 BE (auth, wallet, IDOR)
- [x] Epic 3: 3.1 Invoice Upload BE, 3.3 Invoice List BE
- [x] Epic 4: 4.1 Agent Framework, 4.2 WebSocket Server, all 11 tools
- [x] Epic 5: 5.1 Dashboard Summary BE
- [x] Epic 7: 7.1 Seller Rules CRUD
- [x] 321/321 tests passing, all pre-existing failures fixed

---

## Milestone 2 (Day 13) — Agents + Blockchain + Frontend
**Status: IN PROGRESS**

### Backend Integration (COMPLETE — 535/535 tests passing)

- [x] **4.10** Invoice Processing Agent Assembly — 11 tools wired into direct pipeline (Phase 1)
- [x] **4.11** Underwriting Agent + 7 tools — all tools complete, decision routing in pipeline
- [x] **6.1** Smart Contract ARC4 + ARC-69 — 7 ABI methods, fully implemented
- [x] **4.12** Pipeline Orchestration — 14-step pipeline runner with DB persistence + WebSocket events
- [x] **6.2** NFT opt-in endpoint — builds unsigned ASA opt-in txn for wallet signing
- [x] **6.5** NFT claim endpoint — submits opt-in + ASA transfer to user wallet
- [x] Event Bridge — maps tool results to WebSocket step_complete events (51 tests)
- [x] DB Persistence — saves tool results to invoice JSONB columns + agent traces (32 tests)
- [x] Pipeline Runner — orchestrates 14 steps with error handling (42 tests)
- [x] Process Endpoint — POST /invoices/{id}/process triggers pipeline (10 tests)
- [x] Pre-existing bug fixed: mint_nft.py missing `import algosdk`
- [x] IDOR fix: GET /invoices/{id} now requires auth

### Remaining (Frontend + Strands Swarm)

- [ ] Frontend features (Manoj + Sanjay)
- [ ] Strands Swarm integration (Phase 2 — swap direct calls for real Agent/Swarm execution)

### Milestone 2 Checkpoint (before moving to M3)

- [ ] All M2 features complete
- [x] Full test suite passes (535/535)
- [ ] Security scan clean
- [ ] Demo mode works with 3 test invoices
- [ ] README.md updated
- [ ] Retrospective → update lessons.md

---

## Milestone 3 (Day 16) — Polish + Deploy + Demo
**Status: NOT STARTED**

### Features (P1)

- [ ] **5.5** NL Query Agent + Backend
- [ ] **8.1** Critical Path BE Tests
- [ ] **8.3** AWS Deployment (enable terraform + deploy-on-aws plugins)
- [ ] **8.4** Demo Mode polish

### Deployment

- [ ] Docker images built and tested
- [ ] Terraform infrastructure provisioned
- [ ] Backend deployed to ECS Fargate
- [ ] Frontend deployed to S3 + CloudFront
- [ ] Database migrations applied
- [ ] Smoke tests pass on staging

### Demo Preparation

- [ ] Demo mode end-to-end tested
- [ ] Full flow recorded as backup
- [ ] Wallet funded on testnet
- [ ] Talking points prepared
- [ ] Fallback plan verified

### Milestone 3 Checkpoint (final)

- [ ] All features complete
- [ ] Full test suite passes (80%+ coverage)
- [ ] Security scan clean (no CRITICAL/HIGH)
- [ ] Deployed and accessible
- [ ] Demo rehearsed and timed (<2 min)
- [ ] Final retrospective → lessons.md + MEMORY.md
