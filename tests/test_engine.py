"""Testes com dados sintéticos: sem dependência de informações reais de clientes."""
import csv
from datetime import date
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
    source.refresh_catalog()


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
    request = a.ask("pedido 1")
    assert "e-mail cadastrado" in request.message
    assert request.order_step == "email"
    denied = a.ask("outro@example.invalid", order_step=request.order_step, order_id=request.order_id)
    assert denied.handoff and "TESTE123" not in denied.message
    allowed = a.ask("cliente@example.invalid", order_step=request.order_step, order_id=request.order_id)
    assert "pedido 1" in allowed.message.lower()
    assert "TESTE123" in allowed.message
    assert allowed.order_step is None and allowed.order_id is None


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


def test_generic_category_queries_match_csv_category(source):
    # O nome pode não conter a palavra violão; a categoria contém "Violões".
    update_row(source, "products", name="Yamaha C40")
    a = agent(source)
    for question in ("violão", "Quais modelos de violão estão disponíveis?"):
        reply = a.ask(question)
        assert "Yamaha C40" in reply.message
        assert "No manual da loja" not in reply.message


def test_guitarra_singular_matches_plural_category(source):
    update_row(source, "categories", name="Guitarras")
    update_row(source, "products", name="Fender Player", category_id="cat1")
    assert "Fender Player" in agent(source).ask("guitarra").message


def test_budget_filters_and_respects_availability(source):
    a = agent(source)
    for question in (
        "Quais opções de violões disponíveis custando até R$1000?",
        "violão disponível até R$ 1.000,00",
    ):
        reply = a.ask(question)
        assert "Yamaha" in reply.message and "R$ 900,00" in reply.message
        assert "devolução" not in reply.message

    update_row(source, "products", price_brl="1500.00")
    reply = a.ask("violões disponíveis até R$1000")
    assert "não encontrei instrumentos" in reply.message.casefold()
    assert "Yamaha" not in reply.message

    update_row(source, "products", price_brl="1000.00", stock_quantity="0")
    assert "não encontrei instrumentos" in a.ask("violões disponíveis até R$1000").message.casefold()


def test_catalog_cache_is_snapshot_and_reloadable(source):
    first = source.rows("products")
    assert first[0]["stock_quantity"] == "2"
    path = source.directory / "fixture - products.csv"
    with path.open(encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    rows[0]["stock_quantity"] = "7"
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    assert source.rows("products")[0]["stock_quantity"] == "2"
    source.refresh_catalog()
    assert source.rows("products")[0]["stock_quantity"] == "7"
    source.rows("products")[0]["stock_quantity"] = "99"
    assert source.rows("products")[0]["stock_quantity"] == "7"
    assert "customers" not in source._catalog
    assert "orders" not in source._catalog


def test_exact_model_and_product_followup(source):
    update_row(source, "products", name="Rozini RC-104 Nylon Estudante",
               price_brl="459.90", description="Violão clássico de estudo.",
               stock_quantity="10")
    update_row(source, "promotions", is_active="0")
    a = agent(source)
    initial = a.ask("Rozini RC-104")
    assert initial.product_id == "p1"
    assert "Violão clássico de estudo" in initial.message
    assert "R$ 459,90" in initial.message
    assert "PIX: R$ 436,91" in initial.message
    continuation = a.ask("e o desconto PIX?", selected_product_id=initial.product_id)
    assert continuation.product_id == "p1"
    assert "R$ 436,91" in continuation.message
    assert "No manual da loja" not in continuation.message


def test_pix_on_named_brand_uses_catalog_not_manual(source):
    update_row(source, "products", name="Rozini RC-104 Nylon Estudante",
               price_brl="459.90")
    update_row(source, "promotions", is_active="0")
    reply = agent(source).ask("verifique desconto pix para o modelo Rozini")
    assert "Rozini RC-104" in reply.message
    assert "R$ 436,91" in reply.message
    assert not reply.handoff
    assert "CSV: products" in reply.sources


def test_brand_then_model_selects_exact_product(source):
    update_row(source, "products", name="Rozini RC-104 Nylon Estudante",
               price_brl="459.90", description="Modelo para estudantes.")
    a = agent(source)
    first = a.ask("mais informações sobre o modelo Rozini")
    assert "Rozini RC-104" in first.message
    exact = a.ask("Rozini RC-104")
    assert exact.product_id == "p1"
    assert "Modelo para estudantes." in exact.message


def test_generic_pix_policy_still_uses_manual(source):
    reply = agent(source).ask("Qual o desconto no PIX?")
    assert "Manual: p." in " ".join(reply.sources)
    assert "CSV: products" not in reply.sources


def test_product_warranty_not_mistaken_for_price(source):
    update_row(source, "products", name="Rozini RC-104 Nylon Estudante")
    reply = agent(source).ask("garantia do Rozini RC-104")
    assert reply.handoff and "90 dias" in reply.message
    assert reply.product_id is None


def test_both_brand_and_model_are_required_for_exact_match(source):
    update_row(source, "products", name="Rozini RC-104 Nylon Estudante")
    a = agent(source)
    reply = a.ask("Rozini")
    assert reply.product_id is None
    assert "Rozini" in reply.message


def test_brand_ambiguity_does_not_select_wrong_model(source):
    path = source.directory / "fixture - products.csv"
    with path.open(encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    rows[0].update(name="Rozini RC-104 Nylon Estudante", price_brl="459.90")
    other = dict(rows[0], product_id="p2", name="Rozini RV-174 Nylon", price_brl="1299.00")
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([rows[0], other])
    source.refresh_catalog()

    a = agent(source)
    options = a.ask("mais informações sobre o modelo Rozini")
    assert options.product_id is None
    assert "RC-104" in options.message and "RV-174" in options.message

    chosen = a.ask("Rozini RC-104")
    assert chosen.product_id == "p1"
    assert "RC-104" in chosen.message and "RV-174" not in chosen.message

    followup = a.ask("e quanto custa?", selected_product_id=chosen.product_id)
    assert followup.product_id == "p1"
    assert "R$ 459,90" in followup.message
    assert "R$ 1.299,00" not in followup.message


@pytest.mark.parametrize("question,expected", [
    ("horario de funcionamento aos domingos", "não abre aos domingos e feriados"),
    ("Vocês abrem domingo?", "não abre aos domingos e feriados"),
    ("Qual o horário de sábado?", "sábados, funcionamos das 9h às 13h"),
    ("Que horas abre de segunda a sexta?", "segunda a sexta-feira, funcionamos das 9h às 18h"),
    ("Qual o horário de funcionamento?", "Domingos e feriados, fechamos"),
])
def test_opening_hours_from_manual(source, question, expected):
    a = agent(source)
    reply = a.ask(question, selected_product_id="p1")
    assert expected in reply.message
    assert reply.sources == ["Manual: p. 2"]
    assert "No manual da loja consta" not in reply.message
    assert not reply.handoff


def test_current_promotions_route_to_catalog_not_pdf(source, monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls, tz=None):
            from datetime import datetime
            return datetime(2026, 11, 4, tzinfo=tz)

    from emporio import engine
    monkeypatch.setattr(engine, "datetime", FakeDateTime)
    reply = agent(source).ask("quais as promoções ativas?")
    assert "Promoções disponíveis neste mês" in reply.message
    assert "Yamaha" in reply.message and "R$ 900,00" in reply.message
    assert "5% de desconto" in reply.message
    assert "não é cumulativo" in reply.message
    assert "No manual da loja consta" not in reply.message
    assert reply.sources[0] == "CSV: promotions"


def test_campaign_only_in_its_manual_month(source):
    update_row(source, "promotions", description="Black Friday", is_active="1")
    a = agent(source)
    november = a._promotions_response(reference_date=date(2026, 11, 4))
    august = a._promotions_response(reference_date=date(2026, 8, 4))
    assert "Yamaha" in november.message
    assert "Não há promoções" in august.message
    assert "5% de desconto" in august.message


def test_inactive_promotions_not_offered_even_in_campaign_month(source):
    update_row(source, "promotions", description="Black Friday", is_active="0")
    reply = agent(source)._promotions_response(reference_date=date(2026, 11, 27))
    assert "Não há promoções" in reply.message
    assert "Yamaha" not in reply.message
    assert "PIX" in reply.message


def test_unavailable_product_not_advertised_as_promotion(source):
    update_row(source, "products", stock_quantity="0")
    reply = agent(source)._promotions_response(reference_date=date(2026, 11, 4))
    assert "Não há promoções" in reply.message


def test_seasonal_promotion_not_applied_to_product_outside_month(source, monkeypatch):
    update_row(source, "promotions", description="Aniversário da Loja")
    class FakeDateTime:
        @classmethod
        def now(cls, tz=None):
            from datetime import datetime
            return datetime(2026, 11, 4, tzinfo=tz)
    from emporio import engine
    monkeypatch.setattr(engine, "datetime", FakeDateTime)
    text = agent(source).ask("violão Yamaha").message
    assert "R$ 1.000,00" in text
    assert "PIX: R$ 950,00" in text
    assert "R$ 900,00" not in text


@pytest.mark.parametrize("question", [
    "como contatar a loja",
    "contato da loja",
    "qual o telefone?",
    "qual o email?",
])
def test_contact_questions_return_verified_channels(source, question):
    reply = agent(source).ask(question, selected_product_id="p1")
    assert "(67) 3341-4444" in reply.message
    assert "contato@emporiodamusica.com.br" in reply.message
    assert "No manual da loja consta:" not in reply.message
    assert "CSV: products" not in reply.sources
    assert reply.handoff  # WhatsApp conflitante no manual, confirmação necessária.


def test_whatsapp_ambiguity_is_not_hidden(source):
    reply = agent(source).ask("qual o whatsapp da loja?")
    assert "precisa ser confirmado" in reply.message
    assert "(67) 3321-4500" not in reply.message
    assert reply.handoff


def test_address_has_direct_answer(source):
    reply = agent(source).ask("qual endereço da loja?")
    assert "Rua 14 de Maio, 3200" in reply.message
    assert "Campo Grande" in reply.message
    assert not reply.handoff


def test_policy_reply_has_human_tone_without_internal_boilerplate(source):
    reply = agent(source).ask("Qual é a forma de pagamento?")
    assert reply.message.startswith("Claro!")
    assert "desconto de 5%" in reply.message
    assert "Se tiver alguma dúvida, posso encaminhar você para um atendente humano." in reply.message
    assert "No manual da loja consta:" not in reply.message
    assert "Se houver dúvida sobre a aplicação da regra, a gerência deve confirmar." not in reply.message
    assert reply.sources == ["Manual: p. 3"]


def test_short_policy_excerpt_not_cut_midword(source):
    class LongIndex:
        def search(self, query, limit=3):
            return [{"page": 4, "text": "Informação confirmada sobre atendimento. " + "Detalhes complementares. " * 50}]
    reply = Agent(source, LongIndex(), "mock").ask("Como funciona o atendimento?")
    assert len(reply.message) < 550
    assert "Detalhes complementares." in reply.message
    assert "No manual da loja consta" not in reply.message


def test_order_consultation_with_email_inside_chat(source):
    a = agent(source)
    first = a.ask("qual o andamento do pedido 1?")
    assert first.order_step == "email" and first.order_id == "1"
    assert "e-mail cadastrado" in first.message
    assert "TESTE123" not in first.message

    last = a.ask("cliente@example.invalid", order_step=first.order_step, order_id=first.order_id)
    assert "TESTE123" in last.message
    assert last.order_step is None and last.order_id is None


def test_order_single_message_with_number_and_email(source):
    reply = agent(source).ask("Consultar pedido 1 para cliente@example.invalid")
    assert "TESTE123" in reply.message
    assert reply.order_step is None


def test_order_consultation_all_orders_by_email(source):
    a = agent(source)
    # 1. Consulta direta por e-mail com pedidos relacionados
    reply = a.ask("verifique os pedidos relacionados ao e-mail cliente@example.invalid")
    assert "TESTE123" in reply.message
    assert "Pedido 1" in reply.message
    assert reply.order_step is None

    # 2. Pergunta sobre quantidade -> solicita e-mail -> retorna pedidos do e-mail
    first = a.ask("quantos pedidos tenho na loja ?")
    assert first.order_step == "email"
    assert "e-mail cadastrado" in first.message.lower()

    second = a.ask("cliente@example.invalid", order_step=first.order_step, order_id=first.order_id)
    assert "TESTE123" in second.message
    assert "Pedido 1" in second.message
    assert second.order_step is None


def test_order_consultation_multiple_orders_by_email(source):
    path = source.directory / "fixture - orders.csv"
    with path.open(encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    rows.append({
        "order_id": "2",
        "customer_id": "c1",
        "status": "cancelado",
        "tracking_code": "",
        "estimated_delivery": "",
    })
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["order_id", "customer_id", "status", "tracking_code", "estimated_delivery"])
        writer.writeheader()
        writer.writerows(rows)

    a = agent(source)
    reply = a.ask("verifique os pedidos relacionados ao e-mail cliente@example.invalid")
    assert "Encontrei 2 pedidos" in reply.message
    assert "Pedido 1" in reply.message
    assert "Pedido 2" in reply.message
    assert "TESTE123" in reply.message
    assert "cancelado" in reply.message


def test_order_consultation_email_not_found(source):
    a = agent(source)
    reply = a.ask("verifique os pedidos relacionados ao e-mail inexistente@example.invalid")
    assert reply.handoff
    assert "Não encontrei nenhum cadastro" in reply.message


def test_order_consultation_email_without_orders(source):
    path = source.directory / "fixture - customers.csv"
    with path.open("a", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["c2", "sem.pedidos@example.invalid"])

    a = agent(source)
    reply = a.ask("verifique os pedidos relacionados ao e-mail sem.pedidos@example.invalid")
    assert not reply.handoff
    assert "Não encontrei nenhum pedido vinculado" in reply.message


def test_order_wrong_email_denied_and_unrelated_safe(source):
    a = agent(source)
    wrong = a.ask("pedido 1 atacante@example.invalid")
    assert wrong.handoff
    assert "TESTE123" not in wrong.message

    # E-mails isolados e não relacionados não consultam pedidos.
    unrelated = a.ask("cliente@example.invalid")
    assert "TESTE123" not in unrelated.message


def test_complaints_override_pending_order(source):
    reply = agent(source).ask(
        "Quero reclamar do pedido 1", order_step="email", order_id="1"
    )
    assert reply.handoff
    assert reply.order_step is None
    assert "TESTE123" not in reply.message


def test_order_context_is_discarded_when_topic_changes(source):
    reply = agent(source).ask("qual o horário?", order_step="email", order_id="1")
    assert reply.order_step is None
    assert "9h" in reply.message
