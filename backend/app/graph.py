from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import StateGraph, END

from app.agents.attrition import run_attrition
from app.agents.segmentation import segment_customer
from app.agents.rag import build_product_context, build_semantic_index, find_offers, semantic_retrieve
from app.agents.communication import generate_response
from app.data.store import load_customers, load_offers, load_product_catalog, load_knowledge


class RetentionState(TypedDict, total=False):
    user_input: str
    customer_id: Optional[str]
    approve_email: bool
    approve_email_content: Optional[str]
    attrition: Dict[str, Any]
    segment: Dict[str, Any]
    offers: Any
    product_context: Any
    semantic_hits: Any
    response_text: str


CUSTOMERS = load_customers()
OFFERS = load_offers()
PRODUCT_CATALOG = load_product_catalog()
KNOWLEDGE = load_knowledge()
SEMANTIC_INDEX = build_semantic_index(OFFERS, KNOWLEDGE)


def attrition_node(state: RetentionState) -> RetentionState:
    attrition = run_attrition(CUSTOMERS, state["user_input"], state.get("customer_id"))
    return {"attrition": attrition}


def segmentation_node(state: RetentionState) -> RetentionState:
    if state["attrition"]["mode"] == "single":
        customer = state["attrition"]["customer"]
    else:
        customer = state["attrition"]["customers"][0]
    segment = segment_customer(customer)
    return {"segment": segment}


def rag_node(state: RetentionState) -> RetentionState:
    if state["attrition"]["mode"] == "single":
        customer = state["attrition"]["customer"]
    else:
        customer = state["attrition"]["customers"][0]
    reason = customer.get("reason", "general")
    offers = find_offers(OFFERS, state["segment"]["segment"], reason)
    product_context = build_product_context(PRODUCT_CATALOG, customer.get("product"))
    query = f"{reason} {state['segment']['segment']} {customer.get('product', '')}"
    semantic_hits = semantic_retrieve(SEMANTIC_INDEX, query, top_k=3)
    return {"offers": offers, "product_context": product_context, "semantic_hits": semantic_hits}


def communication_node(state: RetentionState) -> RetentionState:
    if state["attrition"]["mode"] == "single":
        customer = state["attrition"]["customer"]
    else:
        # If user requested a ranked list, return a table instead of an email draft.
        if "customers" in state["attrition"] and ("top" in state["user_input"].lower() or "at-risk" in state["user_input"].lower()):
            rows = state["attrition"]["customers"]
            header = "| Rank | Customer | Segment | Risk | Reason | Email |\n|---|---|---|---|---|---|"
            lines = [
                f"| {idx+1} | {row['name']} ({row['customer_id']}) | {row['segment']} | {row['churn_risk_score']:.2f} | {row['reason']} | {row['email']} |"
                for idx, row in enumerate(rows)
            ]
            return {"response_text": "\n".join([header, *lines])}
        customer = state["attrition"]["customers"][0]

    user_text = state["user_input"].lower()
    wants_email = any(k in user_text for k in ["email", "draft", "send"])
    if state.get("approve_email", False) and state.get("approve_email_content"):
        approved = state["approve_email_content"]
        return {
            "response_text": (
                "Approval recorded. Here is the final email content:\n\n"
                f"email_draft:\n{approved}"
            )
        }

    payload = {
        "customer": customer,
        "segment": state["segment"]["segment"],
        "reason": customer.get("reason", "general"),
        "offers": state["offers"],
        "product_context": state["product_context"],
        "knowledge": state.get("semantic_hits", []),
    }
    response_text = generate_response(payload)
    if wants_email and "email_draft" not in response_text.lower():
        response_text = response_text + "\n\nemail_draft:\n(Provide the drafted email here.)"
    return {"response_text": response_text}


def build_graph():
    graph = StateGraph(RetentionState)
    graph.add_node("attrition_node", attrition_node)
    graph.add_node("segmentation_node", segmentation_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("communication_node", communication_node)

    graph.set_entry_point("attrition_node")
    graph.add_edge("attrition_node", "segmentation_node")
    graph.add_edge("segmentation_node", "rag_node")
    graph.add_edge("rag_node", "communication_node")
    graph.add_edge("communication_node", END)
    return graph.compile()
