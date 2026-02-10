from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import SLA_COMPLIANCE, SLA_COMPLETENESS
from app.db import add_audit_event, add_event, add_message, create_conversation, list_judge_runs, list_metrics
from app.graph import build_graph
from app.guards.guardrails import run_guardrails
from app.telemetry.langfuse_client import start_trace

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None
    approve_email: Optional[bool] = False
    approve_email_content: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    blocked: bool
    guardrail_findings: dict


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    guardrail = run_guardrails(req.message)
    conversation_id = req.conversation_id or create_conversation(req.customer_id)

    if guardrail.redactions:
        add_audit_event(
            conversation_id,
            "pii_redaction",
            {"redactions": guardrail.redactions, "original_length": len(req.message)},
        )

    if guardrail.blocked:
        add_event(conversation_id, "guardrail_block", {"findings": guardrail.findings})
        raise HTTPException(status_code=400, detail={"blocked": True, "findings": guardrail.findings})

    add_message(conversation_id, "user", guardrail.redacted_text, {"customer_id": req.customer_id})

    trace = start_trace("retention_chat", {"message": guardrail.redacted_text, "customer_id": req.customer_id})

    state = {
        "user_input": guardrail.redacted_text,
        "customer_id": req.customer_id,
        "approve_email": bool(req.approve_email),
        "approve_email_content": req.approve_email_content,
    }
    graph = build_graph(trace_id=conversation_id)
    result = graph.invoke(state)
    response_text = result.get("response_text", "")

    if trace:
        trace.update(output={"response": response_text})

    add_message(conversation_id, "assistant", response_text, {"customer_id": req.customer_id})

    return ChatResponse(
        conversation_id=conversation_id,
        response=response_text,
        blocked=False,
        guardrail_findings=guardrail.findings,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    guardrail = run_guardrails(req.message)
    conversation_id = req.conversation_id or create_conversation(req.customer_id)

    if guardrail.redactions:
        add_audit_event(
            conversation_id,
            "pii_redaction",
            {"redactions": guardrail.redactions, "original_length": len(req.message)},
        )

    if guardrail.blocked:
        add_event(conversation_id, "guardrail_block", {"findings": guardrail.findings})
        raise HTTPException(status_code=400, detail={"blocked": True, "findings": guardrail.findings})

    add_message(conversation_id, "user", guardrail.redacted_text, {"customer_id": req.customer_id})

    trace = start_trace("retention_chat", {"message": guardrail.redacted_text, "customer_id": req.customer_id})

    state = {
        "user_input": guardrail.redacted_text,
        "customer_id": req.customer_id,
        "approve_email": bool(req.approve_email),
        "approve_email_content": req.approve_email_content,
    }
    graph = build_graph(trace_id=conversation_id)
    result = graph.invoke(state)
    response_text = result.get("response_text", "")

    if trace:
        trace.update(output={"response": response_text})

    add_message(conversation_id, "assistant", response_text, {"customer_id": req.customer_id})

    def sse():
        yield f"event: meta\ndata: {conversation_id}\n\n"
        chunk_size = 32
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i : i + chunk_size].replace("\n", "\\n")
            yield f"event: chunk\ndata: {chunk}\n\n"
        yield "event: done\ndata: end\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


@router.get("/metrics")
async def metrics(limit: int = 24):
    return {
        "metrics": list(list_metrics(limit)),
        "sla": {
            "compliance": SLA_COMPLIANCE,
            "completeness": SLA_COMPLETENESS,
        },
    }


@router.get("/judge-runs")
async def judge_runs(limit: int = 50):
    return {"runs": list(list_judge_runs(limit))}
