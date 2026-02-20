# Digital Freeman - Product Backlog

> Autonomous entertainment AI agent based on Sentient Agent Framework
> Goal: MVP for partnership with Sentient AGI

---

## MVP Scope

**Platforms:** Telegram, Twitter
**Core:** Sentient Agent Framework
**Key Feature:** Emotional memory and user relationships

---

## EPIC 1: Memory System (CRITICAL)

The memory system is the heart of the project. Freeman must remember people, their actions, and build relationships.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| MEM-1 | **Research: Memory Frameworks** - study mem0, Graphiti, Letta, custom solutions. Choose optimal for emotional memory | P0 | Research | TODO |
| MEM-2 | **User Recognition** - recognize users across platforms (Telegram ID, Twitter handle). Unified user profile | P0 | Medium | TODO |
| MEM-3 | **Relationship Levels** - relationship level system (stranger → acquaintance → friend → ally). Affects communication tone | P0 | Medium | TODO |
| MEM-4 | **Action Memory** - remember user actions: likes, reposts, token purchases, comments. Weighted scoring | P0 | Medium | TODO |
| MEM-5 | **Event Importance Scoring** - ML/rule-based system for evaluating event importance to Freeman. What to remember long-term vs ignore | P0 | High | TODO |
| MEM-6 | **Emotional Memory** - emotional trace from interactions. Freeman remembers HOW he felt during interactions | P0 | High | TODO |
| MEM-7 | **Short-term → Long-term** - memory consolidation mechanism. Nightly "sleep" for processing and compressing memories | P1 | High | TODO |
| MEM-8 | **Memory Retrieval** - efficient memory search. RAG or graph-based retrieval | P1 | High | TODO |

### Acceptance Criteria for EPIC 1:
- [ ] Freeman recognizes a user on repeated contact
- [ ] Communication tone changes depending on relationship history
- [ ] Important events (token purchase) affect the relationship more strongly than likes
- [ ] Freeman can recall what the user said previously

---

## EPIC 2: Agent Core (Sentient Integration)

Migration of existing agents to Sentient Framework and creation of the orchestrator.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| CORE-1 | **Research: Sentient Framework** - deep study of the API, patterns, limitations. Integration documentation | P0 | Research | TODO |
| CORE-2 | **Project Scaffolding** - basic project structure for Sentient. Docker, configs, env variables | P0 | Low | TODO |
| CORE-3 | **Inner Voice Agent → Sentient** - migration of the philosophical reflection agent | P0 | Medium | TODO |
| CORE-4 | **Decision Agent → Sentient** - migration of the decision-making agent (respond/ignore/how to respond) | P0 | Medium | TODO |
| CORE-5 | **Response Generator → Sentient** - migration of the response formulation agent | P1 | Medium | TODO |
| CORE-6 | **Content Creator → Sentient** - migration of the content creation agent (images, video, formats) | P2 | High | TODO |
| CORE-7 | **Orchestrator Agent** - main agent coordinating all sub-agents. Message routing, state management | P0 | High | TODO |
| CORE-8 | **Agent Communication Protocol** - inter-agent communication protocol. Message format, error handling | P1 | Medium | TODO |

### Acceptance Criteria for EPIC 2:
- [ ] All 4 agents run on Sentient Framework
- [ ] Orchestrator correctly routes messages
- [ ] Agents share context
- [ ] System operates autonomously without manual intervention

---

## EPIC 3: Telegram Integration

First platform for MVP. Bot + possibly a channel.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| TG-1 | **Basic Bot Setup** - create bot, webhook/polling, basic handler | P0 | Low | TODO |
| TG-2 | **Message Processing Pipeline** - process incoming: text, stickers, media. Normalization for agents | P0 | Medium | TODO |
| TG-3 | **Memory Integration** - connect to memory system. Save/load user context | P0 | Medium | TODO |
| TG-4 | **Response Formatting** - format responses for Telegram: markdown, buttons, media | P1 | Low | TODO |
| TG-5 | **Group Chat Support** - support group chats. Respond to mentions | P2 | Medium | TODO |
| TG-6 | **Channel Posting** - autonomous channel posting. Scheduler, content queue | P2 | Medium | TODO |
| TG-7 | **Inline Mode** - inline mode for using Freeman in other chats | P3 | Low | TODO |

### Acceptance Criteria for EPIC 3:
- [ ] Bot responds to direct messages in Freeman's style
- [ ] Bot remembers interaction history with the user
- [ ] Responses are properly formatted (markdown, media)

---

## EPIC 4: Twitter Integration

Second platform. More complex due to rate limits and specifics.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| TW-1 | **Twitter API v2 Setup** - OAuth, API keys, rate limit handling | P1 | Medium | TODO |
| TW-2 | **Mentions Monitoring** - monitor @freeman mentions. Webhook or polling | P1 | Medium | TODO |
| TW-3 | **Reply Generation** - generate and post replies. Thread support | P1 | Medium | TODO |
| TW-4 | **Grok Integration** - use Grok for user research before responding | P2 | Research | TODO |
| TW-5 | **Autonomous Posting** - independent posts on schedule or triggers | P2 | High | TODO |
| TW-6 | **Engagement Tracking** - track likes, retweets, comments for Memory System | P2 | Medium | TODO |
| TW-7 | **Thread Composer** - create threads for long reflections | P3 | Medium | TODO |

### Acceptance Criteria for EPIC 4:
- [ ] Freeman responds to Twitter mentions
- [ ] Responses match Twitter's style and limits
- [ ] Engagement is tracked and affects relationships

---

## EPIC 5: Personality & Evolution

Freeman must evolve and reconsider views.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| PERS-1 | **Worldview Model** - formalized model of Freeman's views. What he thinks about topics X, Y, Z | P1 | High | TODO |
| PERS-2 | **Opinion Evolution** - mechanism for changing opinions based on arguments. Not flip-flop, but gradual shift | P1 | High | TODO |
| PERS-3 | **Conversation Chunk Evaluation** - evaluate each conversation chunk: important/routine/noise | P1 | Medium | TODO |
| PERS-4 | **Self-Reflection Agent** - periodic self-reflection. "What did I learn? How have I changed?" | P2 | High | TODO |
| PERS-5 | **Consistency Checker** - verify Freeman doesn't contradict himself (or does so intentionally) | P2 | Medium | TODO |
| PERS-6 | **Mission Alignment** - all actions checked for alignment with the mission: awakening people | P1 | Medium | TODO |

### Acceptance Criteria for EPIC 5:
- [ ] Freeman can change his opinion if given good arguments
- [ ] Freeman remembers his past statements
- [ ] All responses align with the awakening mission

---

## EPIC 6: Self-Improvement System

Autonomous agent improvement.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| SELF-1 | **Research: Self-improvement patterns** - study Auto-Claude, Claude Code wrappers, OpenHands, Devin patterns | P2 | Research | TODO |
| SELF-2 | **Feedback Collection** - collect user feedback (reactions, engagement, explicit feedback) | P2 | Medium | TODO |
| SELF-3 | **Prompt Optimization Pipeline** - automatic prompt optimization based on feedback | P2 | High | TODO |
| SELF-4 | **A/B Testing Framework** - test different versions of responses/prompts | P3 | High | TODO |
| SELF-5 | **Performance Metrics** - quality metrics: engagement, sentiment, mission alignment | P2 | Medium | TODO |

### Acceptance Criteria for EPIC 6:
- [ ] System collects response quality metrics
- [ ] There is a mechanism for prompt improvement
- [ ] Freeman improves over time

---

## EPIC 7: Infrastructure & DevOps

Infrastructure for production.

| ID | Task | Priority | Complexity | Status |
|----|------|----------|------------|--------|
| INFRA-1 | **Docker Setup** - containerize all components | P1 | Low | TODO |
| INFRA-2 | **CI/CD Pipeline** - automatic deployment, tests | P1 | Medium | TODO |
| INFRA-3 | **Logging & Monitoring** - centralized logs, alerts | P1 | Medium | TODO |
| INFRA-4 | **Database Setup** - PostgreSQL/Redis for memory and state | P0 | Low | TODO |
| INFRA-5 | **Secrets Management** - secure API key storage | P0 | Low | TODO |
| INFRA-6 | **Cost Monitoring** - track LLM API expenses | P2 | Low | TODO |

### Acceptance Criteria for EPIC 7:
- [ ] System deploys with a single command
- [ ] Monitoring and alerts are in place
- [ ] Secrets are protected

---

## MVP Milestone

**Goal:** Working demo for Sentient partnership

**Includes:**
- [x] EPIC 1: MEM-1 → MEM-6 (basic memory)
- [x] EPIC 2: CORE-1 → CORE-5, CORE-7 (agents on Sentient)
- [x] EPIC 3: TG-1 → TG-4 (Telegram bot)
- [x] EPIC 5: PERS-3, PERS-6 (basic personality)
- [x] EPIC 7: INFRA-4, INFRA-5 (minimal infrastructure)

**Not included (Post-MVP):**
- Twitter integration
- Self-improvement
- Full personality evolution
- CI/CD

---

## Labels

- `P0` - Blocker, MVP doesn't work without this
- `P1` - Important for MVP quality
- `P2` - Nice to have for MVP
- `P3` - Post-MVP
- `Research` - Requires research before implementation
- `Low/Medium/High` - Implementation complexity

---

## 📝 Notes

### Current Agent Prompts
1. **Inner Voice Agent** - philosophical reflections, analysis methods (synthesis, analogies, SCAMPER)
2. **Decision Agent** - deciding how to react (prompt needed)
3. **Response Generator** - formulating responses (prompt needed)
4. **Content Creator** - generating media content (prompt needed)

### Key Research Questions
- Which memory framework is best for emotional memory?
- How to integrate Grok for user research on Twitter?
- Which self-improvement patterns actually work?
- How to measure user "awakening"?

### API Keys (in .env)
- OpenAI
- Anthropic
- Telegram Bot Token
- Twitter API v2
- (others as needed)
