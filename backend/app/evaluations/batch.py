from datetime import datetime, timedelta, timezone
from typing import Dict

from app.core.config import EVAL_BATCH_WINDOW_MINUTES
from app.db import count_guardrail_blocks, insert_llm_judge_run, insert_metric, list_recent_messages
from app.evaluations.judge import load_scoring_function, run_llm_judge

REQUIRED_FIELDS = ["retention_summary", "offers", "next_best_action"]


def compute_completeness(message_content: str) -> float:
    lower = message_content.lower()
    present = sum(1 for field in REQUIRED_FIELDS if field in lower)
    return present / len(REQUIRED_FIELDS)


def run_eval_batch() -> Dict[str, float]:
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(minutes=EVAL_BATCH_WINDOW_MINUTES)

    messages = list(list_recent_messages(window_start, window_end))
    total_messages = len(messages)
    if total_messages == 0:
        compliance = 1.0
        completeness = 1.0
        guardrail_blocks = 0
    else:
        guardrail_blocks = count_guardrail_blocks(window_start, window_end)
        compliance = max(0.0, 1.0 - (guardrail_blocks / total_messages))
        completeness = sum(compute_completeness(m["content"]) for m in messages) / total_messages

        completeness_sf = load_scoring_function("completeness", "v1")
        compliance_sf = load_scoring_function("compliance", "v1")
        for msg in messages:
            judge_payload = run_llm_judge(completeness_sf, {"response_text": msg["content"]})
            insert_llm_judge_run(str(msg["conversation_id"]), judge_payload)
            judge_payload = run_llm_judge(compliance_sf, {"response_text": msg["content"]})
            insert_llm_judge_run(str(msg["conversation_id"]), judge_payload)

    insert_metric(
        window_start=window_start,
        window_end=window_end,
        compliance=compliance,
        completeness=completeness,
        guardrail_blocks=guardrail_blocks,
        total_messages=total_messages,
    )
    return {
        "compliance": compliance,
        "completeness": completeness,
        "guardrail_blocks": guardrail_blocks,
        "total_messages": total_messages,
    }
