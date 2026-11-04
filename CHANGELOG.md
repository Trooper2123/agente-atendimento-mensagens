# Changelog

## [Unreleased] — 2026-11-04 (BRT)
- `refactor`: removido histórico duplicado sem uso (`src/emporio/engine.py`).
- `fix`: reclamações sobre pedidos recebem encaminhamento humano (`src/emporio/engine.py`).
- `fix`: perguntas de PIX/garantia passam pelo fluxo de políticas (`src/emporio/engine.py`).
- `fix`: conflitos de defeito/garantia e parcelamento tratados sem depender de LLM (`src/emporio/engine.py`).
- `fix`: validação de preço, percentual e estoque recusa ofertas inválidas (`src/emporio/engine.py`).
- `test`: fixtures sintéticas e casos de promoção, PIX, estoque e descontinuação (`tests/test_engine.py`).
- `docs`: README atualizado com mudanças e riscos de privacidade.


## [Unreleased] — 2026-11-03 (BRT)
- `chore`: criada estrutura Python, configuração e `.gitignore` (`pyproject.toml`, `.env.example`).
- `feat`: implementados adaptadores CSV/SQLite somente leitura (`src/emporio/data.py`).
- `feat`: recuperação lexical das páginas do PDF e engine de consulta de catálogo/pedido (`retrieval.py`, `engine.py`).
- `feat`: interface local com Flet (`app.py`).
- `test`: casos unitários de preços, permissões básicas, catálogo e PDF (`tests/test_engine.py`).
- `docs`: README detalhado, limitações, divulgação do uso de IA e AGENTS.md adaptado.
- Situação: versão base publicada; correções desenvolvidas na branch `develop`.
