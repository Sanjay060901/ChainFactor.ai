
# ChainFactor AI - Development Pipeline

> **Single source of truth** for the entire project lifecycle — from new project bootstrap
> through per-feature development to deployment, monitoring, and demo delivery.
> Maps skills, agents, slash commands, plugins, MCP tools, and hooks into one actionable flow.
>
> Last updated: 2026-03-19

---

## Table of Contents

1. [Project Lifecycle Overview](#project-lifecycle-overview)
2. [Project Bootstrap](#project-bootstrap-new-projects)
3. [Session Continuity](#session-continuity)
4. [Quick Reference Card](#quick-reference-card) (per-feature)
5. [Phase 0-9](#phase-0-session-start-automatic) (per-feature development)
6. [Special Flows](#special-flows)
7. [Milestone Checkpoints](#milestone-checkpoints)
8. [Deployment Workflow](#deployment-workflow)
9. [Post-Deployment & Monitoring](#post-deployment--monitoring)
10. [Demo Preparation](#demo-preparation-hackathon)
11. [Context Management](#context-management)
12. [Plugin & MCP Reference](#plugin--mcp-reference)
13. [Agent Roster](#agent-roster)
14. [Slash Commands Cheat Sheet](#slash-commands-cheat-sheet)
15. [Superpowers Orchestration Flow](#superpowers-orchestration-flow)
16. [What's Automatic vs Manual](#whats-automatic-vs-manual)
17. [Anti-Patterns](#anti-patterns-dont-do-this)

---

## Project Lifecycle Overview

```
[A] PROJECT BOOTSTRAP ──── new project only (once)
 |
[B] SESSION START ──────── every session
 |
[C] PER-FEATURE CYCLE ─── repeat for each feature (Phases 0-9)
 |   Phase 0: Session Start
 |   Phase 1: Research
 |   Phase 2: Planning
 |   Phase 3: Implementation (TDD)
 |   Phase 4: Build & Fix
 |   Phase 5: Code Review
 |   Phase 6: Verification
 |   Phase 7: Documentation
 |   Phase 8: Commit & PR
 |   Phase 9: Post-Feature
 |
[D] MILESTONE CHECKPOINT ── at each milestone boundary
 |
[E] DEPLOYMENT ──────────── per-milestone or final
 |
[F] POST-DEPLOYMENT ─────── monitoring, incident response
 |
[G] DEMO PREPARATION ───── hackathon/presentation readiness
 |
[H] SESSION END ─────────── save state, extract learnings
```

---

## Project Bootstrap (New Projects)

> Run ONCE at project creation. Not needed for existing projects.

### Step A1: Initialize Project
```
Skill: new-project
```
- Bootstrap project scaffold (dirs, configs, entry points)
- Select tech stack, framework templates
- Initialize git repo with `main` branch

### Step A2: Generate Core Artifacts (mandatory, immediate)

| # | Artifact | Purpose | Skill/Tool |
|---|----------|---------|------------|
| 1 | `README.md` | Project overview, setup, team | Manual (FIRST doc artifact) |
| 2 | `CLAUDE.md` | Project-level instructions, rules, key files | `/revise-claude-md` |
| 3 | `.gitignore` | Language + framework ignores | `new-project` |
| 4 | `tasks/project-plan.md` | Epics, features, milestones | `project-planning` skill |
| 5 | `tasks/lessons.md` | Empty, ready for first lesson | Manual |
| 6 | `tasks/todo.md` | Active work tracking | Manual |
| 7 | `tasks/dev-pipeline.md` | This document (copy/adapt) | Manual |
| 8 | `tasks/wireframes.md` | ASCII wireframes + API contracts | Manual or `spec-workflow` |

### Step A3: Architecture & Design
```
Agent: architect  →  system design, component diagram, tech decisions
Skill: superpowers:brainstorming  →  explore architecture options
Skill: project-planning  →  break into epics, features, milestones
```
- Document decisions in `tasks/architecture-raw.md`
- Skeleton-first: define ALL API contracts before implementation
- Identify risks, dependencies, integration points

### Step A4: Environment Setup
- Configure `CLAUDE.md` with project-specific rules
- Set up `.env.example` with all required env vars
- Docker Compose for local dev (DB, cache, services)
- CI/CD pipeline (GitHub Actions)
- Terraform for infrastructure (if applicable)

### Step A5: Smoke Tests (Day 1)
- Verify all SDK/library versions match documentation
- Test external service connectivity (APIs, databases, blockchain)
- Request quota increases (Bedrock RPM, API rate limits)
- Verify static export / build compatibility

---

## Session Continuity

> Protocol for maintaining context across sessions. Follow EVERY session.

### Session Start Protocol

| Step | Action | Tool |
|------|--------|------|
| 1 | Hooks auto-fire (project detect, profile load, ECC check) | Automatic |
| 2 | Resume previous session if available | `/resume-session` |
| 3 | Read MEMORY.md | Auto-loaded |
| 4 | Read `tasks/lessons.md` for recent corrections | Manual or auto |
| 5 | Check `tasks/todo.md` for current progress | Manual |
| 6 | Review `git status` for uncommitted work | Manual |
| 7 | State the feature/task to work on | User |

### Mid-Session Checkpoints
```
Skill: /checkpoint
```
- Save progress at natural breakpoints (after completing a sub-task)
- Use when context window is getting large
- Use before switching to a different feature/topic

### Context Window Management
```
Skill: strategic-compact
```
- **When to trigger:** Context approaching 80% capacity, or after 10+ tool calls
- **What it does:** Suggests what can be safely compacted/forgotten
- **Alternative:** Offload research/exploration to subagents (Explore, Plan) to keep main context clean
- **Rule:** Use subagents liberally — one task per subagent for focused execution

### Session End Protocol

| Step | Action | Tool |
|------|--------|------|
| 1 | Update `tasks/todo.md` — mark completed, note blockers | Manual |
| 2 | Update `tasks/lessons.md` — any corrections or gotchas | Manual |
| 3 | Extract reusable patterns | `/learn` |
| 4 | Save session state for next time | `/save-session` |
| 5 | Update MEMORY.md if stable new patterns confirmed | Manual |
| 6 | Dotfiles auto-sync fires | `stop-dotfiles-sync.sh` (automatic) |

---

## Quick Reference Card

### Project Lifecycle Stages

| Stage | When | Key Action |
|-------|------|------------|
| **A. Bootstrap** | New project only | `/new-project`, generate core artifacts |
| **B. Session Start** | Every session | `/resume-session`, read lessons.md + todo.md |
| **C. Per-Feature** | Phases 0-9 below | Full development cycle |
| **D. Milestone** | At epic/milestone boundary | Full review, tag, retrospective |
| **E. Deployment** | Per-milestone or final | Enable terraform plugin, deploy, smoke test |
| **F. Monitoring** | Post-deployment | Health checks, incident response |
| **G. Demo Prep** | 1-2 days before demo | End-to-end test, rehearsal, backup recording |
| **H. Session End** | Every session | Update todo.md, `/learn`, `/save-session` |

### Per-Feature Phases (Stage C)

| Phase | Slash Command | Skill | Agent | Auto? |
|-------|--------------|-------|-------|-------|
| 0. Session Start | `/resume-session` | - | - | Hooks auto-fire |
| 1. Research | - | `deep-research`, `exa-search` | Explore subagent | Manual |
| 2. Planning | `/plan` | `superpowers:brainstorming`, `superpowers:writing-plans` | planner, architect | Manual |
| 3. Implementation | `/tdd` | `superpowers:test-driven-development`, `python-patterns`, `frontend-patterns` | tdd-guide | Manual |
| 4. Build & Fix | `/build-fix` | `build-fix` | build-error-resolver | On failure |
| 5. Code Review | `/code-review` | `superpowers:requesting-code-review`, `simplify` | code-reviewer, python-reviewer, security-reviewer | After impl |
| 6. Verification | `/verify` | `superpowers:verification-before-completion`, `verification-loop` | - | Before done |
| 7. Documentation | `/update-docs` | `documentation-workflow` | doc-updater | After verify |
| 8. Commit & PR | `/commit`, `/commit-push-pr` | `superpowers:finishing-a-development-branch`, `git-workflow` | - | Manual |
| 9. Post-Feature | `/learn` | `continuous-learning` | - | After each feature |

---

## Phase 0: Session Start (Automatic)

> See [Session Continuity](#session-continuity) for the full start/end protocol.

**What fires automatically (via hooks in `~/.claude/settings.json`):**

| Hook | What It Does |
|------|-------------|
| `session-start-project-detect.sh` | Detects project type, loads context |
| `session-start-ecc-update-check.sh` | Checks for ECC plugin updates (async) |
| Profile loader (Node inline) | Loads `~/.claude/memory/PROFILE.md` into context |

**What YOU should do at session start:**
1. Resume previous session if available: `/resume-session`
2. Claude reads `MEMORY.md` (auto-loaded) and `tasks/lessons.md`
3. Check `tasks/todo.md` for current progress
4. Review git status for uncommitted work
5. State the feature/task you want to work on

---

## Phase 1: Research & Discovery

> **Rule:** Never write code before researching. (from `development-workflow.md` Step 0)

### Search Order (mandatory)
1. **GitHub code search** -- `gh search repos`, `gh search code` via GitHub MCP
2. **Library docs** -- Context7 MCP (`resolve-library-id` -> `query-docs`)
3. **AWS docs** -- AWS Docs MCP (`search_documentation` -> `read_documentation`)
4. **Web search** -- Exa MCP (`web_search_exa`) -- only when steps 1-3 insufficient
5. **Package registries** -- `pip index versions`, `npm view`

### Skills & Tools
| What | When |
|------|------|
| `deep-research` skill | Unfamiliar domain, need multi-source synthesis |
| `exa-search` skill | Broad web discovery |
| `iterative-retrieval` skill | Progressively deeper codebase exploration |
| Explore subagent | Codebase exploration (find files, patterns, architecture) |
| Serena MCP | Semantic code analysis (symbols, references, overview) |

### Output
- Understanding of existing patterns to reuse
- Library versions confirmed
- API contracts verified

---

## Phase 2: Planning & Design

> **Rule:** Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).

### Step 2a: Brainstorm (REQUIRED before plan mode)
```
Skill: superpowers:brainstorming
```
- Fires BEFORE entering plan mode
- Explores multiple approaches, trade-offs
- Identifies risks and dependencies
- Narrows to the best approach

### Step 2b: Write Plan
```
Skill: superpowers:writing-plans  OR  /plan
```
- Produces structured implementation plan
- Breaks into phases with checkable items
- Identifies files to create/modify

### Step 2c: Architecture Review (if needed)
```
Agent: architect     -- system design, scalability, technical decisions
Agent: planner       -- implementation plan, phases, risks
Agent: database-reviewer  -- if DB schema changes needed
```
- Use `superpowers:dispatching-parallel-agents` to run multiple reviewers at once
- For complex features, launch architect + planner in parallel

### Output
- Plan written to `tasks/todo.md` with checkable items
- Architecture decisions documented
- Dependencies and risks identified

---

## Phase 3: Implementation (TDD)

> **Rule:** NEVER skip TDD. Write tests BEFORE implementation. (from `lessons.md`)

### Step 3a: Execute Plan
```
Skill: superpowers:executing-plans
```
- Follows the written plan step by step
- Updates todo items as completed
- For large features: `superpowers:subagent-driven-development` dispatches work to subagents

### Step 3b: TDD Cycle (per unit of work)
```
Skill: superpowers:test-driven-development  OR  /tdd
Agent: tdd-guide
```

| Phase | What | Verify |
|-------|------|--------|
| RED | Write failing test | `python -m pytest tests/... -v` -- MUST fail |
| GREEN | Write minimal implementation | `python -m pytest tests/... -v` -- MUST pass |
| IMPROVE | Refactor, clean up | All tests still pass, coverage 80%+ |

### Reference Skills (consult during implementation)
| Skill | When |
|-------|------|
| `python-patterns` | Python idioms, PEP 8, type hints |
| `python-testing` | pytest patterns, mocking, fixtures |
| `frontend-patterns` | React/Next.js patterns, hooks, components |
| `backend-patterns` | FastAPI architecture, middleware, error handling |
| `postgres-patterns` | SQLAlchemy queries, migrations, JSONB |
| `coding-standards` | Universal quality standards |
| `security-review` | When handling auth, user input, API endpoints |

### MCP Tools During Implementation
| Tool | When |
|------|------|
| Context7 | Look up library API docs mid-implementation |
| Serena | Navigate symbols, find references, understand code structure |
| Pyright LSP | Type checking for Python |
| TypeScript LSP | Type checking for Next.js/TypeScript |

### Parallel Implementation
```
Skill: superpowers:dispatching-parallel-agents  OR  parallel-orchestrator
```
- When 2+ independent pieces can be built simultaneously
- Example: backend route + frontend component + test file
- Launch multiple Agent subagents in a single message

### Git Worktrees (for isolated feature work)
```
Skill: superpowers:using-git-worktrees
```
- Creates isolated git worktree for feature branch
- Agent works in worktree without affecting main
- Merge back when complete

---

## Phase 4: Build & Fix

> Fires when tests fail or build breaks.

```
Skill: build-fix
Agent: build-error-resolver
```

### Process
1. Run full test suite: `python -m pytest tests/ --tb=short -q`
2. If failures: agent analyzes errors, fixes incrementally
3. Verify after each fix
4. For stubborn errors: `superpowers:systematic-debugging`

### Debugging Flow
```
Skill: superpowers:systematic-debugging
```
1. Reproduce the issue
2. Form hypothesis
3. Test hypothesis
4. Fix root cause (not symptoms)
5. Add regression test
6. Verify fix

---

## Phase 5: Code Review (Multi-Layer)

> **Rule:** Use code-reviewer agent IMMEDIATELY after writing code. (from `agents.md`)

### Step 5a: Request Review
```
Skill: superpowers:requesting-code-review  OR  /code-review
```

### Step 5b: Multi-Agent Review (run in PARALLEL)

| Agent | Focus | Priority |
|-------|-------|----------|
| `code-reviewer` | General quality, logic, maintainability (>80% confidence filter) | Always |
| `python-reviewer` | PEP 8, type hints, security (runs: ruff, mypy, bandit) | Python files |
| `security-reviewer` | OWASP Top 10, secrets, injection, auth, SSRF | Auth/API/input code |
| `database-reviewer` | Query optimization, schema design, RLS, N+1 | DB changes |

Launch all applicable reviewers in parallel:
```
Agent: code-reviewer      (background)
Agent: python-reviewer    (background)
Agent: security-reviewer  (background)
```

### Step 5c: Simplify
```
Skill: simplify  OR  /simplify
Agent: code-simplifier (pr-review-toolkit)
```
- Review changed code for reuse opportunities
- Reduce complexity
- Remove dead code

### Step 5d: Address Findings
- Fix all CRITICAL and HIGH issues immediately
- Fix MEDIUM issues when possible
- Document any accepted LOW issues with rationale

### Receiving Review Feedback
```
Skill: superpowers:receiving-code-review
```
- Process feedback systematically
- Don't dismiss findings without investigation

---

## Phase 6: Verification

> **Rule:** Never mark a task complete without proving it works.

### Step 6a: Verification Loop
```
Skill: superpowers:verification-before-completion  OR  /verify
Skill: verification-loop
```

### Checklist
- [ ] All tests pass: `python -m pytest tests/ -v --tb=short`
- [ ] Coverage >= 80%
- [ ] No type errors (Pyright / TypeScript LSP)
- [ ] No security issues (semgrep scan)
- [ ] Behavior matches spec in `tasks/wireframes.md`
- [ ] API contract matches request/response shapes
- [ ] No hardcoded secrets or values
- [ ] Error handling comprehensive
- [ ] IDOR prevention verified (auth checks)
- [ ] "Would a staff engineer approve this?"

### Security Scan
```
Skill: security-scan
```
- Run semgrep against changed files
- Check for OWASP Top 10 vulnerabilities
- Verify no secrets in code

### E2E Testing (when applicable)
```
Agent: e2e-runner
MCP: Playwright (browser automation)
```
- Critical user flows
- Frontend + backend integration
- Screenshot/video artifacts

---

## Phase 7: Documentation

> Update docs AFTER verification, BEFORE commit.

### What to Update

| File | When |
|------|------|
| `tasks/todo.md` | Mark items complete, add review section |
| `tasks/lessons.md` | After ANY correction, mistake, or non-obvious fix |
| `CLAUDE.md` | If architecture, key files, or rules changed |
| `MEMORY.md` | Stable patterns confirmed across interactions |
| `README.md` | After milestone completion |

### Tools
```
Agent: doc-updater
Skill: documentation-workflow (for structured docs)
Skill: revise-claude-md  OR  /revise-claude-md (for CLAUDE.md updates)
```

---

## Phase 8: Git Operations

### Step 8a: Commit
```
Skill: /commit
```
- Stage specific files (never `git add -A` blindly)
- Conventional commit format: `<type>: <description>`
- Types: feat, fix, refactor, docs, test, chore, perf, ci

### Step 8b: Push & PR (when ready)
```
Skill: /commit-push-pr
Skill: superpowers:finishing-a-development-branch
```
- Analyze full commit history (not just latest)
- `git diff main...HEAD` for comprehensive PR summary
- Include test plan with TODOs
- Push with `-u` flag for new branches

### Hooks (automatic)
| Hook | What |
|------|------|
| `pre-bash-git-safety.sh` (PreToolUse) | Blocks force push, reset --hard |
| `post-edit-python-format.sh` (PostToolUse) | Auto-formats Python on edit |
| `stop-dotfiles-sync.sh` (Stop) | Syncs dotfiles on session end |

---

## Phase 9: Post-Feature

> After completing a feature, before moving to the next one or ending the session.

### Update Tracking
- Mark feature complete in `tasks/todo.md`
- Update `MEMORY.md` implementation status if significant

### Extract Learnings
```
Skill: /learn  OR  continuous-learning
```
- Extract reusable patterns from the feature work
- Update `tasks/lessons.md` with any corrections or non-obvious fixes

### Decide Next Action
- **More features this session?** → Return to Phase 1 for next feature
- **Milestone boundary?** → Go to [Milestone Checkpoints](#milestone-checkpoints)
- **Ending session?** → Follow [Session End Protocol](#session-continuity)

### Harness Optimization (periodic, every ~5 sessions)
```
Agent: harness-optimizer
```
- Review agent configuration for reliability and cost
- Optimize token usage patterns

---

## Special Flows

### Bug Fix Flow
```
Phase 1: superpowers:systematic-debugging  →  reproduce, hypothesize
Phase 2: /tdd  →  write regression test (RED)
Phase 3: Implement fix (GREEN)
Phase 4: code-reviewer + security-reviewer
Phase 5: /verify
Phase 6: /commit
```

### Large Feature Flow (multi-day)
```
Phase 1: superpowers:brainstorming
Phase 2: superpowers:writing-plans  →  detailed multi-phase plan
Phase 3: superpowers:using-git-worktrees  →  isolated branch
Phase 4: superpowers:subagent-driven-development  →  dispatch to subagents
Phase 5: Per-subunit: /tdd → build-fix → code-review → /verify
Phase 6: superpowers:finishing-a-development-branch  →  merge
Phase 7: /commit-push-pr
```

### Parallel Development Flow
```
Skill: superpowers:dispatching-parallel-agents
Launch N agents simultaneously:
  Agent 1: Backend route + tests
  Agent 2: Frontend component + tests
  Agent 3: Database migration
Merge results → /verify → /commit
```

### Refactoring Flow
```
Agent: refactor-cleaner  →  identify dead code
/tdd  →  ensure tests cover refactored area
Refactor  →  run tests after each change
/simplify  →  reduce complexity
/verify  →  full test suite
/commit
```

### Frontend Feature Flow
```
Research: Context7 (Next.js/React docs)
Plan: superpowers:brainstorming → /plan
Reference: frontend-patterns skill
Implement: /tdd with Jest tests
Visual: Playwright MCP for screenshot verification
Review: code-reviewer agent
Verify: /verify + E2E with e2e-runner agent
```

### Database Change Flow
```
Agent: database-reviewer  →  review schema design
Create migration: alembic revision --autogenerate
Reference: postgres-patterns skill
Test: SQLite compat patches (from lessons.md)
Review: database-reviewer agent
Verify: /verify
```

### Security-Critical Flow (auth, API, user input)
```
Reference: security-review skill BEFORE implementation
Implement with OWASP awareness
Agent: security-reviewer  →  post-implementation scan
Skill: security-scan  →  semgrep analysis
Verify: No injection, XSS, CSRF, IDOR
/commit
```

---

## Milestone Checkpoints

> Run at each milestone boundary (e.g., after completing an epic or before a demo/deadline).
> For ChainFactor AI: Milestone 1 (Day 8), Milestone 2 (Day 13), Milestone 3 (Day 16).

### Milestone Review Checklist

| # | Check | Tool | Pass Criteria |
|---|-------|------|---------------|
| 1 | All milestone features complete | `tasks/todo.md` | All items checked |
| 2 | Full test suite passes | `python -m pytest tests/ -v` | 0 failures |
| 3 | Coverage >= 80% | `python -m pytest --cov` | Branch + line coverage |
| 4 | No type errors | Pyright LSP / `npx tsc --noEmit` | 0 errors |
| 5 | Security scan clean | `/security-scan` + `security-reviewer` agent | No CRITICAL/HIGH |
| 6 | No hardcoded secrets | `semgrep` | Clean |
| 7 | API contracts match | Compare impl vs `tasks/wireframes.md` | All endpoints match |
| 8 | README.md updated | Manual | Reflects current state |
| 9 | Demo mode works | Test with `DEMO_MODE=true` | 3 test invoices pass |
| 10 | Retrospective | Update `tasks/lessons.md` | New learnings captured |

### Milestone Review Process
```
Step 1: Run full verification
  /verify

Step 2: Multi-agent review of ALL changes since last milestone
  git diff <last-milestone-tag>...HEAD
  Agent: code-reviewer    (background)
  Agent: security-reviewer (background)
  Agent: python-reviewer   (background)

Step 3: Update documentation
  Agent: doc-updater  →  update README, codemaps
  /revise-claude-md   →  update CLAUDE.md if architecture changed

Step 4: Tag the milestone
  git tag -a milestone-N -m "Milestone N: <description>"

Step 5: Retrospective
  /learn  →  extract patterns from this milestone
  Update tasks/lessons.md with what went well / what didn't
  Update MEMORY.md with confirmed stable patterns

Step 6: Plan next milestone
  Review tasks/todo.md  →  prioritize next batch
  superpowers:brainstorming  →  if architectural decisions needed
```

### Milestone Progress Tracking (in `tasks/todo.md`)

```markdown
## Milestone 1 (Day 8) — Core Pipeline
- [x] Feature list...
- Status: COMPLETE | IN PROGRESS | NOT STARTED
- Tag: milestone-1

## Milestone 2 (Day 13) — Blockchain + Frontend
- [ ] Feature list...
- Status: IN PROGRESS
```

---

## Deployment Workflow

> Per-milestone deployment or final release. Enable `terraform` + `deploy-on-aws` plugins first.

### Pre-Deployment Checklist

| # | Check | Command | Required |
|---|-------|---------|----------|
| 1 | All tests pass | `python -m pytest tests/ -v` | Yes |
| 2 | Security scan | `/security-scan` | Yes |
| 3 | No secrets in code | `git log --all -p \| grep -i "password\|secret\|key"` | Yes |
| 4 | Docker builds | `docker build -t chainfactor-backend ./backend` | Yes |
| 5 | Docker runs locally | `docker-compose up -d` + smoke test | Yes |
| 6 | Environment vars documented | Check `.env.example` is complete | Yes |
| 7 | Database migrations ready | `alembic upgrade head` on clean DB | Yes |
| 8 | Demo mode tested | `DEMO_MODE=true` + 3 test invoices | Yes |

### Deployment Process

```
Step 1: Enable deployment plugins (one-time)
  settings.json → enable: terraform, deploy-on-aws

Step 2: Infrastructure (Terraform)
  Skill: deployment-workflow
  Reference: terraform skill (when enabled)

  cd infra/terraform/backends/bootstrap && terraform init && terraform apply  # one-time
  cd infra/terraform/environments/staging && terraform init
  cd infra/terraform/environments/staging && terraform plan -var-file=terraform.tfvars
  cd infra/terraform/environments/staging && terraform apply -var-file=terraform.tfvars

Step 3: Build & Push Docker Images
  docker build -t chainfactor-backend ./backend
  # Tag and push to ECR
  aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>
  docker tag chainfactor-backend:latest <ecr-url>/chainfactor-backend:latest
  docker push <ecr-url>/chainfactor-backend:latest

Step 4: Deploy Backend (ECS Fargate)
  # Update ECS service to use new image
  aws ecs update-service --cluster chainfactor --service backend --force-new-deployment

Step 5: Deploy Frontend (S3 + CloudFront)
  cd frontend && npm run build && next export
  aws s3 sync out/ s3://chainfactor-frontend/ --delete
  aws cloudfront create-invalidation --distribution-id <id> --paths "/*"

Step 6: Database Migration (on first deploy or schema change)
  # Run alembic in ECS task or via bastion
  alembic upgrade head

Step 7: Smoke Test
  curl https://api.chainfactor.ai/health  →  {"status": "healthy"}
  # Test critical flows manually or via E2E
  Agent: e2e-runner  →  run critical path tests against staging
```

### Post-Deployment Verification
```
/verify  →  run against deployed environment
Agent: e2e-runner  →  critical user flows on staging URL
```

### Rollback Plan
```
# If deployment fails:
aws ecs update-service --cluster chainfactor --service backend --task-definition <previous-task-def>
# Or revert Terraform:
cd infra/terraform/environments/staging && terraform apply -var-file=terraform.tfvars -target=<resource>
```

---

## Post-Deployment & Monitoring

> After deployment, ensure the system stays healthy.

### Health Monitoring

| What | How | Frequency |
|------|-----|-----------|
| API health check | `GET /health` returns 200 | Continuous (ALB health check) |
| WebSocket connectivity | Test WS connection + message flow | After each deploy |
| Bedrock API quota | Check CloudWatch `ThrottlingException` | Daily |
| Database connections | RDS CloudWatch metrics | Continuous |
| Redis connectivity | ElastiCache CloudWatch | Continuous |
| Error rate | Application logs in CloudWatch | Continuous |

### Incident Response
```
Skill: incident-response
```
1. **Detect:** CloudWatch alarm or user report
2. **Triage:** Identify severity (P0-P3)
3. **Diagnose:** Check logs, metrics, recent deployments
4. **Fix:** Apply minimal fix or rollback
5. **Verify:** Confirm fix resolves the issue
6. **Post-mortem:** Update `tasks/lessons.md` with root cause and prevention

### Observability Setup (when needed)
```
Skill: observability-setup
```
- CloudWatch Logs for application logging
- CloudWatch Metrics for custom metrics (invoice processing time, agent latency)
- CloudWatch Alarms for error rate thresholds
- X-Ray tracing for request flow (optional, if debugging latency)

---

## Demo Preparation (Hackathon)

> Specific workflow for hackathon demo readiness. Run 1-2 days before demo.

### Demo Readiness Checklist

| # | Item | How to Verify | Status |
|---|------|---------------|--------|
| 1 | Demo mode works | `DEMO_MODE=true`, process 3 test invoices | |
| 2 | Invoice upload → processing → NFT mint (full flow) | End-to-end test via UI | |
| 3 | WebSocket trace streams in real-time | Watch browser console during processing | |
| 4 | NFT visible on Pera Explorer | Check `testnet.explorer.perawallet.app/asset/{id}` | |
| 5 | Wallet connect works (Pera/Defly) | Test on mobile + desktop | |
| 6 | Claim NFT flow works | Opt-in + receive ASA transfer | |
| 7 | Dashboard shows aggregated stats | Check /dashboard endpoint | |
| 8 | Error handling graceful | Test with invalid invoice, network failure | |
| 9 | Fallback plan ready | If Bedrock/Algorand down, demo mode kicks in | |
| 10 | Recording backup | Screen record a successful demo run | |

### Demo Preparation Process
```
Step 1: Test Demo Mode
  Set DEMO_MODE=true in environment
  Process each of the 3 pre-computed test invoices
  Verify WebSocket trace events stream correctly
  Verify NFT minting returns valid ASA ID

Step 2: Test Real Mode (if Bedrock + Algorand accessible)
  Set DEMO_MODE=false
  Upload a real test invoice (use sample from tasks/wireframes.md)
  Watch full pipeline: extract → validate → fraud → risk → underwrite → mint
  Verify NFT on Pera Explorer testnet

Step 3: E2E Smoke Test
  Agent: e2e-runner
  MCP: Playwright
  - Navigate to app
  - Connect wallet
  - Upload invoice
  - Watch processing
  - View result
  - Claim NFT

Step 4: Fallback Verification
  - Kill Bedrock access → verify DEMO_MODE fallback kicks in
  - Disconnect Algorand → verify mock NFT response
  - Network slow → verify timeout handling

Step 5: Rehearsal
  - Time the full demo flow (target: under 2 minutes)
  - Note any UI glitches or slow steps
  - Prepare talking points for each screen

Step 6: Screen Recording Backup
  - Record a successful full-flow demo
  - Save as fallback if live demo fails
```

### Pre-Demo Day Checklist
- [ ] Testnet wallet funded (10+ ALGO for MBR)
- [ ] Application wallet funded (fund via `algokit dispenser fund`)
- [ ] Bedrock quota sufficient (check RPM limits)
- [ ] Environment variables all set on deployed environment
- [ ] Demo invoices uploaded to S3
- [ ] Browser cache cleared, no stale state
- [ ] Backup screen recording ready

---

## Context Management

> Strategies for managing Claude Code's context window efficiently across long sessions.

### When to Use Each Strategy

| Situation | Strategy | Tool |
|-----------|----------|------|
| Starting a new session | Resume previous state | `/resume-session` |
| Completed a logical chunk | Save checkpoint | `/checkpoint` |
| Context getting large (80%+) | Compact suggestions | `strategic-compact` skill |
| Need deep research | Offload to subagent | Agent tool (Explore type) |
| Multiple independent tasks | Parallel subagents | `superpowers:dispatching-parallel-agents` |
| Ending session | Persist state | `/save-session` |
| Switching topics mid-session | Checkpoint first | `/checkpoint` then switch |

### Subagent Strategy (from CLAUDE.md global rules)
- Use subagents **liberally** to keep main context clean
- Offload research, exploration, and parallel analysis
- One task per subagent for focused execution
- For complex problems, throw more compute via parallel subagents

### Context-Expensive Operations (avoid in main context)
- Reading large files (>500 lines) → use Explore subagent
- Searching across many files → use Explore subagent
- Deep research (multi-source) → use `deep-research` skill via subagent
- Full codebase exploration → use Serena MCP for targeted symbol lookup instead

### Context-Cheap Operations (safe in main context)
- Single-file edits
- Running tests
- Reading specific functions (with Serena `find_symbol`)
- Git operations
- Simple Bash commands

---

## Plugin & MCP Reference

### Enabled Plugins (18)

| Plugin | Purpose | Used In |
|--------|---------|---------|
| superpowers | Core workflow skills (brainstorm, plan, TDD, verify, debug) | Phases 2-8 |
| everything-claude-code | 95+ skills, 20 agents, patterns, standards | All phases |
| learning-output-style | Educational insights during development | All phases |
| context7 | Library documentation lookup | Phase 1, 3 |
| serena | Semantic code analysis (symbols, refs) | Phase 1, 3 |
| firecrawl | Web scraping for research | Phase 1 |
| pyright-lsp | Python type checking | Phase 3, 6 |
| typescript-lsp | TypeScript type checking | Phase 3, 6 |
| playwright | Browser automation, E2E | Phase 6 |
| frontend-design | Frontend patterns, components | Phase 3 |
| code-review | Code review skills + agents | Phase 5 |
| code-simplifier | Reduce complexity | Phase 5 |
| feature-dev | Guided feature development | Phase 2, 3 |
| commit-commands | Git commit, push, PR | Phase 8 |
| pr-review-toolkit | PR review + analysis agents | Phase 5, 8 |
| claude-md-management | CLAUDE.md maintenance | Phase 7 |
| hookify | Hook creation and management | Setup |
| semgrep | Security scanning | Phase 6 |

### MCP Servers

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| Context7 | Library docs | `resolve-library-id`, `query-docs` |
| GitHub | Code search, PRs, issues | `search_code`, `create_pull_request` |
| Exa | Web search | `web_search_exa` |
| AWS Docs | AWS documentation | `search_documentation`, `read_documentation` |
| Playwright | Browser automation | `browser_navigate`, `browser_snapshot`, `browser_click` |
| Serena | Semantic code tools | `find_symbol`, `get_symbols_overview`, `replace_symbol_body` |
| SQLite | Database operations | `query`, `create_record` |

### Hooks (from settings.json)

| Type | Trigger | Action |
|------|---------|--------|
| SessionStart | Every session | Project detect + ECC update + Profile load |
| PreToolUse (Bash) | Before any Bash | Git safety (blocks force push, reset --hard) |
| PostToolUse (Edit/Write) | After .py edit | Auto-format with ruff |
| Stop | Session end | Dotfiles sync |

---

## Agent Roster

### Development Agents (use via Agent tool with `subagent_type`)

| Agent | Model | When to Use | Phase | Key Output |
|-------|-------|-------------|-------|------------|
| `planner` | Opus | Complex features, refactoring | 2 | Implementation steps with phases |
| `architect` | Opus | System design, scalability | 2 | Architecture diagrams, ADRs |
| `tdd-guide` | Sonnet | New features, bug fixes | 3 | Test suite, 80%+ coverage |
| `build-error-resolver` | Haiku | Build/test failures | 4 | Minimal error fixes |
| `code-reviewer` | Sonnet | After any code change | 5 | Review findings by severity |
| `python-reviewer` | Sonnet | Python file changes | 5 | PEP 8, type hints, security |
| `security-reviewer` | Sonnet | Auth, API, user input | 5, 6 | OWASP findings, remediation |
| `database-reviewer` | Sonnet | Schema, queries, migrations | 2, 5 | Query plans, schema advice |
| `e2e-runner` | Sonnet | Critical user flows | 6 | Test suite, screenshots, traces |
| `refactor-cleaner` | Sonnet | Dead code, consolidation | Special | Cleaned codebase |
| `doc-updater` | Haiku | Documentation updates | 7 | Codemaps, READMEs |
| `harness-optimizer` | Sonnet | Agent config tuning | 9 | Config improvements |

### Support Agents

| Agent | Model | When to Use |
|-------|-------|-------------|
| `chief-of-staff` | Opus | Communication triage |
| `loop-operator` | Sonnet | Autonomous loop management |
| Explore subagent | (inherits) | Codebase exploration |
| Plan subagent | (inherits) | Architecture planning |
| claude-code-guide | (inherits) | Claude Code help/questions |

---

## Slash Commands Cheat Sheet

| Command | What It Does | Phase |
|---------|-------------|-------|
| `/plan` | Restate requirements, plan approach | 2 |
| `/tdd` | Enforce test-driven development | 3 |
| `/verify` | Run verification loop | 6 |
| `/code-review` | Review code quality | 5 |
| `/simplify` | Simplify changed code | 5 |
| `/commit` | Create git commit | 8 |
| `/commit-push-pr` | Commit + push + open PR | 8 |
| `/review-pr` | Review a pull request | 5 |
| `/revise-claude-md` | Update CLAUDE.md | 7 |
| `/learn` | Extract reusable patterns | 9 |
| `/feature-dev` | Guided feature development | 2-3 |
| `/hookify` | Create automation hooks | Setup |
| `/checkpoint` | Save progress checkpoint | Any |
| `/save-session` | Save session state | Any |
| `/resume-session` | Resume saved session | Session start |
| `/e2e` | Generate and run E2E tests | 6 |
| `/python-review` | Python-specific review | 5 |
| `/security-scan` | Scan for vulnerabilities | 6 |
| `/update-docs` | Update documentation | 7 |
| `/build-fix` | Fix build errors | 4 |
| `/new-project` | Bootstrap new project scaffold | Bootstrap |
| `/harness-audit` | Audit agent harness config | Optimization |
| `/evolve` | Analyze and suggest instinct improvements | Post-session |
| `/promote` | Promote project instincts to global | Post-session |
| `/orchestrate` | Multi-agent parallel orchestration | Phase 3 |

---

## Superpowers Orchestration Flow

```
User Request
    |
[1] superpowers:brainstorming -------- explore options, identify trade-offs
    |
[2] superpowers:writing-plans -------- structured plan with phases + risks
    | (user confirms plan)
[3] superpowers:executing-plans ------ coordinate phases with checkpoints
    |--- superpowers:test-driven-development --- RED/GREEN/REFACTOR cycle
    |--- superpowers:subagent-driven-development --- dispatch to specialist agents
    |    \--- superpowers:dispatching-parallel-agents --- run agents simultaneously
    |--- superpowers:systematic-debugging --- (if failures occur, root cause analysis)
    |
[4] superpowers:requesting-code-review --- get structured feedback
    |
[5] superpowers:receiving-code-review ---- implement feedback, re-verify
    |
[6] superpowers:verification-before-completion --- 6-phase quality gate:
    |    Phase 1: Build verification
    |    Phase 2: Type checking (Pyright / tsc)
    |    Phase 3: Lint checking (ruff / eslint)
    |    Phase 4: Test suite (full coverage report, 80%+)
    |    Phase 5: Security scan (secrets, hardcoding, OWASP)
    |    Phase 6: Diff review (no unintended changes)
    |
[7] superpowers:finishing-a-development-branch --- PR summary, pre-flight, merge
    |
[8] superpowers:writing-skills --- capture reusable patterns (connects to /learn)
```

**Key insight:** Superpowers are workflow orchestrators that sit ON TOP of the agents, skills, and MCP tools. They sequence and parallelize the underlying components automatically.

---

## What's Automatic vs Manual

> Not everything in this pipeline requires you to type a command. Here's what fires
> on its own, what Claude does proactively, and what you must trigger.

### Layer 1: Fully Automatic (Hooks — zero human action)

| Action | Trigger | Hook |
|--------|---------|------|
| Python auto-format (ruff) | After any `.py` file edit | PostToolUse: `post-edit-python-format.sh` |
| Git safety block | Before destructive git commands | PreToolUse: `pre-bash-git-safety.sh` |
| Project type detection | Every session start | SessionStart: `session-start-project-detect.sh` |
| User profile loading | Every session start | SessionStart: Profile loader (Node inline) |
| ECC update check | Weekly at session start | SessionStart: `session-start-ecc-update-check.sh` |
| Dotfiles sync | Every session end | Stop: `stop-dotfiles-sync.sh` |

### Layer 2: Claude Does Proactively (no slash command needed)

These are triggered by instructions in `CLAUDE.md` and agent definitions. Claude invokes
them automatically when the context matches — you don't need to type anything.

| Action | When | What Claude Invokes |
|--------|------|-------------------|
| Brainstorming before planning | Before entering plan mode | `superpowers:brainstorming` skill |
| TDD enforcement | Before writing any feature code | `superpowers:test-driven-development` skill + `tdd-guide` agent |
| Code review | After writing or modifying code | `code-reviewer` + `python-reviewer` agents (parallel) |
| Security review | After auth/API/user-input code | `security-reviewer` agent |
| Build error resolution | When build or tests fail | `build-error-resolver` agent |
| Todo tracking | After completing a feature | Updates `tasks/todo.md` |
| Lessons capture | After any correction or mistake | Updates `tasks/lessons.md` |
| Context management | When context window is large | Suggests `/checkpoint` or offloads to subagents |
| Research before coding | Before new implementation | GitHub search → Context7 → Exa (Phase 1) |
| Read lessons at session start | Every session | Reads `tasks/lessons.md` for context |

### Layer 3: User-Triggered (slash commands — you decide when)

These affect shared state, are irreversible, or involve judgment calls about timing.
Claude will **suggest** them at the right moment but will **never fire them without asking**.

| Command | Why Manual |
|---------|-----------|
| `/commit` | Commits are permanent — you decide what/when to commit |
| `/commit-push-pr` | Pushes to remote, visible to team |
| `/plan` | You decide scope and depth of planning |
| `/verify` | You decide when to run the full quality gate |
| `/learn` | You decide when the session is ending |
| `/save-session` | You decide when to persist session state |
| `/resume-session` | You decide whether to resume previous state |
| `/security-scan` | Full scan is expensive — you trigger when ready |
| `/e2e` | E2E tests are slow — you trigger when ready |
| Deploy commands | Affects production, costs money |
| `git push`, `git tag` | Shared state — always needs your OK |
| Delete files/branches | Destructive — always needs your OK |

### How It Works In Practice

```
You: "Let's implement feature 4.10 — Invoice Processing Agent Assembly"

Claude automatically:
  1. Reads lessons.md + todo.md (session start)
  2. Invokes superpowers:brainstorming (before planning)
  3. Creates plan, asks you to confirm
  4. Writes tests first (TDD — automatic)
  5. Implements code
  6. Runs code-reviewer + python-reviewer (automatic after writing)
  7. Runs security-reviewer if auth code touched (automatic)
  8. Fixes any issues found
  9. Updates todo.md (automatic)

Claude suggests (you trigger):
  → "Ready for verification. Want me to run /verify?"
  → "All checks pass. Want me to /commit?"
  → "Should I /commit-push-pr for a PR?"
```

---

## Anti-Patterns (Don't Do This)

| Anti-Pattern | What To Do Instead |
|-------------|-------------------|
| Skip research, start coding | Phase 1 first: GitHub search → Context7 → Exa |
| Skip brainstorming, jump to plan | `superpowers:brainstorming` BEFORE `/plan` |
| Write code without tests | `/tdd` -- write test first (RED), then implement (GREEN) |
| Skip code review | `/code-review` after EVERY implementation |
| Self-declare "done" without verification | `/verify` with full checklist |
| Commit without security check | `security-reviewer` agent for auth/API code |
| Push without PR description | `/commit-push-pr` with full commit history analysis |
| Fix bugs without regression test | Write test first, THEN fix |
| Ignore lessons.md | Read at session start, update after corrections |
| Use Opus for everything | Sonnet for dev work, Opus only for NL query |
| Sequential when parallel is possible | `superpowers:dispatching-parallel-agents` |
| Large refactor without plan | `superpowers:brainstorming` → `/plan` → `refactor-cleaner` |
| End session without saving | `/save-session` + `/learn` + update todo.md |
| Start session cold | `/resume-session` first, then check todo.md + lessons.md |
| Skip milestone checkpoint | Run full review + tag before starting next milestone |
| Deploy without security scan | `/security-scan` + `security-reviewer` agent before deploy |
| Demo without rehearsal | Full demo prep checklist + screen recording backup |
| Let context window bloat | `/checkpoint` at breakpoints, offload to subagents |
| New project without artifacts | README.md + CLAUDE.md + .gitignore + tasks/ — IMMEDIATELY |

---

## ChainFactor AI - Project-Specific Notes

### Agent Model Assignments
- **Invoice Processing Agent**: Sonnet 4.6 (via Bedrock, us-east-1)
- **Underwriting Agent**: Sonnet 4.6 (NOT Opus)
- **NL Query Agent**: Opus 4.6 (on-demand only)
- **Collection Agent**: Haiku 4.5 (deferred to Round 3)

### Test Infrastructure
- Backend: `python -m pytest tests/ -v --tb=short`
- Frontend: `npm test` (Jest)
- E2E: `npx playwright test`
- SQLite compat patches in `conftest.py` (JSONB, UUID)

### Key Contracts
- API contracts: `tasks/wireframes.md`
- Architecture: `tasks/architecture-raw.md`
- Project plan: `tasks/project-plan.md`
- Lessons: `tasks/lessons.md`

### Current Feature Pipeline (Phase 8 - Feature Orchestration)
See `MEMORY.md` for implementation status and next features.
