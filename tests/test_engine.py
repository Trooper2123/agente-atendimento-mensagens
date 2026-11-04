from decimal import Decimal

from emporio.data import CSVSource, SQLiteSource
from emporio.engine import Agent, brl
from emporio.retrieval import PolicyIndex, tokens


class IndexStub:
    def search(self, query, limit=3):
        return [{"page": 3, "text": "O pagamento por PIX tem desconto de 5%."}]


def agent():
    return Agent(CSVSource("data"), IndexStub(), "mock")


def test_money():
    assert brl(Decimal("1234.5")) == "R$ 1.234,50"


def test_stock_and_promotion_are_real():
    response = agent().ask("violão yamaha")
    assert "Yamaha" in response.message
    assert "CSV: products" in response.sources


def test_order_requires_email_and_matches_owner():
    a = agent()
    assert "e-mail cadastrado" in a.ask("pedido 1").message
    denied = a.ask("pedido 1", email="atacante@exemplo.com")
    assert denied.handoff and "rastreamento:" not in denied.message
    import csv
    with open("data/desafio_tecnico_ai_eng - orders.csv", newline="", encoding="utf-8") as file:
        order = next(csv.DictReader(file))
    with open("data/desafio_tecnico_ai_eng - customers.csv", newline="", encoding="utf-8") as file:
        customer = next(row for row in csv.DictReader(file) if row["customer_id"] == order["customer_id"])
    allowed = a.ask("pedido 1", email=customer["email"])
    assert "Pedido 1:" in allowed.message


def test_accessories_not_sold():
    assert "não com acessórios" in agent().ask("Vocês vendem cabos?").message


def test_bad_table_rejected():
    import pytest
    with pytest.raises(ValueError):
        CSVSource("data").rows("../../customers")


def test_token_accents():
    assert "violao" in tokens("violão")


def test_pdf_retrieval():
    index = PolicyIndex("data/politicas_da_loja.pdf")
    found = index.search("direito arrependimento devolução sete dias")
    assert found and any(p["page"] == 4 for p in found)
