# Agente de atendimento — Empório da Música

Protótipo de assistente de atendimento **em português brasileiro**, com motor em Python e interface desktop Flet. Responde sobre produtos/preços/estoque consultando os CSVs e sobre políticas consultando o manual interno. Consulta pedidos apenas após cruzar número e e-mail cadastrado. A aplicação é **somente leitura**: não realiza compras, reservas nem cria chamados.

## Requisitos
- Python **3.11+**; acesso ao terminal; conexão para instalar dependências.
- Interface gráfica disponível no sistema operacional.
- Chave OpenAI **somente** se optar pelo modo com LLM; o modo `mock` funciona sem chave e é indicado para testes.

## Instalação e execução
```bash
git clone https://github.com/Trooper2123/agente-atendimento-mensagens.git
cd agente-atendimento-mensagens
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
cp .env.example .env  # Windows: copy .env.example .env
python -m emporio.app
```
**Importante:** o clone só terá esses arquivos após aprovação e publicação. Para executar o pacote entregue localmente, extraia-o e entre na pasta. Os caminhos `data/` são relativos à pasta raiz do projeto: execute os comandos a partir dela.

A configuração é feita no `.env`:
```dotenv
MODEL_PROVIDER=mock
# Para respostas geradas por LLM:
# MODEL_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
DATA_BACKEND=csv
DATA_DIR=data
POLICY_PDF=data/politicas_da_loja.pdf
```
O modelo é chamado **apenas em dúvidas sobre políticas**; preços, descontos, estoque e rastreio vêm de lógica determinística, para evitar alucinações numéricas. O modo `mock` devolve trecho literal abreviado do manual, sem linguagem natural sofisticada; não simula chamada de LLM. Para usar OpenAI, preencha a chave no `.env` e ative `MODEL_PROVIDER=openai` (custo e internet necessários). Não expor chave em prints ou commits.

## Exemplos de uso
- `Tem violão Yamaha?` — lista até cinco produtos correspondentes, com preço, estoque e promoção vigente no CSV.
- `Vocês vendem cabos?` — explica restrição de catálogo.
- `Quais são as regras de devolução?` — recupera passagem relevante do manual (no modo OpenAI, gera resposta baseada no trecho).
- `Qual o andamento do pedido 1?` — solicita e-mail cadastrado; o campo separado na interface permite informar esse dado.
- `Quero reclamar` — orienta encaminhamento humano, sem declarar abertura de chamado.

## Arquitetura e justificativas
| Decisão | Justificativa e contrapartida |
|---|---|
| Python + Flet | Stack solicitada; UI local com componentes prontos e baixa complexidade. Não é um canal real de WhatsApp. |
| `DataSource` por interface `rows(table)` | Separa fontes dos casos de uso; `CSVSource` resolve o desafio com arquivos fornecidos, `SQLiteSource` permite banco de dados local de leitura com o mesmo esquema. |
| Retrieval lexical TF-IDF simplificado (stdlib) + PyMuPDF | Recupera trechos específicos de políticas por página, sem serviço vetorial/embeddings; bom para manual pequeno e auditável. Sensível a sinônimos e divisão de blocos. |
| OpenAI opcional, via SDK | Provider conhecido e simples de configurar; `gpt-4o-mini` é valor configurável, não premissa de disponibilidade. O modo `mock` mantém execução reproduzível e sem custos. |
| Consulta determinística de negócios | O LLM não cria preços, frete, estoque, status nem códigos de rastreio. Promoções consideram `is_active`; desconto PIX só sobre preço sem promoção. |
| Prompt com contexto recuperado | Orientação de tom, fontes delimitadas, proibição de inventar e aviso para escalar conflitos; não há fine-tuning nem memória durável. |
| Fallback seguro | Erro no provedor não vira resposta fabricada; encaminha para atendimento humano. |
| Histórico limitado em memória | Mantém a sessão simples; dados não são persistidos. O exemplo atual não envia histórico anterior ao modelo. |

### Fluxo
`Flet -> Agent.ask -> classificador por regras -> {CSVSource/SQLiteSource, PolicyIndex} -> resposta determinística ou OpenAI -> UI + indicação de fontes`

### CSV hoje, banco/Excel amanhã
O projeto lê `categories`, `customers`, `order_items`, `orders`, `products` e `promotions`. Para utilizar SQLite, crie previamente tabelas de **mesmos nomes e colunas**, carregue os dados sob seus próprios procedimentos de migração, e configure `DATA_BACKEND=sqlite` e `SQLITE_PATH=data/loja.sqlite3`. O adaptador SQLite usa conexão **somente leitura**; não há script de migração ou sincronização automática nesta entrega. Para Excel, pode-se criar um adaptador `ExcelSource.rows(table)` com `openpyxl` e a mesma interface, sem alterar o motor. Para PostgreSQL/API/ERP, a mesma interface permite novo adaptador, acrescentando autenticação, autorização, atualidade e tratamento de erros.

## Conformidade com o manual
Manual `data/politicas_da_loja.pdf`, versão 2.1 (junho/2025). Regras relevantes: loja vende apenas instrumentos (p. 2); PIX 5%, crédito e parcelamento (p. 3); arrependimento em 7 dias, troca e entregas (p. 4–5); promoções não cumulativas (p. 6); WhatsApp e atendimento preciso (p. 6–7); garantia legal de 90 dias e LGPD (p. 7–8).

**Ambiguidades preservadas:** o manual menciona troca por defeito em 30 dias (p. 4) mas também garantia legal de 90 dias (p. 7); são institutos distintos e o assistente não pode negar garantia legal. A tabela de crédito informa parcela mínima de R$ 100, enquanto o detalhamento permite condições por faixas (p. 3); dúvidas concretas devem ir à equipe. Há contatos de e-mail/WhatsApp divergentes em seções do documento; confirmar dados de contato antes de divulgação automática.

## Testes e qualidade
```bash
python -m pytest -q
python -m ruff check .
```
Testes cobrem formatação de BRL, produto, proteção de pedido por e-mail, acessórios, prevenção de path traversal em tabelas e recuperação do PDF. A verificação de e-mail é apenas barreira básica de demonstração — **não é autenticação forte**. Para uso externo, exigir OTP/login, sessões, autorização por cliente, auditoria e gestão de consentimento.

## Limitações conhecidas e evolução
- CSV é snapshot; não garante estoque/preço em tempo real nem validade temporal de promoções (`is_active` sem datas). Não há integração com ERP, WhatsApp Business API, gateways ou atendimento humano real.
- Busca de produtos por tokens é simples; nomes com sinônimos, marcas não previstas ou pedidos genéricos podem falhar. Classificação por regras pode identificar intenções ambiguamente.
- O índice do PDF é recriado na inicialização; a recuperação lexical pode retornar trechos pouco relacionados. Validar qualidade com conjunto de perguntas de avaliação antes de produção.
- Respostas do modo OpenAI não têm verificador automático de entailment; não devem ser usadas para decisões legais sem supervisão.
- O protótipo mantém histórico em memória somente; o provedor recebe a pergunta e trechos do manual (não recebe o e-mail em consultas de pedido, pois estas são determinísticas).
- E-mail + número do pedido não substituem autenticação real. Não usar em ambiente publicamente acessível sem controles adicionais.
- Com mais tempo: autenticação OTP, integração transacional/ERP, ingestão de Excel, testes end-to-end da UI, melhor avaliação RAG, observabilidade sem PII, implantação com CI e human handoff efetivo.

## Histórico Git e aprovação
Evolução recomendada, **com commits reais e separados depois da aprovação**: `chore: estrutura e configuração`; `feat: adaptadores CSV e SQLite`; `feat: retrieval e motor de atendimento`; `feat: interface Flet`; `test: cenários e documentação`. Não fazer force-push e não reescrever histórico para aparentar trabalho incremental. Este pacote é uma preparação local; **ainda não foi enviado ao repositório**.

## Uso de assistentes de código
Este projeto foi elaborado com assistência do **ChatGPT (OpenAI, GPT-6)** para revisão do manual/CSV, proposta de arquitetura, redação inicial de código, testes e documentação. As escolhas técnicas, o conteúdo do repositório e qualquer publicação devem ser revisados e aprovados pelo responsável humano. Nenhum resultado de execução deve ser apresentado como validado sem rodar o respectivo comando. Não inserir dados de clientes em prompts externos; o modo OpenAI envia apenas a pergunta de política e os trechos recuperados.
