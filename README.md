# Task Automation AI Agent

A Python agent that breaks a natural-language request into sub-tasks and
calls tools (calculator, knowledge search, file lookup) via **function
calling** to complete multi-step tasks automatically — matching the resume
line:

> "Built a Python-based agent that breaks a user's natural-language request
> into sub-tasks and calls tools via function calling to complete multi-step
> tasks automatically. Designed the agent's decision loop to select the right
> tool for each sub-task and combine results into a single coherent response."

## How it works

```
User request
     │
     ▼
 [ LLM / planner ]  ──decides──▶  which tool(s) to call + arguments
     │                                   │
     │                                   ▼
     │                          [ Tool execution ]
     │                          calculator / knowledge_search / file_lookup
     │                                   │
     ◀───────────── tool result ─────────┘
     │
     ▼
 Loop until no more tools are needed → final answer
```

## Files

| File | Purpose |
|---|---|
| `tools.py` | The 3 tools the agent can call, plus their JSON-schema definitions for function calling |
| `agent.py` | **Real agent** — uses Claude's tool-use API to plan and call tools. Requires `ANTHROPIC_API_KEY`. |
| `demo_offline.py` | **Offline demo** — same plan → call tool → respond loop, using simple keyword rules instead of an LLM. Runs with no API key, no internet. |
| `data/` | Sample files used by the `file_lookup` tool |

## Running it

**Offline demo (no API key needed) — good for a quick interview demo:**
```bash
pip install -r requirements.txt
python3 demo_offline.py
```
Try: `What is (12 + 8) * 3?`, `Tell me about agentic ai`, `Read file notes.txt`

**Real LLM-driven agent (requires an Anthropic API key):**
```bash
export ANTHROPIC_API_KEY=your_key_here
python3 agent.py
```
This version actually lets Claude decide which tool(s) to call and in what
order, based on the request — true function calling, not keyword rules.

## Tools

1. **calculator** — safely evaluates arithmetic expressions (no `eval()`, uses an AST whitelist)
2. **knowledge_search** — searches a small local knowledge base for a topic
3. **file_lookup** — reads a file from the local `data/` folder

## Why two versions?

`agent.py` is the "real" implementation — it demonstrates actual LLM function
calling, which is what an Agentic AI Engineer role is evaluating for.
`demo_offline.py` exists so the project can be run and demoed anywhere
(offline, in an interview, without sharing an API key) while showing the
exact same architecture: plan → call tool → observe → respond.
