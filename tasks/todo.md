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

### Next Up (P0 - Can Run in Parallel)

- [ ] **4.10** Invoice Processing Agent Assembly — wire 11 tools into Strands Agent
- [ ] **4.11** Underwriting Agent + 7 tools — cross_validate, approve/reject/flag, log_decision
- [ ] **6.1** Smart Contract ARC4 + ARC-69 — scaffold exists, needs full impl

### Then (P0 - Sequential, depends on above)

- [ ] **4.12** Swarm Orchestration — wire both agents into Strands Swarm
- [ ] **6.2** mint_nft endpoint + ASA opt-in + transfer
- [ ] **6.5** Claim NFT flow BE portion

### Frontend (Manoj + Sanjay)

- [ ] Frontend features as needed (Manoj now also doing FE work)

### Milestone 2 Checkpoint (before moving to M3)

- [ ] All M2 features complete
- [ ] Full test suite passes
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
