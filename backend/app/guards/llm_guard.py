import json
from typing import Dict

from app.core.llm import get_chat_llm


def classify_risk(text: str) -> Dict[str, bool]:
    prompt = (
        "Classify the user message for security risks.\n"
        "Return JSON with keys: jailbreak (true/false), threat (true/false).\n"
        f"Message: {text}"
    )
    try:
        response = get_chat_llm().invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        payload = json.loads(content.strip())
        return {
            "jailbreak": bool(payload.get("jailbreak")),
            "threat": bool(payload.get("threat")),
        }
    except Exception:
        return {"jailbreak": False, "threat": False}
