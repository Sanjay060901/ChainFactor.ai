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
