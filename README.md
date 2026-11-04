# Agente de atendimento — Empório da Música

Protótipo de assistente de atendimento **em português brasileiro**, com motor em Python e interface desktop Flet. Responde sobre produtos/preços/estoque consultando os CSVs e sobre políticas consultando o manual interno. Consulta pedidos por mensagens, solicitando número e e-mail cadastrado no próprio chat. A aplicação é **somente leitura**: não realiza compras, reservas nem cria chamados.

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
**Importante:** o repositório contém código e testes sintéticos. Arquivos privados do negócio precisam ser fornecidos localmente em `data/` (não versionar). Os caminhos relativos de `DATA_DIR`, `POLICY_PDF` e `SQLITE_PATH` são resolvidos pela raiz do projeto (ou pela pasta do `.exe` empacotado), independentemente de onde o programa foi iniciado.

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
- `Qual o andamento do pedido 1?` ou `quantos pedidos tenho na loja?` — consulta pedidos por número ou lista todos os pedidos vinculados ao e-mail cadastrado.
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
| Contexto de atendimento mínimo | A interface Flet mantém o identificador do último produto selecionado, sem duplicar histórico de mensagens no motor. |

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

Sessões e diálogos de teste conversacionais (incluindo consultas por e-mail, direcionamento telefônico e políticas) estão documentados em [TEST_LOGS.md](TEST_LOGS.md).

## Limitações conhecidas e evolução
- CSV é snapshot; não garante estoque/preço em tempo real nem validade temporal de promoções (`is_active` sem datas). Não há integração com ERP, WhatsApp Business API, gateways ou atendimento humano real.
- Busca de produtos por tokens é simples; nomes com sinônimos, marcas não previstas ou pedidos genéricos podem falhar. Classificação por regras pode identificar intenções ambiguamente.
- **Melhoria futura — busca por termos parciais:** reconhecer nomes reduzidos e prefixos de modelos (ex.: `Shelby SGD` → `Shelby SGD-195E`) com correspondência por prefixo, ranking, desambiguação e testes para evitar indicar modelos diferentes. Não implementado nesta entrega.
- O índice do PDF é recriado na inicialização; a recuperação lexical pode retornar trechos pouco relacionados. Validar qualidade com conjunto de perguntas de avaliação antes de produção.
- Respostas do modo OpenAI não têm verificador automático de entailment; não devem ser usadas para decisões legais sem supervisão.
- Somente a interface Flet mantém a conversa visual durante a sessão; o motor não guarda mensagens. O provedor recebe a pergunta e trechos do manual (não recebe o e-mail em consultas de pedido, pois estas são determinísticas).
- E-mail + número do pedido não substituem autenticação real. Não usar em ambiente publicamente acessível sem controles adicionais.
- Com mais tempo: autenticação OTP, integração transacional/ERP, ingestão de Excel, testes end-to-end da UI, melhor avaliação RAG, observabilidade sem PII, implantação com CI e human handoff efetivo.

## Histórico Git e aprovação
Evolução recomendada, **com commits reais e separados depois da aprovação**: `chore: estrutura e configuração`; `feat: adaptadores CSV e SQLite`; `feat: retrieval e motor de atendimento`; `feat: interface Flet`; `test: cenários e documentação`. Não fazer force-push e não reescrever histórico para aparentar trabalho incremental. As correções estão sendo desenvolvidas na branch `develop`, em commits separados.

## Uso de assistentes de código
Este projeto foi elaborado com assistência do **ChatGPT (OpenAI, GPT-6)** para revisão do manual/CSV, proposta de arquitetura, redação inicial de código, testes e documentação. As escolhas técnicas, o conteúdo do repositório e qualquer publicação devem ser revisados e aprovados pelo responsável humano. Nenhum resultado de execução deve ser apresentado como validado sem rodar o respectivo comando. Não inserir dados de clientes em prompts externos; o modo OpenAI envia apenas a pergunta de política e os trechos recuperados.


## Correções de atendimento — 2026-11-04
- Reclamações, inclusive sobre pedidos, priorizam encaminhamento humano.
- Dúvidas sobre PIX, pagamento e garantia são tratadas como políticas, não busca de produtos.
- Garantia legal de 90 dias e conflito de parcelamento são explicitados nos dois modos, sem depender de LLM.
- Preço negativo/não finito, desconto fora de 0–100% e estoque inválido bloqueiam a oferta.
- Testes usam dados sintéticos e verificam promoção ativa/inativa, PIX não cumulativo, estoque zero e descontinuação.
- O motor não retém perguntas e respostas: o histórico visual permanece apenas no Flet.

**Privacidade:** o repositório público já teve CSVs de clientes e manual interno versionados no histórico anterior. O .gitignore ou a exclusão na árvore atual não removem cópias históricas. A limpeza integral exigirá procedimento próprio de reescrita coordenada de histórico, com avaliação de impacto e rotação de credenciais caso necessário.


## Arquivos de dados locais e execução como .exe
Os arquivos privados devem permanecer **fora do Git**, dentro da pasta `data/` ao lado do projeto:

```text
agente-atendimento-mensagens/
├── data/
│   ├── politicas_da_loja.pdf
│   ├── desafio_tecnico_ai_eng - categories.csv
│   ├── desafio_tecnico_ai_eng - customers.csv
│   ├── desafio_tecnico_ai_eng - order_items.csv
│   ├── desafio_tecnico_ai_eng - orders.csv
│   ├── desafio_tecnico_ai_eng - products.csv
│   └── desafio_tecnico_ai_eng - promotions.csv
└── .env
```

Após atualizar a branch `develop`, a aplicação procura `data/` na **raiz do projeto**, independentemente da pasta em que o terminal estiver aberto. Em executáveis Python marcados como `frozen`, procura a pasta `data/` **ao lado do executável**. Se os arquivos estiverem em outro lugar, defina caminhos **absolutos** no `.env`:

```dotenv
DATA_DIR=C:/caminho/para/dados
POLICY_PDF=C:/caminho/para/dados/politicas_da_loja.pdf
```

O `.env` também deve ficar ao lado do projeto ou, no caso de executável empacotado, ao lado do `.exe`. `pip install -e '.[dev]'` instala o pacote em modo editável, mas **não cria a pasta `data/` nem gera um .exe**. Os arquivos operacionais permanecem locais e não são incluídos nos commits.


## Busca de catálogo e cache em memória (2026-11-04)
A busca reconhece categorias no singular e no plural (`violão/violões`, `guitarra/guitarras`) e filtra expressões como `disponíveis até R$ 1.000` pelo preço vigente. Não mistura a consulta de catálogo com trechos do manual de políticas.
O adaptador CSV carrega em memória somente `categories`, `products` e `promotions` na primeira consulta, evitando reler esses arquivos em cada mensagem. `customers` e `orders` **não são mantidos nesse cache**, por privacidade.
As alterações feitas nos CSVs não aparecem automaticamente: pressione **Atualizar catálogo** na interface (ou reinicie). Se a recarga falhar, a versão anterior é preservada. O cache é um snapshot local, **não é estoque em tempo real**; para produção, recomenda-se integração ao ERP/banco, com controle de atualização e concorrência.


## Atendimento contextual por modelo (2026-11-04)
O agente reconhece códigos completos de instrumento, como `Rozini RC-104`, mesmo sem categoria na mensagem. Ao identificar um modelo de maneira inequívoca, mostra descrição, preço, estoque e desconto PIX **consultados no catálogo**. A interface conserva apenas o `product_id` escolhido durante a sessão: perguntas como `e o desconto PIX?` usam esse item, sem armazenar conversas duplicadas ou dados de clientes.
Perguntas genéricas sobre PIX continuam no fluxo de políticas. Quando o usuário informa somente uma marca com vários modelos, o agente apresenta as opções e solicita especificação, sem assumir qual produto deseja.
Os preços seguem a regra de não cumulatividade: uma promoção ativa impede o desconto PIX adicional. O código do produto só é reconhecido como referência exata quando identifica unicamente um item do catálogo.


## Horário de funcionamento
Perguntas sobre horário são respondidas por regra explícita do manual (p. 2): segunda a sexta, 9h–18h; sábado, 9h–13h; domingos e feriados, fechado. Datas especiais podem alterar o horário e exigem confirmação; este protótipo não consulta calendário de exceções.


## Promoções vigentes e desconto PIX (2026-11-04)
- Perguntas como `quais as promoções ativas?` consultam `promotions.csv` e `products.csv`; campanhas descritas no PDF **não** são anunciadas como ofertas vigentes sem confirmação nos dados.
- O mês de referência é o da consulta, no fuso **America/Campo_Grande**. Campanhas sazonais previstas no manual são limitadas aos seus meses: Aniversário da Loja em agosto, Volta às Aulas em fevereiro, Black Friday e Semana do Músico em novembro.
- Promoções sem mês definido no manual dependem de `is_active=1`. Como os CSVs não possuem datas de início e fim, a validade exata precisa de confirmação antes da compra. Produtos esgotados, descontinuados ou com dados financeiros inválidos não são anunciados como promoções.
- Sempre informar em **respostas comerciais sobre promoções** que o PIX oferece 5% sobre o preço de tabela de produtos sem promoção e **não é cumulativo** com descontos promocionais. Não aplicar PIX sobre uma promoção já existente.
- Melhoria futura: adicionar `starts_at` e `ends_at` à fonte de promoções para checagem da vigência exata; preferir ERP/banco com dados sincronizados para atendimento em produção.


## Contato e endereço (2026-11-04)
Perguntas como `como contatar a loja`, `telefone`, `e-mail` e `endereço` têm respostas diretas, sem mostrar trechos aleatórios do manual. Foram confirmados na capa e no cadastro do manual: telefone **(67) 3341-4444**, e-mail **contato@emporiodamusica.com.br** (capa) e endereço **Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, CEP 79202-333**.

Solicitações diretas para falar com atendente, vendedor ou atendimento humano (ex.: `quero falar com um vendedor`, `atendente`, `falar com um humano`) direcionam para o telefone da loja **(67) 3341-4444** e esclarecem com transparência que o redirecionamento automático da conversa não está ativo neste canal demonstrativo.

**Atenção:** o próprio manual apresenta conflito entre o número indicado como telefone/WhatsApp nas páginas 1–2 e o canal principal de WhatsApp na página 6; além disso, há diferença na grafia do e-mail entre capa e cadastro. O assistente **não anuncia um WhatsApp específico como confirmado** até a loja validar o número. A resposta encaminha para conferência humana. A fonte de contato deverá ser consolidada no manual ou em configuração oficial da loja.


## Estilo de atendimento
O assistente responde como um atendente humano: cordial, descontraído sem perder o profissionalismo, com frases curtas e claras. A resposta de políticas não inicia mais com "No manual da loja consta:" nem encerra com instrução administrativa sobre a gerência. Quando necessário, oferece encaminhamento humano, sem afirmar que a transferência já aconteceu. As páginas do manual continuam disponíveis nas fontes técnicas da interface. No modo sem LLM, a resposta é um trecho curto e fiel à política; reescrita sofisticada depende do provedor LLM.


## Consulta de pedidos pelo chat — limitações e segurança
A interface **não tem campo de e-mail separado**. A consulta pode ocorrer de duas formas:
1. **Pedido específico:** O cliente solicita o andamento de um pedido e informa o número (ou o agente pede o número e em seguida o e-mail cadastrado). Só após conferir **número do pedido + e-mail correspondente no cadastro**, o agente retorna status, rastreamento e previsão registrados no CSV. Se os dados não corresponderem, o atendimento é encaminhado para conferência humana.
2. **Todos os pedidos vinculados a um e-mail:** O cliente pergunta sobre seus pedidos (ex.: `quantos pedidos tenho na loja?` ou `verifique os pedidos relacionados ao e-mail [e-mail]`). O agente solicita o e-mail se ainda não fornecido, busca o cadastro no CSV e retorna a lista de todos os pedidos vinculados (número, status, rastreamento, previsão e notas).

Exemplo conversacional: `quantos pedidos tenho na loja ?` → `Para consultar seus pedidos, por favor me informe o seu e-mail cadastrado.` → `[e-mail informado]` → `Encontrei 2 pedidos relacionados ao seu e-mail: ...`.
Também aceita consulta direta em uma única mensagem: `verifique os pedidos relacionados ao e-mail cliente@example.com` ou `Consultar pedido 1 para cliente@example.com`.

**Considerações de segurança e LGPD:**
- O chat oculta e-mails na exibição das mensagens (`[e-mail informado]`), evitando exposição visual na tela.
- O motor e a interface retêm apenas a etapa e o número do pedido em memória durante o fluxo conversacional, sem persistir o e-mail em logs ou histórico.
- Em ambiente de produção real, a listagem de pedidos por e-mail isolado **deve ser protegida por autenticação forte** (código OTP enviado por e-mail/SMS ou sessão autenticada do usuário), impedindo que terceiros obtenham relação de compras digitando o endereço de e-mail de outro consumidor.
