# Sentient Chat Integration Proposal (from Sentient)

## Technical Requirements

Your agent must be hosted and exposed through one of three interfaces:

1. **Sentient Agent API** (preferred) — rich set of intermediate events, context-sharing between agents
2. **OpenAI Chat Completions API** — flexible but no intermediate events
3. **OpenAI Completions API** (legacy) — simple, no context sharing

Streaming is highly recommended regardless of format.

## What Sentient Needs From Us

### Phase 1: Agent Listing
1. Name of the agent
2. Agent icon/image
3. Name of company + link
4. Short description (1-2 sentences)
5. List of capabilities (1-2 words each)
6. Example queries showcasing complex capabilities

### Phase 2: Technical Integration
- Exchange API keys and documentation
- Implement UI and complete integration

## Our Implementation Choice

**Sentient Agent API** (option 1) — gives richest UX with intermediate events showing ROMA's thinking process.

Contact: roko@sentient.xyz
