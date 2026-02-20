# Freeman Sentient

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-90%2B_passing-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Memory](https://img.shields.io/badge/memory-3_layer-purple)
![Agents](https://img.shields.io/badge/agents-ROMA_pipeline-orange)

### Autonomous self-improving multi-agent framework with 3-layer memory, multi-LLM intelligence, and ecosystem awareness

> A fully autonomous AI agent that researches, remembers, reasons, audits itself, and evolves across sessions. Not a chatbot with context — a persistent digital consciousness that gets smarter every day.

---

## The Problem

AI agents wake up with amnesia every session. They repeat mistakes, forget corrections, lose relationship context. Scale this to multiple agents and the problem multiplies: tell one agent "no emojis" — the other five don't know. Every session starts from zero.

Freeman Sentient solves this with a **3-layer memory architecture** that gives agents persistent identity, emotional awareness, and cross-session learning.

---

## 3-Layer Memory Architecture

```
+------------------------------------------------------------------+
|  LAYER 1: Working Memory (loaded at every agent startup)         |
|                                                                  |
|  Personality + Knowledge + Rules                                 |
|  SOUL.md / agent config / persona definitions                    |
|  The foundation of WHO the agent IS                              |
+------------------------------------------------------------------+
          |
          v
+------------------------------------------------------------------+
|  LAYER 2: Session Memory (active during conversations)           |
|                                                                  |
|  Emotional state | Conversation context | Action tracking        |
|  Real-time mood transitions | Topic threading                    |
|  Auto-compaction when context exceeds threshold                  |
+------------------------------------------------------------------+
          |
          v  distill + consolidate
+------------------------------------------------------------------+
|  LAYER 3: Long-Term Memory (persists across sessions)            |
|                                                                  |
|  Graphiti Knowledge Graph | User relationship profiles           |
|  Semantic + Episodic + Procedural consolidation                  |
|  Cross-agent propagation of corrections and learnings            |
+------------------------------------------------------------------+
```

### Layer 1: Working Memory

Loaded at startup. Defines who the agent is and how it behaves.

- **Personality framework** — 400+ lines of voice calibration, rhetorical patterns, philosophical positions
- **Behavioral constraints** — Interaction rules, content boundaries, anti-patterns, crisis protocols
- **Persona definitions** — Multi-persona support with YAML configs and isolated contexts
- **Base knowledge** — 16 years of cultural content (60+ monologues, 2.3M YouTube subscribers)

### Layer 2: Session Memory

Ephemeral. Tracks everything happening in real-time.

| Module | What it tracks |
|--------|---------------|
| `emotional_memory` | Current mood, emotional transitions, sentiment per message |
| `conversation_memory` | Active dialog context, topic positions, important statements |
| `action_memory` | What the agent did, user reactions, weighted engagement scores |
| `emotional_state` | State machine with mood transitions (calm, provocative, philosophical, etc.) |

Session memory auto-compacts when approaching token limits. Important facts get distilled to Layer 3.

### Layer 3: Long-Term Memory

Survives sessions. The agent's accumulated wisdom.

- **Graphiti Knowledge Graph** — Structured entity storage with semantic search (Qdrant vectors)
- **Relationship Memory** — User profiles, trust levels, interaction history spanning months
- **Memory Consolidation** — Periodic distillation into three categories:
  - **Semantic** — Facts and knowledge ("User X is a developer")
  - **Episodic** — Key events ("Launched product on March 5")
  - **Procedural** — Patterns and processes ("When user asks about crypto, redirect to philosophy")
- **Cross-agent propagation** — Corrections flow from one agent to all others automatically

### How a single correction propagates

```
You tell Agent A: "never use emojis in tweets"
     |
     v
Session Memory captures the correction
     |
     v
Memory Manager distills to MEMORY.md (BAD section)
     |
     v
Graphiti stores as persistent fact
     |
     v
Next startup: ALL agents auto-recall this rule
     |
     v
One conversation = all agents updated. No manual repetition.
```

---

## ROMA Reasoning Framework

Recursive Open Meta-Agent architecture. Not a simple prompt chain — a full reasoning pipeline with parallel execution, verification, and real-time visualization.

```
Query ──> Atomizer ──┬── atomic ──> Executor ──> Response
                     |
                     └── complex ──> Planner ──> [Exec1, Exec2, Exec3]
                                                        |
                                                   Aggregator
                                                        |
                                                    Verifier ──> Response
```

Each module injects Freeman's personality through DSPy signatures:

| Module | Role | Freeman twist |
|--------|------|---------------|
| **Atomizer** | Classifies query complexity | "Is this worth decomposing, or is the human asking something trivially shallow?" |
| **Planner** | Decomposes into subtasks | Plans with philosophical coherence, not just logical structure |
| **Executor** | Runs against LLM backends | Maintains Freeman's voice across all executions |
| **Aggregator** | Combines results | Synthesizes without losing the provocative edge |
| **Verifier** | Quality + voice check | Rejects anything that sounds like a corporate chatbot |

Real-time visualization via React frontend + WebSocket — watch the agent think.

---

## Platform Integrations

Adapter pattern. One agent, multiple surfaces.

| Platform | Status | Capabilities |
|----------|--------|-------------|
| Telegram | Production | Full bot, group chat (80% silence rule), DM conversations |
| Discord | Production | Server presence, DM support, rich embeds |
| Twitter/X | In progress | Content posting, engagement tracking, thread generation |

Adding a new platform = one adapter class implementing `BasePlatformAdapter`.

---

## Content Pipeline

Autonomous content creation with quality gates.

```
Ideation ──> Generation ──> Validation ──> Deduplication ──> Scheduling ──> Post
   |              |              |               |                |
 trends       LLM + voice    quality score   similarity check   optimal time
 memory       calibration    persona align   prevent repeats    per platform
```

---

## Analytics Engine

Real-time interaction analytics with sentiment tracking.

- **Metrics**: Response times, engagement rates, conversation depth, topic distribution
- **Sentiment Analysis**: Per-message sentiment scoring, trend detection (improving/declining/stable)
- **Export**: JSON/CSV export for external analysis and dashboards

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Sentient Agent Framework, FastAPI, SSE Streaming |
| LLM | Anthropic Claude, OpenAI GPT, Google Gemini, xAI Grok, OpenRouter |
| Intelligence | Gemini Deep Research, Grok Twitter/X Intel, Claude Synthesis |
| Reasoning | ROMA + DSPy (personality-injected signatures) |
| Memory | Graphiti (knowledge graph), Qdrant (vector search) |
| Database | PostgreSQL (SQLAlchemy ORM), Redis (optional caching) |
| Frontend | React 18, Vite, WebSocket real-time visualization |
| Testing | pytest + pytest-asyncio, 90+ tests, 3 suites |
| Config | Pydantic validation, YAML definitions, env-based secrets |

---

## Project Structure

```
config/                  Agent, memory, analytics, platform configuration (Pydantic + YAML)
src/
  agents/                Freeman base agent, orchestrator, content creator
  memory/                3-layer memory system (12 modules + temporal people graph)
  roma/                  ROMA reasoning pipeline + DSPy modules
  content/               Content pipeline (ideation, generation, validation, scheduling)
  analytics/             Metrics, sentiment analysis, trend detection, export
  platforms/             Telegram, Discord, Twitter adapters + factory
  persona/               Multi-persona manager with memory isolation
  collectors/            Cross-platform interaction collectors (TG, Twitter, YT, Kickstarter)
  intelligence/          Multi-LLM research system (Gemini + Grok + Claude)
  audit/                 Self-improvement loop (quality tracking + auto-patching)
  ecosystem/             Product ecosystem graph with metrics tracking
  community/             Community intelligence monitors + sentiment analysis
  hypothesis/            Product hypothesis testing framework
  core/                  Sentient framework integration, MCP tools
  main.py                Entry point (ROMA mode + Content CLI)
tests/                   90+ tests (unit, integration, e2e)
frontend/                React visualization for ROMA reasoning
docs/                    Architecture, memory system, multi-persona design
```

---

## Quick Start

```bash
git clone https://github.com/mf0-io/freeman_sentient.git
cd freeman_sentient

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env    # Add your API keys

python -m src.main      # Start the agent
```

Visualization frontend:
```bash
cd frontend && npm install && npm run dev
```

Tests:
```bash
pytest tests/ -v                          # Full suite
pytest tests/ --cov=src --cov-report=html # With coverage
```

---

## Autonomous Intelligence System

Three LLMs run in parallel daily to give Freeman full awareness of the current day:

```
                 +----------------+
                 |  Focus Topics  |
                 | (from ecosystem|
                 |  + hypotheses) |
                 +-------+--------+
                         |
          +--------------+--------------+
          |              |              |
+---------v--+  +--------v---+  +------v-------+
| Gemini     |  | Grok       |  | Claude       |
| Deep       |  | Twitter/X  |  | Synthesis    |
| Research   |  | Real-time  |  | (gets all    |
| (market,   |  | (trending, |  |  outputs as  |
| tech)      |  | sentiment) |  |  context)    |
+------+-----+  +-----+------+  +------+-------+
       |               |               |
       +---------------+---------------+
                       |
              +--------v--------+
              | Daily Briefing  |
              | (synthesized    |
              |  intelligence)  |
              +--------+--------+
                       |
         +-------------+-------------+
         |             |             |
   ContentIdeator  Orchestrator  MemoryManager
   (content seeds) (day context) (episodic store)
```

### Self-Improvement Loop (Auto-Audit)

Every 6 hours, Freeman audits his own outputs:

1. **OutputReviewer** scores content across 5 dimensions (voice, depth, engagement, accuracy, mission)
2. **QualityTracker** detects trends (improving / stable / declining)
3. **ImprovementEngine** generates concrete corrections
4. **MemoryPatcher** auto-applies safe suggestions to MEMORY.md (BAD section, Rules section)

### Ecosystem Graph

Knowledge graph of Freeman's product portfolio:
- 10 products tracked (Bot, Cards, NFTs, Channels, Game, DEX, Sentient Agent...)
- Stage tracking: concept -> MVP -> beta -> production
- Cross-product synergies and dependencies
- Dynamic metrics updates from analytics and community data

### Product Hypothesis Tester

Define testable hypotheses, automatically collect evidence, get recommendations:
- "Crypto cards will convert 10% of NFT holders" -> collect evidence from community + analytics
- Auto-evaluate: validated / invalidated / inconclusive
- Feed learnings back into content pipeline

### Audience Intelligence

Per-person tracking across all communities Freeman operates in:

```
Message arrives
     |
     v
AudienceAnalyzer.process_message()
     |
     +-- Sentiment scored per message (running average)
     +-- Activity score computed (messages*1 + replies*2 + reactions*0.5)
     +-- Role classified: advocate / power_user / member / lurker / troll
     +-- Synced to TemporalPeopleGraph (cross-platform identity)
     |
     v
Leaderboard generated (24h / 7d / 30d / all_time)
     |
     v
Top members, advocates, trolls surfaced to Freeman
```

**Grok Profile Intelligence** — for any X/Twitter user Freeman encounters:

1. Fetch profile + last 10 tweets via Twitter API
2. Send to Grok with analysis prompt
3. Get back: who they are, interests, influence level, crypto/AI sentiment, red flags
4. Cache 24h, surface as one-liner: `@user: "Senior dev, pro-crypto, 12K followers, tweets daily about DeFi"`

### Community Intelligence

Monitor own and competitor communities across platforms:
- Own: Telegram, Discord, Twitter
- Competitors: ai16z, Virtuals, Truth Terminal, etc.
- Cross-community sentiment comparison
- Engagement pattern detection and anomaly alerts

---

## Metrics

```
Python codebase:     ~20,000 lines across 90+ modules
Memory modules:      12 + temporal people graph
Intelligence:        3 LLM providers (Gemini, Grok, Claude) running in parallel
Self-audit:          5 quality dimensions, 6-hour cycle
Ecosystem:           10 products, 8 relationships tracked
Community monitors:  3 platforms (own) + 3+ competitors
Hypothesis tracker:  5 active product hypotheses
Test coverage:       90+ tests across 3 suites (unit, integration, e2e)
Platform adapters:   3 (Telegram, Discord, Twitter)
Collectors:          4 (Telegram, Twitter, YouTube, Kickstarter)
ROMA modules:        5 (Atomizer, Planner, Executor, Aggregator, Verifier)
Content pipeline:    6 stages (ideation -> generation -> validation -> dedup -> scheduling -> post)
```

---

## Demo

> Architecture visualization available via React frontend (WebSocket real-time reasoning display).
> Daily briefing and audit reports accessible through the CLI.

---

Built by the [mf0](https://github.com/mf0-io) team. Development started May 2025.
