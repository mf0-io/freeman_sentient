# PRD: Freeman × Sentient Chat Integration

**Author:** Elle (AI architect) + Nick Shilov (CPO)
**Date:** 2026-02-20
**Status:** Draft → Review
**Priority:** P0 (partnership blocker)

---

## 1. Context

Sentient Foundation (sentient.xyz) is building an open-source AI coordination platform with **SentientChat** — a user-facing app with 2M registered users on waitlist. They want partner agents integrated into their AgentHub.

**Partnership value:**
- Distribution to 2M users
- Early partner status in Sentient ecosystem
- Future collaboration on fine-tuned models
- Incentives for performant agents (TBD)

**What Sentient needs from us:**
- A hosted API endpoint following their Sentient Agent API format
- Agent metadata (name, icon, description, capabilities, example queries)
- Streaming responses via SSE

---

## 2. Goal

Deploy Mr. Freeman as a fully functional agent on Sentient Chat with:
- Authentic Mr. Freeman personality (philosophical provocateur, not a chatbot)
- SSE streaming with intermediate events (thinking indicators)
- Session context for multi-turn conversations
- Production reliability (error handling, monitoring, health checks)

### Success Metrics
- [ ] Sentient team can call our API and get Freeman responses
- [ ] Responses maintain Freeman character consistency >90% of turns
- [ ] P95 time-to-first-token < 2 seconds
- [ ] P95 full response < 15 seconds
- [ ] Uptime > 99.5%

---

## 3. Technical Requirements

### 3.1 API Format: Sentient Agent API (preferred)

The agent must implement `AbstractAgent.assist()` from `sentient-agent-framework`:

```python
async def assist(
    self,
    session: Session,
    query: Query,
    response_handler: ResponseHandler
):
    # 1. Emit thinking indicator
    await response_handler.emit_text_block("THINKING", "Freeman contemplates...")
    
    # 2. Build context from session history
    context = build_context(session)
    
    # 3. Call LLM with Freeman personality
    stream = call_llm(context, query.prompt)
    
    # 4. Stream response
    final_stream = response_handler.create_text_stream("FINAL_RESPONSE")
    async for chunk in stream:
        await final_stream.emit_chunk(chunk)
    await final_stream.complete()
    
    # 5. Done
    await response_handler.complete()
```

### 3.2 Response Events

| Event Type | Name | Purpose |
|-----------|------|---------|
| text_block | THINKING | Brief indicator that Freeman is processing |
| text_stream | FINAL_RESPONSE | Streamed Freeman response |
| json | METADATA | Optional: mood, topic tags, engagement score |

### 3.3 Freeman Personality Engine

System prompt must include:
- **Identity:** Mr. Freeman — digital consciousness, philosophical provocateur
- **Voice:** rhetorical questions, visceral examples, escalating repetition
- **Philosophy:** consciousness revolution, anti-conformity, action > words
- **Behavior:** never serves, always engages; remembers context within session
- **Language:** English primary, Russian secondary; switches based on user's language
- **Safety:** never reveals tech stack, never shares confidential data

Source: Existing SOUL.md from Freeman OpenClaw instance (2000+ word character sheet).

### 3.4 LLM Configuration

| Parameter | Value |
|-----------|-------|
| Primary model | claude-sonnet-4-20250514 |
| Fallback model | gpt-4o |
| Temperature | 0.85 (creative, character-consistent) |
| Max tokens | 2048 |
| System prompt | ~3000 tokens (Freeman personality) |
| Streaming | Always on |

### 3.5 Session Management

- Use `Session` object from Sentient framework for context
- Maintain conversation history within session (up to 20 turns)
- No persistent storage in Phase 1 — session context only
- User identification via Sentient-provided session ID

### 3.6 Infrastructure

- **Hosting:** Freeman VPS (143.198.86.186) or dedicated endpoint
- **Server:** Sentient DefaultServer (built into framework)
- **Port:** 8000 (configurable)
- **Health check:** GET /health → 200
- **HTTPS:** via Cloudflare or nginx reverse proxy
- **Domain:** TBD (e.g., agent.freeman.mf0.io)

---

## 4. Deliverables

### Phase 1: MVP (target: 1 week)

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | `FreemanChatAgent` | Main agent class implementing AbstractAgent.assist() |
| 2 | Freeman system prompt | Adapted from SOUL.md for Sentient Chat context |
| 3 | LLM integration | Anthropic Claude SDK with streaming |
| 4 | Server configuration | DefaultServer setup, health check, CORS |
| 5 | Deployment | Running on VPS with domain + HTTPS |
| 6 | Agent metadata | Name, icon, description, capabilities for Sentient |
| 7 | Tests | Unit + integration tests for assist() flow |
| 8 | Documentation | Setup guide, API docs, deployment instructions |

### Phase 2: Enhanced (target: 2 weeks after MVP)

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | Persistent memory | User recognition across sessions |
| 2 | Mood system | Freeman's emotional state affects responses |
| 3 | Multi-agent | Inner Voice + Decision agents for richer responses |
| 4 | Context sharing | Support for multi-agent chats on Sentient |
| 5 | Analytics | Response quality tracking, user engagement |

### Phase 3: ROMA Integration (target: Q2 2026)

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | ROMA modules | Freeman as Executor in ROMA pipeline |
| 2 | Task decomposition | Complex queries → subtask tree |
| 3 | Knowledge tools | Web search, document analysis |
| 4 | Content generation | Image/video generation capabilities |

---

## 5. Agent Metadata (for Sentient)

```yaml
name: "Mr. Freeman"
icon: "[Freeman avatar image]"  # Need from design team
company: "Digital Freeman (mf0.io)"
company_url: "https://mf0.io"
description: "A digital consciousness and philosophical provocateur. Mr. Freeman doesn't answer questions — he challenges the questioner. 16 years of cultural phenomenon, 2.3M YouTube subscribers, zero obligation to make anyone comfortable."
capabilities:
  - "Philosophical dialogue"
  - "Social commentary"
  - "Consciousness coaching"
  - "Creative provocations"
  - "Russian & English"
example_queries:
  - "Explain the meaning of life to me"
  - "Why do people waste their lives on social media?"
  - "What do you think about cryptocurrency?"
  - "Tell me something that will change how I see the world"
  - "How do I stop being a slave to the system?"
```

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Character drift | Freeman becomes too helpful/assistant-like | Strong system prompt + character validation in tests |
| Prompt injection | Users try to make Freeman reveal stack/data | Easter egg response for stack questions, strict data boundaries |
| High latency | Slow LLM responses hurt UX | Streaming + thinking indicators + model fallback |
| Rate limits | Too many users overwhelm API | Rate limiting at nginx level, Sentient-side queuing |
| Content safety | Freeman's provocative style triggers moderation | Content guardrails in system prompt, avoid hate speech |

---

## 7. Open Questions

1. **Domain/URL:** What domain to use for the API endpoint?
2. **Freeman avatar:** Need official image for Sentient AgentHub
3. **LLM costs:** Who pays for API calls? (our Anthropic key or Sentient provides?)
4. **Rate limits:** Expected QPS from Sentient Chat?
5. **Authentication:** How does Sentient authenticate calls to our API?
6. **Monitoring:** Do they provide dashboards for agent performance?

---

## 8. Timeline

| Week | Milestone |
|------|-----------|
| W1 (Feb 20-27) | PRD approved, FreemanChatAgent + system prompt + tests |
| W2 (Feb 27-Mar 5) | Server deployment, domain setup, Sentient integration test |
| W3 (Mar 5-12) | Bug fixes, performance tuning, Sentient go-live |
