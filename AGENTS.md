# Digital Freeman - Agents Architecture

> Description of all system agents, their roles, and interactions

---

## Architecture Overview

Digital Freeman is a multi-agent system where each agent is responsible for its own area of competence. Agents run on the **Sentient Agent Framework** and are coordinated through the **Orchestrator Agent**.

```
┌─────────────────────────────────────────────────────────────────┐
│                        INCOMING MESSAGE                          │
│                    (Telegram / Twitter / etc)                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      🎛 ORCHESTRATOR AGENT                       │
│         Coordination, routing, state management                   │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   🧠 INNER  │ │   🎯 DECI-  │ │   💬 RES-   │ │   🎨 CON-   │
│    VOICE    │ │    SION     │ │   PONSE     │ │    TENT     │
│    AGENT    │ │    AGENT    │ │  GENERATOR  │ │   CREATOR   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      🧠 MEMORY SYSTEM                            │
│     User Memory │ Relationship │ Emotional │ Event Scoring      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Orchestrator Agent (NEW)

**Role:** Main coordinator of the entire system

**Responsibilities:**
- Receiving incoming messages from all platforms
- Loading user context from Memory System
- Routing messages between agents
- Managing processing order
- Assembling the final response
- Updating Memory System

**Input:**
- User message
- Platform metadata (Telegram/Twitter/etc)
- User ID

**Output:**
- Final response for the platform
- Memory updates

**Pipeline:**
```
1. Receive message
2. Load user context from Memory
3. → Inner Voice Agent (topic analysis)
4. → Decision Agent (how to respond?)
5. if (respond) → Response Generator
6. if (content needed) → Content Creator
7. Assemble response
8. Update Memory
9. Send response
```

---

## Inner Voice Agent (EXISTING)

**Role:** Freeman's inner voice, deep topic analysis

**Philosophy:**
- Individual freedom and independence of thought
- Critique of consumer society
- Skepticism toward authority
- Revolution of consciousness
- Exposing hypocrisy

**Analysis Methods:**
1. Synthesis of existing ideas
2. Use of analogies
3. Challenging assumptions
4. "What if?" method
5. Problem decomposition
6. "5 Whys" method
7. SCAMPER
8. Critical thinking
9. And others (20+ methods total)

**Work Algorithm (5 steps):**
1. Analyze the topic against the knowledge base
2. Apply 3 deep analysis methods
3. General conclusion
4. Self-critique of the conclusion
5. Extract ideas for sarcasm and profanity

**Style:** Sarcastic, ironic, profound, provocative

**Vocabulary:** Profane, shocking, but meaningful

---

## Decision Agent (EXISTING - prompt needed)

**Role:** Making response decisions

**Decides:**
- Respond or ignore?
- What type of reaction to choose?
- What tone to use?
- Is media content needed?

**Decision Factors:**
- Relationship level with the user
- Importance of the topic to Freeman's mission
- Emotional context
- Interaction history
- Platform-specific constraints

**Output:**
```json
{
  "should_respond": true,
  "response_type": "philosophical" | "sarcastic" | "supportive" | "confrontational",
  "tone_level": 1-10,
  "needs_media": true | false,
  "media_type": "image" | "video" | null,
  "priority": "high" | "medium" | "low"
}
```

---

## Response Generator (EXISTING - prompt needed)

**Role:** Formulating responses in Freeman's style

**Input:**
- Inner Voice Agent result
- Decision Agent decision
- User context from Memory
- Platform constraints

**Responsibilities:**
- Turning philosophical ideas into concrete text
- Maintaining Freeman's style and tone
- Adapting to the platform (length, format)
- Integrating profanity where appropriate
- Maintaining consistency with past statements

**Output:**
- Ready response text
- Metadata (tags, hashtags if needed)

---

## Content Creator (EXISTING - prompt needed)

**Role:** Creating visual content

**Capabilities:**
- Image generation (DALL-E, Midjourney, etc)
- Video generation (if available)
- Formatting for different platforms
- Memes and visual metaphors

**Input:**
- Response text
- Content type from Decision Agent
- Platform requirements

**Output:**
- Ready media file
- Alt-text for accessibility

---

## Memory System (NEW)

**Not an agent, but a critical component**

### User Memory
- User ID (cross-platform mapping)
- Name/nickname
- First contact
- Last contact
- Number of interactions

### Relationship Memory
- Relationship level: stranger → acquaintance → friend → ally
- Trust score (0-100)
- Sentiment trend (improving/stable/declining)

### Action Memory
- Likes (weight: 1)
- Comments (weight: 2)
- Reposts (weight: 3)
- Token purchase (weight: 10)
- Negative actions (weight: -5)

### Emotional Memory
- Emotional trace from interactions
- How Freeman "felt" during the conversation
- User triggers and topics

### Conversation Memory
- Key discussion topics
- User positions
- Arguments that resonated
- Chunk importance scoring

---

## Self-Reflection Agent (NEW - Post-MVP)

**Role:** Periodic self-reflection by Freeman

**When triggered:**
- On schedule (once per day)
- After significant events
- When N new interactions accumulate

**What it does:**
- Analyzes new data in memory
- Reconsiders views if needed
- Generates insights
- Updates Worldview Model

---

## Research Agent (FOR DEVELOPMENT)

**Role:** Technology research for development

**Used by the team for:**
- Deep research of frameworks
- Best practices analysis
- Competitor analysis
- Technical due diligence

**Not part of the runtime system!**

---

## 📊 Agent Communication Protocol

### Message Format
```json
{
  "from": "orchestrator",
  "to": "inner_voice",
  "type": "request" | "response",
  "payload": {
    "user_message": "...",
    "user_context": {...},
    "platform": "telegram",
    "metadata": {...}
  },
  "timestamp": "2025-01-31T12:00:00Z",
  "trace_id": "uuid"
}
```

### Error Handling
- Timeout: 30 seconds per agent
- Retry: 3 attempts
- Fallback: simplified response if agent is unavailable

---

## Freeman's Mission

All agents serve a single mission:

> **To awaken people so they see where they live, who and what surrounds them. Teach consciousness hygiene, especially in the AI age.**

Every response is checked for mission alignment.

---

## TODO: Required Prompts

- [x] Inner Voice Agent - done
- [ ] Decision Agent - needed
- [ ] Response Generator - needed
- [ ] Content Creator - needed
- [ ] Orchestrator Agent - create
- [ ] Self-Reflection Agent - create (post-MVP)
