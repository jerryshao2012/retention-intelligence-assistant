from typing import Any, Dict


def segment_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
    balance = float(customer.get("avg_balance", 0))
    tenure = int(customer.get("tenure_months", 0))
    complaints = int(customer.get("complaints_90d", 0))

    if balance >= 100000:
        segment = "High-Net-Worth"
    elif tenure < 12:
        segment = "New-to-Bank"
    elif complaints >= 2:
        segment = "Service-Recovery"
    else:
        segment = "Mass Affluent"

    return {
        "segment": segment,
        "signals": {
            "avg_balance": balance,
            "tenure_months": tenure,
            "complaints_90d": complaints,
        },
    }
