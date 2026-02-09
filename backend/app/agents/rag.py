from typing import Any, Dict, List

from app.rag.semantic import CorpusItem, SemanticIndex


def find_offers(offers_catalog: List[Dict[str, Any]], segment: str, reason: str) -> List[Dict[str, Any]]:
    matches = []
    for offer in offers_catalog:
        if segment in offer["segments"] and reason in offer["reasons"]:
            matches.append(offer)
    if not matches:
        matches = [o for o in offers_catalog if segment in o["segments"]]
    return matches[:3]


def build_product_context(product_catalog: Dict[str, Any], product_name: str) -> Dict[str, Any]:
    return product_catalog.get(product_name, {})


def build_semantic_index(offers: List[Dict[str, Any]], knowledge: List[Dict[str, Any]]) -> SemanticIndex:
    items: List[CorpusItem] = []
    for offer in offers:
        text = f"Offer: {offer['name']}. Segments: {', '.join(offer['segments'])}. Reasons: {', '.join(offer['reasons'])}. Details: {offer['details']}"
        items.append(CorpusItem(id=offer["id"], text=text, payload={"type": "offer", **offer}))
    for doc in knowledge:
        text = f"{doc['title']}: {doc['content']}"
        items.append(CorpusItem(id=doc["id"], text=text, payload={"type": "knowledge", **doc}))
    return SemanticIndex(items)


def semantic_retrieve(index: SemanticIndex, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    results = index.search(query, top_k=top_k)
    return [
        {
            "score": score,
            **item.payload,
        }
        for item, score in results
    ]
