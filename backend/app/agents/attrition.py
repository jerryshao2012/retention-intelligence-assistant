import re
from typing import Any, Dict, List, Optional

import pandas as pd


def _parse_top_n(text: str) -> Optional[int]:
    match = re.search(r"top\s+(\d+)", text.lower())
    if match:
        return int(match.group(1))
    return None


def rank_at_risk(customers: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
    ordered = customers.sort_values(by="churn_risk_score", ascending=False)
    cols = [
        "customer_id",
        "name",
        "email",
        "segment",
        "product",
        "churn_risk_score",
        "reason",
    ]
    return ordered.head(top_n)[cols].to_dict(orient="records")


def run_attrition(customers: pd.DataFrame, user_input: str, customer_id: Optional[str]) -> Dict[str, Any]:
    top_n = _parse_top_n(user_input) or 10
    if customer_id:
        row = customers[customers["customer_id"] == customer_id]
        if not row.empty:
            return {
                "mode": "single",
                "customer": row.iloc[0].to_dict(),
            }
    if "top" in user_input.lower() or "at-risk" in user_input.lower() or "attrit" in user_input.lower():
        return {
            "mode": "ranked_list",
            "customers": rank_at_risk(customers, top_n=top_n),
        }
    return {
        "mode": "ranked_list",
        "customers": rank_at_risk(customers, top_n=top_n),
    }
