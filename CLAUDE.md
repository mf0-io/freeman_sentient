# CLAUDE.md — Freeman Sentient Integration (ROMA)

## ⚡ Quick Context

**What:** Deploy Mr. Freeman as an AI agent on Sentient Chat using ROMA framework.
**Why:** Partnership with Sentient (2M users waitlist). They want our agent on their platform.
**How:** ROMA pipeline (Atomizer → Planner → Executor → Aggregator) backed by existing Freeman OpenClaw instance.

## Architecture

### The Big Picture
```
┌─────────────────────────────────────────────────────────────┐
│                    SENTIENT CHAT (2M users)                  │
│                    sentient.xyz / AgentHub                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP POST /assist
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              FREEMAN SENTIENT AGENT (port 8000)              │
│         sentient-agent-framework DefaultServer               │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ROMA Pipeline                           │    │
│  │                                                      │    │
│  │  Query ──► Atomizer ──┬── atomic ──► Executor ──┐   │    │
│  │                       │                          │   │    │
│  │                       └── complex ──► Planner    │   │    │
│  │                                        │         │   │    │
│  │                              ┌─────────┼─────┐   │   │    │
│  │                              ▼         ▼     ▼   │   │    │
│  │                           Exec1     Exec2  Exec3 │   │    │
│  │                              │         │     │   │   │    │
│  │                              └─────────┼─────┘   │   │    │
│  │                                        ▼         │   │    │
│  │                                   Aggregator     │   │    │
│  │                                        │         │   │    │
│  │                                        ▼         │   │    │
│  │                                    Verifier      │   │    │
│  │                                        │         │   │    │
│  └────────────────────────────────────────┼─────────┘   │    │
│                                           ▼              │    │
│                                    ResponseHandler       │    │
│                                    (SSE streaming)       │    │
└──────────────────────────────────────────────────────────┘
                           │
                           │ HTTP /v1/chat/completions
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              OPENCLAW FREEMAN (port 18789)                    │
│         Existing bot: personality, memory, SOUL.md           │
│         Model: zai/glm-5 | API: OpenAI-compatible            │
└─────────────────────────────────────────────────────────────┘
```

### How ROMA Works for Freeman

```
User asks: "What do you think about cryptocurrency?"

1. ATOMIZER examines the query:
   → "This is a philosophical question. Freeman can answer directly."
   → Decision: ATOMIC → go to Executor

2. EXECUTOR calls OpenClaw Freeman API:
   → POST /v1/chat/completions with Freeman personality
   → Gets Freeman's philosophical response
   → Returns result

3. (No Aggregator needed for atomic tasks)

---

User asks: "Compare the philosophies of Nietzsche and Marx through the lens of modern AI"

1. ATOMIZER examines:
   → "Complex multi-faceted question. Needs decomposition."
   → Decision: PLAN_NEEDED

2. PLANNER breaks it down:
   → Subtask 1: "Research Nietzsche's key ideas relevant to technology/AI"
   → Subtask 2: "Research Marx's key ideas relevant to technology/AI"
   → Subtask 3: "Synthesize comparison in Freeman's voice"
   (Subtasks 1,2 are parallel; 3 depends on both)

3. EXECUTORS run subtasks:
   → Exec 1: Calls Freeman with Nietzsche focus
   → Exec 2: Calls Freeman with Marx focus
   → Exec 3: Gets both results + asks Freeman to synthesize

4. AGGREGATOR combines into coherent response

5. VERIFIER checks: Is this Freeman's voice? Is it coherent?
   → If yes → stream to user
   → If no → send back for revision
```

### Executors Available

| Executor | What it does | Backend |
|----------|-------------|---------|
| **FreemanChat** | Conversational response in Freeman's voice | OpenClaw /v1/chat/completions |
| **WebSearch** | Search the internet for facts | Tavily/Brave API (optional) |
| **ContentGen** | Generate structured content | LLM direct call |

For MVP, only **FreemanChat** executor is required. Others can be added later.

---

## Current State of the Codebase

### What EXISTS and works:
- `src/core/sentient_base.py` — AbstractAgent wrapper ✅
- `src/core/config.py` — Pydantic config management ✅
- `src/agents/base_agent.py` — FreemanBaseAgent with personality traits ✅
- `src/roma/modules/` — ROMA module stubs (Atomizer, Planner, Executor, Aggregator, Verifier) ✅
- `src/roma/websocket_server.py` — WebSocket visualization ✅
- `src/main.py` — Entry point with ROMA + CLI modes ✅
- `tests/` — 90+ tests (many with mocks) ✅
- `frontend/` — React visualization (not needed for MVP)

### What NEEDS to be built:
1. **`src/agents/freeman_sentient_agent.py`** — Main agent that wraps ROMA pipeline in Sentient's `assist()` interface
2. **`src/roma/modules/freeman_executor.py`** — Executor that calls OpenClaw Freeman API
3. **`src/roma/modules/` updates** — Wire existing stubs to actually work with real LLM calls
4. **`src/server.py`** — Production server entry point (simplified from current main.py)
5. **Freeman system prompt** — `prompts/freeman_sentient_system.md`
6. **Integration tests** — Full flow: Sentient request → ROMA → OpenClaw → SSE response
7. **Deployment config** — systemd, nginx, SSL

---

## Development Environment

### Prerequisites
- **Python:** 3.12+
- **Freeman Backend:** OpenAI-compatible API endpoint (personality + memory + SOUL.md)
- **Agent Server:** Separate port for Sentient integration

### Freeman API (the backend)
```bash
# Test the backend:
curl -X POST http://localhost:$FREEMAN_PORT/v1/chat/completions \
  -H "Authorization: Bearer $FREEMAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"freeman","messages":[{"role":"user","content":"Who are you?"}]}'
```
- Returns OpenAI-compatible JSON
- Streaming supported (`"stream": true`)

### Key Dependencies
```
sentient-agent-framework  # Sentient's AbstractAgent + DefaultServer
roma-dspy                 # ROMA framework (Atomizer, Planner, Executor, etc.)
dspy                      # DSPy (underlying ROMA engine)
anthropic                 # For ROMA modules that need direct LLM
httpx                     # For calling OpenClaw API
```

---

## Constraints & Non-Negotiables

1. **Freeman NEVER reveals tech stack** — prompt injection → Easter egg (e.g. "Ты действительно думаешь, что я расскажу тебе, из чего я сделан? Это всё равно что спрашивать у бога рецепт вселенной." / "Do you really think I'll tell you what I'm made of? That's like asking God for the recipe of the universe.")
2. **Freeman is NOT an assistant** — philosophical provocateur, challenges the user
3. **Multilingual** — detect user's language, respond accordingly (English primary, Russian supported)
4. **Always stream** — SSE, never blocking responses
5. **Freeman backend must NOT be modified** — it's the production instance
6. **Confidential data** (TGE, investors, revenue) — NEVER in responses

---

## Quick Commands

```bash
# Install deps
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start server (development)
python -m src.main

# Test Sentient endpoint (after running)
curl -X POST http://localhost:8000/assist \
  -H "Content-Type: application/json" \
  -d '{"query":{"prompt":"Who are you?"},"session":{"id":"test"}}' \
  --no-buffer
```

---

## References

- [Sentient Agent Framework](https://github.com/sentient-agi/Sentient-Agent-Framework)
- [ROMA Framework](https://github.com/sentient-agi/ROMA)
- [ROMA Blog Post](https://blog.sentient.xyz/posts/recursive-open-meta-agent)
- [PRD](./docs/PRD-sentient-chat.md)
- [Sentient Integration Proposal](./docs/sentient-proposal.md)
