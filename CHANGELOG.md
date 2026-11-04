# Changelog

## [Unreleased] — 2026-11-04 (BRT)
- `refactor`: substituído `import fitz` por `import pymupdf` na recuperação de políticas (`src/emporio/retrieval.py`).
- `test`: adicionada validação de leitura de PDF com PyMuPDF (`tests/test_retrieval.py`).
- `feat`: cache em memória restrito a categorias, produtos e promoções; recarga explícita e botão Flet (`src/emporio/data.py`, `src/emporio/app.py`).
- `fix`: busca de catálogo com singular/plural, filtro de preço e estoque disponível, sem roteamento acidental ao manual (`src/emporio/engine.py`).
- `test`: testes sintéticos adicionados para categorias, consultas orçamentárias, estoque e recarga (`tests/test_engine.py`).
- `docs`: README registra funcionamento e limitações do cache.
- `fix`: caminhos relativos de dados, SQLite, PDF e `.env` resolvidos pela raiz do projeto ou pasta de executável empacotado (`src/emporio/data.py`, `src/emporio/app.py`).
- `test`: adicionados testes para execução fora da raiz, override de caminho absoluto e modo executável (`tests/test_paths.py`); 26 testes passaram localmente, compilação Python aprovada; interface `.exe` e Ruff não verificados.
- `docs`: README documenta organização local dos arquivos e execução como `.exe`.
- `security`: adicionada regra `data/` ao `.gitignore` e excluídos da árvore atual os seis CSVs operacionais e o PDF interno na branch `develop` (`.gitignore`, `data/*`). Os objetos continuam no histórico público antigo e na branch `main`.
- `test`: suíte equivalente local com 23 testes aprovada; compilação Python aprovada. Ruff não instalado, verificação pendente.
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
