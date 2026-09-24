# Local model layer (Ollama) — spec

Belongs to Phase 2 (local language layer) and Phase 3 (router) of the roadmap. Out of scope until Phase 0/1 (data foundation, statistical core) are done — see `roadmap.md`.

## Dependency mode

Depend, per `CLAUDE.md`'s build-philosophy table — Ollama and the models it runs are used as-is, no forking.

## What it's for

NL question parsing (turning a typed question into a structured analysis spec) and explanation/caveated-answer generation. Not the statistics/causal-inference itself — that's pure code, no model call, per the "compute, then explain" principle.

## Setup

1. Install Ollama (ollama.com) — runs locally, exposes an API at `localhost:11434`.
2. Pull a model:
   - `ollama pull qwen2.5:7b` or `ollama pull llama3.2` — from Ollama's own curated library (the default, easiest path).
   - `ollama run hf.co/{username}/{repository}:{quantization}` — pulls a GGUF model directly from Hugging Face instead, for anything not already in Ollama's library. Default quantization is Q4_K_M when present in the repo.
3. Call it from code via `pip install ollama`, then `ollama.chat(model="qwen2.5:7b", messages=[...])` — no API key, no cost beyond your own machine's compute.

## Recommended starting model

**Llama 3.2 3B or Qwen2.5 7B** — small enough to run comfortably on a laptop, capable enough for structured extraction and writing a caveated paragraph. Escalate only if a small model's explanations start feeling genuinely thin.

## Fallback when local isn't enough

If the machine can't comfortably run a bigger model, or the agent needs to be available without a laptop staying on, fall back to a Hugging Face Inference Endpoint (same models, hosted, small cost instead of $0). This is a direct instance of the circuit-breaker pattern from the self-healing layer (`MattGPT-Outline.md` §12) — local model down or too weak → switch to the hosted backup — not a separate mechanism to design.
