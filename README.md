# Retention Intelligence Assistant

Multi-agent orchestration system that transforms attrition signals into actionable banker intelligence. Includes guardrails, telemetry, LLM-judge scoring, batch evals, and a styled UI.

## What’s Included
- **LangGraph** workflow with Attrition, Segmentation, RAG, and Communication agents.
- **Guardrails** for PII redaction, jailbreak detection, and threat detection.
- **Email approval gate**: email drafts require explicit approval before finalization.
- **Langfuse** integration for trace capture.
- **Telemetry + AI Eval** batch metrics (compliance, completeness).
- **LLM Judge Scoring Functions** with in-repo versioning and replayable runs.
- **Next.js UI**: Chat Studio + AI Eval Dashboard (metrics + judge runs).

## API Endpoints
- `POST /api/chat` – synchronous response
- `POST /api/chat/stream` – Server-Sent Events (SSE) streaming response
- `GET /api/metrics` – batch metrics + SLA thresholds
- `GET /api/judge-runs` – recent LLM judge runs

## Quick Start
See `SYSTEM_SETUP.md` for full local instructions.

## Folder Structure
- `backend/` FastAPI + LangGraph + telemetry + evals
- `backend/scoring_functions/` versioned scoring function objects
- `backend/data/` synthetic dataset (includes Cash Back Mastercard)
- `frontend/` Next.js UI
- `docs/ARCHITECTURE.md` system architecture

## Scoring Function Objects (LLM Judge)
Scoring functions are versioned in-repo to allow rollbacks and exact replays.

Structure:
```
backend/scoring_functions/
  <scoring_id>/
    <version>/
      spec.json
      README.md
```

Each `spec.json` contains:
- `id`, `version`, `description`
- `prompt_template`
- `schema` (expected JSON output)
- `model`

Every judge run stores:
- `scoring_id`, `scoring_version`, and derived `scoring_revision` hash
- full input, prompt, raw output, parsed output
- timestamps for reproducibility

## Notes
- The synthetic dataset includes the Cash Back Mastercard but the UI is product-agnostic.
- For streaming, the frontend buffers SSE chunks and renders once complete to preserve markdown tables.
