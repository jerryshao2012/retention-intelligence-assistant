import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

import psycopg
from psycopg.rows import dict_row

from app.core.config import DATABASE_URL


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    ddl = """
    create table if not exists conversations (
        id uuid primary key,
        customer_id text,
        started_at timestamptz not null,
        ended_at timestamptz
    );

    create table if not exists chat_messages (
        id uuid primary key,
        conversation_id uuid references conversations(id),
        role text not null,
        content text not null,
        metadata jsonb,
        created_at timestamptz not null
    );

    create table if not exists events (
        id uuid primary key,
        conversation_id uuid references conversations(id),
        event_type text not null,
        payload jsonb,
        created_at timestamptz not null
    );

    create table if not exists audit_trail (
        id uuid primary key,
        conversation_id uuid references conversations(id),
        event_type text not null,
        payload jsonb,
        created_at timestamptz not null
    );

    create table if not exists ai_eval_metrics (
        id uuid primary key,
        window_start timestamptz not null,
        window_end timestamptz not null,
        compliance numeric not null,
        completeness numeric not null,
        guardrail_blocks integer not null,
        total_messages integer not null,
        created_at timestamptz not null
    );

    create table if not exists llm_judge_runs (
        id uuid primary key,
        conversation_id uuid references conversations(id),
        scoring_id text not null,
        scoring_version text not null,
        scoring_revision text not null,
        model text not null,
        input jsonb not null,
        prompt text not null,
        raw_output text not null,
        parsed jsonb,
        scored_at timestamptz not null,
        created_at timestamptz not null
    );
    """
    with get_conn() as conn:
        conn.execute(ddl)
        conn.commit()


def create_conversation(customer_id: Optional[str]) -> str:
    convo_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "insert into conversations (id, customer_id, started_at) values (%s, %s, %s)",
            (convo_id, customer_id, datetime.now(timezone.utc)),
        )
        conn.commit()
    return convo_id


def add_message(conversation_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "insert into chat_messages (id, conversation_id, role, content, metadata, created_at) values (%s, %s, %s, %s, %s, %s)",
            (
                str(uuid.uuid4()),
                conversation_id,
                role,
                content,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc),
            ),
        )
        conn.commit()


def add_event(conversation_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "insert into events (id, conversation_id, event_type, payload, created_at) values (%s, %s, %s, %s, %s)",
            (
                str(uuid.uuid4()),
                conversation_id,
                event_type,
                json.dumps(payload),
                datetime.now(timezone.utc),
            ),
        )
        conn.commit()


def add_audit_event(conversation_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "insert into audit_trail (id, conversation_id, event_type, payload, created_at) values (%s, %s, %s, %s, %s)",
            (
                str(uuid.uuid4()),
                conversation_id,
                event_type,
                json.dumps(payload),
                datetime.now(timezone.utc),
            ),
        )
        conn.commit()


def list_metrics(limit: int = 24) -> Iterable[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "select * from ai_eval_metrics order by window_end desc limit %s",
            (limit,),
        ).fetchall()
    return rows


def insert_metric(window_start, window_end, compliance, completeness, guardrail_blocks, total_messages):
    with get_conn() as conn:
        conn.execute(
            "insert into ai_eval_metrics (id, window_start, window_end, compliance, completeness, guardrail_blocks, total_messages, created_at) values (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(uuid.uuid4()),
                window_start,
                window_end,
                compliance,
                completeness,
                guardrail_blocks,
                total_messages,
                datetime.now(timezone.utc),
            ),
        )
        conn.commit()


def insert_llm_judge_run(conversation_id: str, payload: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "insert into llm_judge_runs (id, conversation_id, scoring_id, scoring_version, scoring_revision, model, input, prompt, raw_output, parsed, scored_at, created_at) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(uuid.uuid4()),
                conversation_id,
                payload.get("scoring_id"),
                payload.get("scoring_version"),
                payload.get("scoring_revision"),
                payload.get("model"),
                json.dumps(payload.get("input", {})),
                payload.get("prompt", ""),
                payload.get("raw_output", ""),
                json.dumps(payload.get("parsed", {})),
                payload.get("scored_at"),
                datetime.now(timezone.utc),
            ),
        )
        conn.commit()


def list_recent_messages(window_start, window_end) -> Iterable[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "select * from chat_messages where created_at >= %s and created_at < %s",
            (window_start, window_end),
        ).fetchall()
    return rows


def count_guardrail_blocks(window_start, window_end) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "select count(*) as total from events where event_type = 'guardrail_block' and created_at >= %s and created_at < %s",
            (window_start, window_end),
        ).fetchone()
    return int(row["total"]) if row else 0


def list_judge_runs(limit: int = 50) -> Iterable[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "select * from llm_judge_runs order by created_at desc limit %s",
            (limit,),
        ).fetchall()
    return rows
