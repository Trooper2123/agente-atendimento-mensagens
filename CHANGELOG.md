# Changelog

## [Unreleased] — 2026-11-04 (BRT)
- `fix`: consultas de pedidos via etapas no próprio chat, aceitando número + e-mail na mesma mensagem, sem campo separado no Flet (`engine.py`, `app.py`).
- `security`: interface mascara endereços de e-mail exibidos e não retém o e-mail no estado da sessão; exige combinação número + e-mail e mantém ressalva sobre autenticação forte.
- `test`: regressões para consulta sequencial, e-mail incorreto, pedido em uma mensagem, reclamações e mudança de assunto.
- `docs`: README descreve a limitação de consultas por e-mail, riscos de privacidade e necessidade de OTP/login para produção.
- `style`: respostas de políticas mais naturais; removidos cabeçalhos internos e frase de confirmação pela gerência, substituídos por oferta de atendimento humano (`src/emporio/engine.py`).
- `test`: validação do tom das respostas e limite de trecho no modo sem LLM (`tests/test_engine.py`).
- `docs`: diretrizes de tom registradas no AGENTS.md e README.
- `fix`: roteamento direto para perguntas de contato, telefone, e-mail, WhatsApp e endereço, sem trechos irrelevantes do manual (`src/emporio/engine.py`).
- `test`: perguntas de contato e dados divergentes do WhatsApp cobertos por testes (`tests/test_engine.py`).
- `docs`: documentada divergência dos canais de contato no manual e necessidade de confirmação humana.
- `fix`: entrada Flet atualizada de `ft.app(target=main)` para `ft.run(main)`, removendo aviso de depreciação (`src/emporio/app.py`).
- `fix`: consultas sobre promoções ativas usam CSV, disponibilidade e mês vigente das campanhas sazonais; reforçam desconto PIX de 5% não cumulativo (`src/emporio/engine.py`).
- `test`: casos de campanhas dentro/fora do mês, promoções inativas, estoque zero, PIX e roteamento (`tests/test_engine.py`).
- `docs`: documentadas limitações dos CSVs sem datas de vigência e regras sazonais no README.
- `fix`: responder horários de funcionamento diretamente conforme o manual, inclusive domingos/feriados, sem selecionar trecho inadequado de retrieval (`src/emporio/engine.py`).
- `test`: cenários de horário de domingo, sábado, dias úteis e pergunta genérica (`tests/test_engine.py`).
- `docs`: busca de nomes parciais adicionada como melhoria futura no README, sem implementação antecipada.
- `fix`: reconhecimento de marca + código completo do modelo e resposta de PIX por produto com preço/estoque verificáveis (`src/emporio/engine.py`).
- `feat`: identificador do produto escolhido permanece apenas na sessão visual Flet, sem histórico duplicado (`src/emporio/app.py`).
- `test`: cenários de conversa Rozini RC-104, desconto PIX, referência isolada e regras de garantia (`tests/test_engine.py`).
- `docs`: registrada estratégia de contexto mínimo e limites no README.
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
