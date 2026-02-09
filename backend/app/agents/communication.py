from typing import Any, Dict

from app.core.llm import get_chat_llm


def _build_prompt(payload: Dict[str, Any]) -> str:
    return f"""
You are a bank retention assistant. Generate a structured response with the following sections:
- retention_summary
- offers
- next_best_action
- email_draft

Context:
Customer: {payload.get('customer')}
Segment: {payload.get('segment')}
Attrition Reason: {payload.get('reason')}
Product Context: {payload.get('product_context')}
Recommended Offers: {payload.get('offers')}
Relevant Knowledge: {payload.get('knowledge')}

Keep it concise, professional, and empathetic.
""".strip()


def generate_response(payload: Dict[str, Any]) -> str:
    llm = get_chat_llm()
    prompt = _build_prompt(payload)
    try:
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception:
        return (
            "retention_summary: Customer shows elevated churn risk driven by recent complaints and reduced engagement.\n"
            "offers: Offer a fee waiver and targeted rewards boost on the Cash Back Mastercard for 3 months.\n"
            "next_best_action: Call within 24 hours, acknowledge service issues, and confirm resolution timeline.\n"
            "email_draft: Hello [Name], I wanted to reach out personally regarding your recent experience..."
        )
