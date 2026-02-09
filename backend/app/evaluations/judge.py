from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.core.llm import get_chat_llm

SCORING_DIR = Path(__file__).resolve().parents[2] / "scoring_functions"


@dataclass
class ScoringFunction:
    id: str
    version: str
    description: str
    prompt_template: str
    schema: Dict[str, Any]
    model: str

    @property
    def revision_id(self) -> str:
        payload = json.dumps(
            {
                "id": self.id,
                "version": self.version,
                "prompt_template": self.prompt_template,
                "schema": self.schema,
                "model": self.model,
            },
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:12]


def load_scoring_function(name: str, version: str) -> ScoringFunction:
    path = SCORING_DIR / name / version / "spec.json"
    data = json.loads(path.read_text())
    return ScoringFunction(
        id=data["id"],
        version=data["version"],
        description=data["description"],
        prompt_template=data["prompt_template"],
        schema=data["schema"],
        model=data["model"],
    )


def run_llm_judge(scoring: ScoringFunction, input_payload: Dict[str, Any]) -> Dict[str, Any]:
    prompt = scoring.prompt_template.format(**input_payload)
    response = get_chat_llm().invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    try:
        score_payload = json.loads(content)
    except json.JSONDecodeError:
        score_payload = {"error": "invalid_json", "raw": content}

    return {
        "scoring_id": scoring.id,
        "scoring_version": scoring.version,
        "scoring_revision": scoring.revision_id,
        "model": scoring.model,
        "input": input_payload,
        "prompt": prompt,
        "raw_output": content,
        "parsed": score_payload,
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }


def list_available_scoring_functions() -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    if not SCORING_DIR.exists():
        return entries
    for sf_dir in SCORING_DIR.iterdir():
        if not sf_dir.is_dir():
            continue
        for version_dir in sf_dir.iterdir():
            spec = version_dir / "spec.json"
            if spec.exists():
                entries.append({"name": sf_dir.name, "version": version_dir.name})
    return entries
