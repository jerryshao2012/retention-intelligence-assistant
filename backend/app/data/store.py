import json
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_customers():
    return pd.read_csv(DATA_DIR / "customers.csv")


def load_offers():
    with open(DATA_DIR / "offers.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_product_catalog():
    with open(DATA_DIR / "product_catalog.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_knowledge():
    with open(DATA_DIR / "knowledge.json", "r", encoding="utf-8") as f:
        return json.load(f)
