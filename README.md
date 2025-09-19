# Multi-Agent Debate DAG using LangGraph (Demo Implementation)

**Objective**: Simulate a structured 2-agent debate with memory, turn-control, and an automated Judge node. This repository provides a runnable CLI demo that meets the assignment requirements. It attempts to use `langgraph` if available; otherwise a bundled lightweight DAG runner is used as a fallback.

## Project Workflow (DAG Structure)
Project Workflow (DAG Structure)

 UserInputNode ───▶ AgentA (Scientist) ───▶
                  │                        │
                  │                        ▼
                  │                  MemoryNode ───▶ JudgeNode
                  │                        ▲
UserInputNode ───▶ AgentB (Philosopher) ──┘

# Nodes roles:
- UserInputNode - Takes Topic from user.
- AgentA (Scientist) → Argues logically with science/safety points.

- AgentB (Philosopher) → Argues with autonomy/ethics points.

- MemoryNode → Stores transcript & passes only relevant memory to each agent.


## Delivered files (contained in this textdoc)
- `nodes.py`         — Node definitions (UserInputNode, Agent nodes, MemoryNode, JudgeNode, Logger)
- `main.py`          — CLI runner that executes the 8-round debate and writes logs
- `utils.py`         — Helpers: argument novelty/duplicate checks and simple judge heuristics
- `dag.dot`          — Graphviz DOT source visualizing the DAG
- `demo_run.txt`     — Example run (sample output)
- `README.md`        — This file (instructions)

## Requirements
- Python 3.9+
- Recommended: create a virtualenv

Optional (used if available):
- `langgraph` (if present, code will attempt to use it)
- `graphviz` (for generating PNG from `dag.dot`)

Install minimal runtime dependencies (only if you choose to):
```bash
pip install graphviz
# If 'langgraph' exists in your environment and you want to try it:
# pip install langgraph
```

## How to run (CLI)
1. Save the repository files (this textdoc's files) into a folder.
2. From terminal:
```bash
python main.py
```
3. Enter the debate topic when prompted.

A `debate.log` file will be created with full message logs and state transitions. A DAG dot file `dag.dot` will also be written; if `graphviz` is installed, you can produce `dag.png`:
```bash
dot -Tpng dag.dot -o dag.png
```

## What's enforced
- Exactly 8 rounds (4 per agent), alternating between `Scientist` and `Philosopher` (AgentA=Scientist starts by default)
- Turn control (agents cannot speak out of turn)
- No repeated argument (simple textual duplication check)
- Memory summaries are stored per-agent and only relevant memory is provided to the opposite agent per round
- All node messages, memory updates, and final judgment are logged to `debate.log`.

## Notes about LangGraph
This implementation includes a small adapter that will use a `langgraph` library (if available) to build a DAG. If `langgraph` is not present, the bundled lightweight runner is used — behavior, logging, and outputs are identical from the caller's perspective.
