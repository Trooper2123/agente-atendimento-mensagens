"""Testes com dados sintéticos: sem dependência de informações reais de clientes."""
import csv
from decimal import Decimal

import pytest

from emporio.data import CSVSource
from emporio.engine import Agent, brl
from emporio.retrieval import tokens


class IndexStub:
    def search(self, query, limit=3):
        return [{"page": 3, "text": "O pagamento por PIX tem desconto de 5%."}]


@pytest.fixture
def source(tmp_path):
    tables = {
        "categories": (["category_id", "name"], [["cat1", "Violões"]]),
        "products": (
            ["product_id", "name", "category_id", "price_brl", "stock_quantity", "status"],
            [["p1", "Violão Yamaha de demonstração", "cat1", "1000.00", "2", "active"]],
        ),
        "promotions": (
            ["promotion_id", "product_id", "discount_percent", "is_active"],
            [["pr1", "p1", "10", "1"]],
        ),
        "orders": (
            ["order_id", "customer_id", "status", "tracking_code", "estimated_delivery"],
            [["1", "c1", "enviado", "TESTE123", "2026-01-10"]],
        ),
        "customers": (
            ["customer_id", "email"], [["c1", "cliente@example.invalid"]],
        ),
    }
    for table, (columns, records) in tables.items():
        with (tmp_path / f"fixture - {table}.csv").open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(columns)
            writer.writerows(records)
    return CSVSource(tmp_path)


def agent(source, provider="mock"):
    return Agent(source, IndexStub(), provider)


def update_row(source, table, **changes):
    path = source.directory / f"fixture - {table}.csv"
    with path.open(encoding="utf-8") as fp:
        records = list(csv.DictReader(fp))
    records[0].update(changes)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def test_brl():
    assert brl(Decimal("1234.50")) == "R$ 1.234,50"


def test_tokens():
    assert "violao" in tokens("violão")


def test_no_duplicate_history(source):
    a = agent(source)
    a.ask("violão Yamaha")
    assert not hasattr(a, "history")


def test_order_privacy(source):
    a = agent(source)
    assert "e-mail cadastrado" in a.ask("pedido 1").message
    assert a.ask("pedido 1", email="outro@example.invalid").handoff
    assert "Pedido 1" in a.ask("pedido 1", email="cliente@example.invalid").message


def test_complaint_is_prioritized(source):
    reply = agent(source).ask("Quero reclamar do pedido 1")
    assert reply.handoff
    assert "24 horas úteis" in reply.message
    assert "e-mail cadastrado" not in reply.message


@pytest.mark.parametrize("question", ["Qual o desconto no PIX?", "Qual a garantia Yamaha?"])
def test_policy_before_catalog(source, question):
    reply = agent(source).ask(question)
    assert "modelo correspondente" not in reply.message
    assert "Manual:" in " ".join(reply.sources)


@pytest.mark.parametrize("provider", ["mock", "openai"])
def test_defect_conflict(source, provider):
    reply = agent(source, provider).ask("Produto com defeito e garantia?")
    assert reply.handoff and "30 dias" in reply.message and "90 dias" in reply.message


@pytest.mark.parametrize("provider", ["mock", "openai"])
def test_installment_conflict(source, provider):
    reply = agent(source, provider).ask("Qual o parcelamento?")
    assert reply.handoff and "confirmar" in reply.message


@pytest.mark.parametrize("field,value", [
    ("price_brl", "-1"), ("price_brl", "NaN"), ("price_brl", "Infinity"),
    ("stock_quantity", "-1"), ("stock_quantity", "2.5"),
])
def test_bad_product_values(source, field, value):
    update_row(source, "products", **{field: value})
    reply = agent(source).ask("violão Yamaha")
    assert reply.handoff and "R$" not in reply.message


@pytest.mark.parametrize("percent", ["150", "-1", "NaN", "Infinity", "abc"])
def test_bad_discount(source, percent):
    update_row(source, "promotions", discount_percent=percent)
    reply = agent(source).ask("violão Yamaha")
    assert reply.handoff and "R$" not in reply.message


def test_stock_and_promotion_matrix(source):
    a = agent(source)
    active = a.ask("violão Yamaha").message
    assert "R$ 900,00" in active and "R$ 1.000,00" in active
    assert "10% de desconto" in active and "sem PIX adicional" in active
    assert "2 em estoque" in active and "R$ 855,00" not in active

    update_row(source, "promotions", is_active="0")
    inactive = a.ask("violão Yamaha").message
    assert "R$ 1.000,00" in inactive and "PIX: R$ 950,00" in inactive
    assert "R$ 900,00" not in inactive

    update_row(source, "products", stock_quantity="0")
    assert "temporariamente esgotado" in a.ask("violão Yamaha").message

    update_row(source, "products", stock_quantity="5", status="discontinued")
    stopped = a.ask("violão Yamaha").message
    assert "descontinuado" in stopped and "5 em estoque" not in stopped


def test_accessories(source):
    assert "não com acessórios" in agent(source).ask("Vendemos cabos?").message


def test_table_whitelist(source):
    with pytest.raises(ValueError):
        source.rows("../../customers")
