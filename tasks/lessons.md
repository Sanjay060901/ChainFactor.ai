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
