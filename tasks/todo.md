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

- [x] Frontend features — all 17 routes built (auth, dashboard, invoices, processing, claim, audit, rules, settings, verify, nft-preview)
- [x] Settings router mounted in API v1 (was missing)
- [ ] Strands Swarm integration (Phase 2 — swap direct calls for real Agent/Swarm execution; `strands.multiagent.swarm` removed in v0.1.9, 4 tests skipped)

### Milestone 2 Checkpoint (before moving to M3)

- [x] All M2 features complete (except Strands Swarm Phase 2 — deferred, SDK restructured)
- [x] Full test suite passes (511/511 + 4 skipped swarm tests)
- [x] Security scan clean (bandit: 0 medium/high/critical, 4 low false-positives)
- [x] Demo mode works with 4 test invoices (INV-2026-001..004)
- [x] README.md updated (test counts, deployed URL, 4 invoices, endpoint corrections)
- [x] Retrospective → lessons.md updated (Strands v0.1.9 swarm removal)

---

## Milestone 3 (Day 16) — Polish + Deploy + Demo
**Status: IN PROGRESS**

### Features (P1)

- [x] **5.5** NL Query Agent + Backend — rule-based nl_engine (15+ query types, safe ORM)
- [x] **8.1** Critical Path BE Tests — 511/511 passing
- [x] **8.3** AWS Deployment — backend + frontend redeployed
- [x] **8.4** Demo Mode polish — agent handoff SSE event added

### Deployment

- [x] Docker images built and tested (CodeBuild succeeded)
- [x] Terraform infrastructure provisioned (already live)
- [x] Backend deployed to ECS Fargate (service stable)
- [x] Frontend deployed to S3 + CloudFront (cache invalidated)
- [x] Database migrations applied (entrypoint.sh runs alembic)
- [x] Smoke tests pass on staging (health, login, settings, nl-query verified)

### Demo Preparation

- [x] Demo mode end-to-end tested (SSE stream + DB update + frontend)
- [ ] Full flow recorded as backup
- [ ] Wallet funded on testnet
- [ ] Talking points prepared
- [ ] Fallback plan verified

### Milestone 3 Checkpoint (final)

- [ ] All features complete
- [x] Full test suite passes (511 passed, 4 skipped)
- [x] Security scan clean (no CRITICAL/HIGH)
- [x] Deployed and accessible (https://d20nrao7c3w07a.cloudfront.net)
- [ ] Demo rehearsed and timed (<2 min)
- [ ] Final retrospective → lessons.md + MEMORY.md
