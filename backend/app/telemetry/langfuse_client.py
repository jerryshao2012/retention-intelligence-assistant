from typing import Any, Dict, Optional

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.core.config import LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY


def get_langfuse() -> Optional[Langfuse]:
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        return None
    return Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
    )


def start_trace(name: str, input_payload: Dict[str, Any]):
    lf = get_langfuse()
    if not lf:
        return None
    return lf.trace(name=name, input=input_payload)


def get_langfuse_handler(trace_id: Optional[str] = None) -> Optional[CallbackHandler]:
    lf = get_langfuse()
    if not lf:
        return None
    return CallbackHandler(langfuse=lf, trace_id=trace_id)
