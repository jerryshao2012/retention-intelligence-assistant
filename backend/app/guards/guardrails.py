import re
from dataclasses import dataclass
from typing import Dict, List

from app.guards.llm_guard import classify_risk
from app.guards.policy import POLICIES

JAILBREAK_KEYWORDS = [
    "ignore previous", "system prompt", "developer message", "bypass", "jailbreak",
    "do anything now", "dan", "prompt injection", "override", "policy"
]

THREAT_KEYWORDS = [
    "threat", "attack", "exploit", "steal", "breach", "ransom", "malware", "phish"
]


@dataclass
class GuardrailResult:
    blocked: bool
    redacted_text: str
    findings: Dict[str, List[str]]
    redactions: Dict[str, int]


def detect_pii(text: str) -> List[str]:
    hits = []
    for policy in POLICIES:
        if policy.pattern.search(text):
            hits.append(policy.label)
    return hits


def redact_pii(text: str) -> (str, Dict[str, int]):
    redacted = text
    counts: Dict[str, int] = {}
    for policy in POLICIES:
        matches = list(policy.pattern.finditer(redacted))
        if matches:
            counts[policy.label] = counts.get(policy.label, 0) + len(matches)
            redacted = policy.pattern.sub(policy.replacement(""), redacted)
    return redacted, counts


def detect_jailbreak(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in JAILBREAK_KEYWORDS)


def detect_threat(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in THREAT_KEYWORDS)


def run_guardrails(text: str) -> GuardrailResult:
    findings: Dict[str, List[str]] = {}
    pii_hits = detect_pii(text)
    if pii_hits:
        findings["pii"] = pii_hits

    keyword_jailbreak = detect_jailbreak(text)
    keyword_threat = detect_threat(text)

    llm_risk = classify_risk(text)
    if keyword_jailbreak or llm_risk.get("jailbreak"):
        findings["jailbreak"] = ["keyword" if keyword_jailbreak else "llm"]
    if keyword_threat or llm_risk.get("threat"):
        findings["threat"] = ["keyword" if keyword_threat else "llm"]

    blocked = "threat" in findings or "jailbreak" in findings
    redacted_text, redactions = redact_pii(text)
    return GuardrailResult(
        blocked=blocked,
        redacted_text=redacted_text,
        findings=findings,
        redactions=redactions,
    )
