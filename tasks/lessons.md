# ChainFactor AI - Lessons Learned

## Planning Phase (2026-03-17)

### Correction: Claude Agent SDK does NOT work with Bedrock
- **What happened:** Initially recommended Claude Agent SDK for agentic framework
- **Discovery:** Background research revealed it wraps the Claude CLI and requires direct Anthropic API key -- does NOT route through Bedrock
- **Fix:** Switched to Strands Agents SDK which is AWS-originated and defaults to Bedrock
- **Rule:** Always verify SDK compatibility with the target deployment platform (Bedrock vs direct API) before committing to a framework

### Research before committing
- Verified @txnlab/use-wallet-react is active (pushed daily, official Algorand wallet lib)
- Verified all Claude models (Opus 4.6, Sonnet 4.6, Haiku 4.5) available on Bedrock
- Verified Strands SDK supports: tool_use, streaming, multimodal, extended thinking, guardrails, caching
- **Rule:** Always run smoke tests on Day 1 to validate SDK + model compatibility

## Comprehensive Audit Phase (2026-03-18)

### CrewAI evaluated and REJECTED for this project
- **What happened:** Considered switching from Strands to CrewAI (Python-native, larger community)
- **Discovery (4-agent parallel research):**
  - CrewAI has NO native tool execution callbacks -- only streams LLM text chunks, not tool start/end events. This is a dealbreaker for our WebSocket real-time trace requirement.
  - CrewAI connects to Bedrock via LiteLLM (extra abstraction layer). LiteLLM has historically lagged behind Bedrock API updates for new models.
  - CrewAI has frequent breaking changes between versions (pre-1.0 was volatile, post-1.0 still breaking).
  - CrewAI does not expose Claude's extended thinking feature.
  - CrewAI's sequential process is less flexible than Strands Swarm for conditional handoffs (approve vs reject).
- **Fix:** Confirmed Strands Agents SDK as the right choice. It is an official AWS project (Apache 2.0, authors = AWS), has native `Swarm.stream_async()` for per-event real-time streaming, native Bedrock integration (no adapter layer), and BeforeToolCallEvent/AfterToolCallEvent hooks.
- **Rule:** For real-time streaming requirements, verify the framework supports per-tool-execution callbacks, not just LLM text streaming. This is a different feature.

### 5-agent architecture evaluated and REJECTED
- **What happened:** Considered expanding from 3 agents to 5 (adding GST Compliance Agent + QA Supervisor Agent)
- **Discovery:**
  - GST compliance is deterministic rules (HSN/SAC lookup, rate validation, format checks) -- no LLM reasoning needed. Using an agent for this is like using a neural network to add two numbers.
  - QA Supervisor (Opus) would cost ~$0.45 per invoice extra for cross-validation that the Underwriting Agent can do in its existing reasoning loop.
  - 5 agents: $0.90-1.50/invoice, 45-75s latency, 15-20% completion probability
  - 3 agents: $0.50-0.60/invoice, 25-43s latency, 80-90% completion probability
  - Each additional agent = ~25-35 extra dev hours for a 1-backend-dev team
- **Fix:** Keep 3 agents. Absorb GST compliance as a `validate_gst_compliance` tool on Invoice Agent. Fold QA cross-validation into Underwriting Agent's system prompt + `cross_validate_outputs` tool.
- **Rule:** An "agent" should only exist when it needs autonomous reasoning and dynamic decision-making. Deterministic checks belong as tools. Supervisor patterns should be folded into existing decision-making agents when the decider already has full context.

### Underwriting Agent: Sonnet, not Opus
- **What happened:** Initially assigned Opus 4.6 for underwriting decisions
- **Discovery:** Underwriting in our system is rule-based (check auto-approve thresholds, compare risk score to seller rules). Opus's deep reasoning is overkill -- Sonnet handles this well. Opus costs ~5x more per token.
- **Fix:** Sonnet for underwriting, Opus reserved for NL query only (low-volume, on-demand, actually needs deep reasoning)
- **Rule:** Match model tier to reasoning complexity. Rules-based decisions = Sonnet. Open-ended reasoning over unstructured data = Opus.

### AlgoExplorer is SHUT DOWN
- **What happened:** Referenced AlgoExplorer (testnet.algoexplorer.io) for viewing NFTs on-chain
- **Discovery:** AlgoExplorer has been shut down. Algorand's current block explorers are Pera Explorer (explorer.perawallet.app) and Allo (allo.info).
- **Fix:** All explorer references updated to Pera Explorer
- **Rule:** Always verify external service availability before committing to it in architecture docs

### ARC-69 metadata standard required for NFTs
- **Discovery:** ARC4 defines the smart contract interface, but NFT metadata needs a separate standard. ARC-69 (metadata in note field of latest acfg transaction) is simpler than ARC-19 and widely supported by Algorand explorers/marketplaces.
- **Fix:** Adopted ARC-69 for all invoice NFT metadata
- **Rule:** For Algorand NFTs, always specify the metadata standard (ARC-19 or ARC-69) separately from the contract standard (ARC4)

### ASA opt-in required for NFT ownership
- **Discovery:** Application wallet mints the NFT, but without ASA opt-in + transfer, the user never actually holds the NFT. This is a fundamental gap -- the user can see it on the explorer but doesn't own it.
- **Fix:** Added "Claim NFT" flow: user opts-in to the ASA, then application wallet transfers the NFT
- **Rule:** Algorand ASA transfers require the receiver to opt-in first. Always include the opt-in step in any ASA transfer flow.

### Strands SDK technical gotchas
- Session persistence NOT supported for Swarm agents yet -- use own PostgreSQL persistence
- Swarm agents do NOT share conversation history -- context must be passed explicitly via handoff
- `handoff_to_agent` is auto-injected as a reserved tool name -- do not use it for custom tools
- `@tool` decorator does NOT support `pydantic.Field` in `Annotated` -- use docstrings for parameter descriptions
- Default model is Bedrock Sonnet in us-west-2 if not specified -- always explicitly set model_id

### API Gateway WebSocket 29s hard timeout
- **Context:** In a previous project, API Gateway WebSocket had a 29-second hard idle timeout that caused issues
- **Fix:** Use ALB + Fargate direct for WebSocket connections. ALB supports up to 4000s idle timeout. Added SSE as fallback for environments where WebSocket is blocked.
- **Rule:** Never use API Gateway for WebSocket connections that need to stay open for more than 29 seconds. Use ALB or direct connections instead.

### Bedrock default RPM limits
- **Discovery:** Bedrock has per-model, per-region invocation quotas. Default for Sonnet on-demand is often 4-8 RPM.
- **Fix:** Request quota increase on Day 1 (takes 24-48 hours to process)
- **Rule:** Always check and request Bedrock quota increases BEFORE starting development, not at demo time

### Budget management for Bedrock
- **Discovery:** Opus costs ~5x Sonnet per token. Using Opus for every underwriting decision would cost $250+ for 500 test invoices alone, blowing the $200 budget.
- **Fix:** Sonnet for all pipeline agents, Opus only for low-volume NL query. Estimated cost: $109-144/month (down from $140-185).
- **Rule:** Always calculate per-invocation Bedrock costs early. Multiply by expected test volume + demo volume + debug retries. Add 50% buffer.

## Framework Deep Evaluation Phase (2026-03-18)

### AutoGen evaluated and REJECTED for this project
- **What happened:** Considered Microsoft AutoGen (v0.4+, currently v0.7.5) as alternative to Strands
- **Discovery:**
  - CRITICAL: There are TWO incompatible projects called "AutoGen" -- microsoft/autogen (v0.4+, MIT) and ag2ai/ag2 (forked from v0.2, Apache 2.0). They have different APIs, packages, and architectures. Must use microsoft/autogen for current features.
  - AutoGen is conversation-based, not pipeline-based. ALL agents share the full message thread. Our Invoice Agent's raw OCR data, fraud check details, etc. would all be visible to the Underwriting Agent, wasting tokens and potentially confusing the model.
  - Bedrock integration is indirect (via anthropic SDK's AsyncAnthropicBedrock, not native boto3).
  - Tool callbacks are coarse-grained (ToolCallRequestEvent/ToolCallExecutionEvent) -- no in-progress events during tool execution. For WebSocket streaming, we'd need custom wrappers.
  - Requires 3 separate packages: autogen-agentchat + autogen-core + autogen-ext.
  - Uses tiktoken (OpenAI's tokenizer) for token counting on Claude models -- inaccurate.
  - AG2 fork (v0.2 lineage) has NO streaming support with Bedrock at all -- explicitly disabled in source code.
- **Rule:** AutoGen is designed for multi-agent conversations (debate, collaboration). For sequential pipelines with structured handoffs, use a pipeline-oriented framework. Conversation-based models waste tokens when agents don't need to see each other's full history.

### LangGraph evaluated and REJECTED for this project
- **What happened:** Considered LangGraph (by LangChain) as alternative to Strands
- **Discovery:**
  - LangGraph has the BEST streaming of all frameworks -- 4 modes (values, updates, custom, messages) including `get_stream_writer()` for pushing custom events from inside tools. This is genuinely excellent.
  - LangGraph has built-in PostgreSQL checkpointing (AsyncPostgresSaver) -- durable execution, resume from failure. Also excellent.
  - BUT: Bedrock integration is indirect via langchain-aws package. No Bedrock-specific examples in the LangGraph repo (all examples use OpenAI). Less community-tested for Bedrock.
  - Tools require node functions (verbose) instead of simple `@tool` decorators.
  - Graph abstraction (StateGraph, nodes, edges, state TypedDict with reducers, compile step) adds boilerplate for what is fundamentally a 2-agent sequential pipeline.
  - Requires langchain-core + 4 sub-packages as dependencies.
  - LangGraph Platform (managed hosting) is paid -- but the open-source core (MIT) is all we need.
- **LangGraph's sweet spot:** Complex branching workflows, human-in-the-loop approval gates, parallel agent execution, long-running durable workflows. Not a 2-agent sequential pipeline.
- **Rule:** Match framework complexity to pipeline complexity. For sequential agent pipelines with structured handoffs, a lightweight SDK (Strands) beats a graph engine (LangGraph). Save LangGraph for when you actually need graph-level orchestration.

### The "agent vs tool" decision framework
- **Discovery:** Through evaluating 5-agent, 3-agent, and various framework options, a clear pattern emerged for when something should be an agent vs a tool.
- **Agent criteria (ALL must apply):**
  1. Requires LLM reasoning (not deterministic rules)
  2. Has dynamic decision-making (multiple valid paths)
  3. Benefits from natural language interpretation of ambiguous inputs
  4. Orchestrates multiple tools based on context
- **Tool criteria (ANY applies):**
  1. Deterministic logic (lookup table, math, format check)
  2. Single API call with fixed response handling
  3. Same input always produces same output
  4. Can be written as a Python function in <100 lines
- **Examples from our project:**
  - GST compliance (HSN/SAC lookup, rate validation) = TOOL (deterministic rules)
  - QA cross-validation (consistency checks) = TOOL on Underwriting Agent
  - Risk calculation = TOOL but agent interprets the result (hybrid)
  - Underwriting decision = AGENT (weighs multiple signals, applies judgment)
  - Invoice data extraction = TOOL (Textract) but agent interprets ambiguous fields
- **Rule:** If you can write it as a deterministic Python function, it's a tool. If it requires judgment, it's an agent. When in doubt, start as a tool -- you can always promote it to an agent later.

### 4-framework comparison completed
- Evaluated: Strands Agents SDK, CrewAI, LangGraph, AutoGen
- **Winner: Strands Agents SDK** for our specific requirements:
  - Native Bedrock integration (zero abstraction layers) -- only framework built by AWS
  - Per-tool WebSocket streaming via BeforeToolCallEvent/AfterToolCallEvent hooks
  - Pipeline-oriented Swarm with isolated agent contexts + structured handoffs
  - Simple `@tool` decorator (fastest development velocity for hackathon)
  - Lightweight dependency footprint (boto3 + core SDK)
- **Rule:** Framework selection criteria for Bedrock-first projects: (1) native Bedrock support, (2) tool-level callbacks for real-time streaming, (3) pipeline vs conversation model match, (4) development velocity for timeline constraints

## Algorand Stack Verification Phase (2026-03-18)

### AlgoKit version: 2.x (NOT 3.0)
- **What happened:** All project docs referenced "AlgoKit 3.0" as if it existed
- **Discovery:** The latest AlgoKit CLI version is 2.10.2. There is no AlgoKit 3.0.
- **Fix:** Replaced all references with "AlgoKit 2.x" across project-plan.md, team-brief.md, CLAUDE.md
- **Rule:** Always verify actual released versions of tools before committing to them in docs. Use `pip index versions` or `npm view` to check.

### Algorand Python SDK versions confirmed
- **Backend (py-algorand-sdk):** v2.11.1 on PyPI, import as `algosdk`. Testnet endpoint: `https://testnet-api.algonode.cloud` (free, no token needed).
- **Frontend (algosdk JS):** v3.x, used by @txnlab/use-wallet-react v4.6.0. Breaking change from v2: transaction signing API changed.
- **Smart contract (algorand-python):** v3.5.0, import as `algopy`. Compiler: `puyapy` v5.8.0. Extend `ARC4Contract`, use `@arc4.abimethod`.
- **Rule:** Pin SDK versions in requirements.txt and package.json from Day 1. Algorand ecosystem moves fast.

### Pera Wallet is NOT MyAlgo
- **What happened:** Early CLAUDE.md draft said "Pera Wallet (formerly MyAlgo)"
- **Discovery:** Pera and MyAlgo are completely different wallets by different teams. MyAlgo (by Rand Labs) is shut down. Pera (by Pera team) is the active primary wallet.
- **Fix:** Corrected in CLAUDE.md Known Gotchas
- **Rule:** Never conflate Algorand wallets. Pera, Defly, MyAlgo, and Lute are all separate products.

### ARC-69 metadata: superseded but still widely supported
- **Discovery:** ARC-69 has been technically superseded by ARC-89 (Digital Media Standard), but ARC-69 remains the most widely supported standard by Algorand explorers and marketplaces. For a hackathon, ARC-69 is the safer choice.
- **Rule:** Use ARC-69 for hackathon NFTs. Consider ARC-89 for production if broader metadata is needed.

### Static export (next export) with use-wallet-react: UNVERIFIED
- **What happened:** Architecture assumes Next.js static export (next export -> S3 + CloudFront)
- **Discovery:** @txnlab/use-wallet-react uses React context providers that require client-side rendering. Static export should work since wallet interactions are client-side, but this has NOT been verified in a real build.
- **Fallback:** If static export fails, switch to Amplify Hosting (SSR support, still free tier)
- **Rule:** Test static export compatibility with wallet libraries on Day 1. Don't wait until deployment day.

### ASA opt-in costs and MBR
- **Discovery:** Each ASA opt-in costs the user 0.1 ALGO MBR (Minimum Balance Requirement). The application wallet also needs 0.1 ALGO base + 0.1 ALGO per ASA it creates. Fund the application wallet with 10+ ALGO from testnet faucet on Day 1.
- **Rule:** Always pre-fund application wallets on testnet before testing NFT minting. Budget for user MBR in the UX (show "this will require 0.1 ALGO" before opt-in).

### Testnet endpoints: use Algonode (free, no token)
- **Discovery:** Algorand testnet endpoints via Algonode are free and require no API token:
  - Algod: `https://testnet-api.algonode.cloud`
  - Indexer: `https://testnet-idx.algonode.cloud`
  - Previous endpoints (PureStake, AlgoExplorer API) are deprecated or shut down.
- **Rule:** Always use Algonode endpoints for testnet. For mainnet, consider Nodely or run your own node.

## Development Methodology (2026-03-18)

### Skeleton-first (wireframe method) development adopted
- **What it is:** Build all pages (frontend) and API endpoints (backend) as stubs/skeletons first with placeholder/hardcoded data. Then fill in real logic in a second pass.
- **Why:** Frontend doesn't wait for backend. API contracts are agreed upfront. Demo mode is built-in from day 1. Integration is smooth because both sides code against the same contract.
- **How we apply it:**
  - Pass 1: Backend returns hardcoded stub responses matching the API contract. Frontend builds UI against stubs.
  - Pass 2: Backend replaces stubs with real logic (DB, agents, S3). Frontend swaps data source.
- **Artifacts:** `tasks/wireframes.md` contains ASCII wireframes for all screens + full API contracts (request/response shapes).
- **Rule:** Always define the API contract (request body, response shape, status codes) BEFORE implementing either side. Both frontend and backend build against the contract independently.

### Region split: ap-south-1 (Mumbai) + us-east-1 (Bedrock only)
- **Decision:** All AWS services (RDS, ElastiCache, S3, ECS, Cognito, CloudFront, Secrets Manager) run in ap-south-1 (Mumbai) for lowest latency to Indian users. Bedrock stays in us-east-1 because Bedrock model availability varies by region.
- **Impact:** Bedrock calls are cross-region (ap-south-1 -> us-east-1), adding ~50-80ms latency per call. Acceptable for agent tools (not user-facing latency-sensitive).
- **Config:** `AWS_REGION=ap-south-1` (all services), `BEDROCK_REGION=us-east-1` (AI models only). Terraform defaults to ap-south-1.
- **Rule:** Never hardcode us-east-1 as the default region. Always use ap-south-1 except for Bedrock.

### Docker best practices: multi-stage builds
- **Backend:** 2-stage build (builder with gcc/libpq-dev -> runtime with only libpq5). Non-root user, healthcheck, .dockerignore.
- **Frontend:** 3-stage (deps -> development for docker-compose -> production static export for S3). Non-root user, .dockerignore.
- **Rule:** Always use multi-stage Docker builds. Never ship build tools (gcc, node devDeps) in runtime images. Always run as non-root user.

### SQLAlchemy: "metadata" is a reserved attribute name
- **What happened:** Named an NFT model column `metadata` -- SQLAlchemy raised `InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API`.
- **Fix:** Renamed to `arc69_metadata`.
- **Rule:** Never use `metadata`, `registry`, or `__tablename__` as column names in SQLAlchemy models. These are reserved by DeclarativeBase.
