"""Garante a abertura do PDF com o módulo público pymupdf."""
import pymupdf

from emporio.retrieval import PolicyIndex


def test_policy_index_uses_pymupdf(tmp_path):
    path = tmp_path / "manual_teste.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((40, 40), "Politica demonstrativa de pagamento por PIX para atendimento ao cliente.")
        pdf.save(path)

    passages = PolicyIndex(path).search("pagamento PIX")
    assert passages and passages[0]["page"] == 1
