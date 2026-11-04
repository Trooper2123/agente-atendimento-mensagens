# Logs de Teste — Empório da Música (Assistente de Atendimento)

Este documento registra sessões de teste e interações conversacionais realizadas durante o desenvolvimento e validação do protótipo de atendimento.

> [!IMPORTANT]
> **Privacidade e LGPD:**
> - Nunca registre e-mails de clientes reais em logs públicos ou commits.
> - Utilize a máscara visual do chat `[e-mail informado]` ou endereços fictícios de teste sintético (`cliente@example.invalid`).
> - Não registre chaves de API, senhas ou dados sensíveis.

---

## Índice de Sessões de Teste
- [Sessão 1: Verificação de Todos os Pedidos por E-mail](#sessão-1-verificação-de-todos-os-pedidos-por-e-mail)
- [Sessão 2: Consulta de Pedido Específico (Número + E-mail)](#sessão-2-consulta-de-pedido-específico-número--e-mail)
- [Sessão 3: Solicitação de Atendente / Vendedor e Direcionamento Telefônico](#sessão-3-solicitação-de-atendente--vendedor-e-direcionamento-telefônico)
- [Sessão 4: Consulta de Catálogo, Estoque e Desconto PIX](#sessão-4-consulta-de-catálogo-estoque-e-desconto-pix)
- [Sessão 5: Conflitos Normativos e Políticas (Garantia e Parcelamento)](#sessão-5-conflitos-normativos-e-políticas-garantia-e-parcelamento)
- [Sessão 6: Tratamento de Reclamações](#sessão-6-tratamento-de-reclamações)
- [Template para Novos Registros](#template-para-novos-registros)

---

## Sessão 1: Verificação de Todos os Pedidos por E-mail
- **Data:** 2026-11-04
- **Objetivo:** Validar a consulta de quantidade e situação de múltiplos pedidos vinculados a um cadastro por e-mail.
- **Canal:** Chat Desktop Flet / Motor Python determinístico.

### Diálogo 1.1 — Fluxo conversacional em etapas
```text
Você: quantos pedidos tenho na loja ?
Empório: Claro! Para consultar seus pedidos, por favor me informe o seu e-mail cadastrado. Se preferir consultar um pedido específico, pode informar o número dele.
[Fontes: Manual: p. 7]

Você: verifique os pedidos relacionados so e-mail [e-mail informado]
Empório: Encontrei 2 pedidos relacionados ao seu e-mail:
• Pedido 1: situação delivered. Código de rastreamento: BRAB1234567BR. Previsão cadastrada: 2025-10-25 (sujeita a atualização).
• Pedido 19: situação cancelled. Observação: Pagamento não confirmado dentro do prazo.
[Fontes: CSV: orders; CSV: customers]
```
- **Resultado:** Aprovado. A contagem de pedidos e o detalhamento individual com rastreio/observações foram exibidos corretamente.

### Diálogo 1.2 — E-mail não encontrado no cadastro
```text
Você: verifique os pedidos relacionados ao e-mail inexistente@example.invalid
Empório: Não encontrei nenhum cadastro com o e-mail informado. Se quiser, posso encaminhar você para um atendente humano.
[Fontes: CSV: customers]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Dispara `handoff=True` sem vazar informações de outros clientes.

---

## Sessão 2: Consulta de Pedido Específico (Número + E-mail)
- **Data:** 2026-11-04
- **Objetivo:** Validar a autenticação básica de 2 fatores demonstrativos (número do pedido + e-mail do titular).

### Diálogo 2.1 — Consulta sequencial
```text
Você: qual o andamento do pedido 1?
Empório: Obrigado! Agora me informe o e-mail cadastrado no pedido 1, por favor.
[Fontes: Manual: p. 7–8]

Você: [e-mail informado]
Empório: Encontrei o pedido 1! A situação atual é: delivered. Código de rastreamento: BRAB1234567BR. Previsão cadastrada: 2025-10-25 (sujeita a atualização).
[Fontes: CSV: orders; CSV: customers]
```
- **Resultado:** Aprovado. O motor reteve o `order_id="1"` durante o turno e confirmou com o e-mail.

### Diálogo 2.2 — Tentativa com e-mail incorreto (proteção de titularidade)
```text
Você: pedido 1 atacante@example.invalid
Empório: Não consegui confirmar esse pedido com os dados informados. Se quiser, posso encaminhar você para um atendente humano.
[Fontes: CSV: orders; CSV: customers]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Dados do pedido não são exibidos quando o e-mail não confere.

---

## Sessão 3: Solicitação de Atendente / Vendedor e Direcionamento Telefônico
- **Data:** 2026-11-04
- **Objetivo:** Garantir que pedidos explícitos de falar com um humano/vendedor sejam direcionados ao telefone oficial da loja, explicitando que a conversa não é transferida automaticamente.

### Diálogo 3.1 — Solicitação de vendedor
```text
Você: quero falar com um vendedor
Empório: O redirecionamento da conversa não está ativo neste canal. Para falar com nossa equipe de atendimento ou com um vendedor, por favor entre em contato pelo telefone da loja: (67) 3341-4444.
[Fontes: Manual: p. 1 e 2]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Direcionamento para telefone (67) 3341-4444 e esclarecimento de ausência de transferência automática.

### Diálogo 3.2 — Termo isolado "atendente"
```text
Você: atendente
Empório: O redirecionamento da conversa não está ativo neste canal. Para falar com nossa equipe de atendimento ou com um vendedor, por favor entre em contato pelo telefone da loja: (67) 3341-4444.
[Fontes: Manual: p. 1 e 2]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Não recupera mais trechos genéricos do manual de procedimentos internos.

---

## Sessão 4: Consulta de Catálogo, Estoque e Desconto PIX
- **Data:** 2026-11-04
- **Objetivo:** Verificar busca de modelos, exibição de estoque e regra de 5% de desconto no PIX (apenas sobre itens sem promoção ativa).

### Diálogo 4.1 — Identificação exata de modelo e follow-up de PIX
```text
Você: Rozini RC-104
Empório: • Rozini RC-104 Nylon Estudante: R$ 459,90 (PIX: R$ 436,91 se elegível); 10 em estoque.
Descrição: Violão clássico de estudo.
Posso ajudar com mais alguma informação?
[Fontes: CSV: products; CSV: promotions; Manual: p. 3 e 6]

Você: e o desconto PIX?
Empório: • Rozini RC-104 Nylon Estudante: R$ 459,90 (PIX: R$ 436,91 se elegível); 10 em estoque.
Descrição: Violão clássico de estudo.
Posso ajudar com mais alguma informação?
[Fontes: CSV: products; CSV: promotions; Manual: p. 3 e 6]
```
- **Resultado:** Aprovado. O contexto manteve o `selected_product_id` sem persistir histórico integral de chat.

### Diálogo 4.2 — Promoção ativa sem cumulatividade com PIX
```text
Você: violão Yamaha
Empório: • Violão Yamaha de demonstração: R$ 900,00 (de R$ 1.000,00, 10% de desconto; sem PIX adicional); 2 em estoque.
Posso ajudar com mais alguma informação?
[Fontes: CSV: products; CSV: promotions; Manual: p. 3 e 6]
```
- **Resultado:** Aprovado. Não acumulou 5% do PIX sobre o produto promocional.

---

## Sessão 5: Conflitos Normativos e Políticas (Garantia e Parcelamento)
- **Data:** 2026-11-04
- **Objetivo:** Evitar alucinações e explicitar conflitos normativos identificados no manual interno v2.1.

### Diálogo 5.1 — Garantia legal vs política interna de troca
```text
Você: Qual a garantia em caso de defeito?
Empório: A loja prevê troca por defeito em até 30 dias, mas a garantia legal é de 90 dias a partir do recebimento. Seu caso precisa de avaliação da equipe, sem limitar seus direitos de garantia.
[Fontes: Manual: p. 4 e 7]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Não nega o prazo legal de 90 dias do CDC.

### Diálogo 5.2 — Regras de parcelamento
```text
Você: Qual o parcelamento?
Empório: Parcelamos em até 12 vezes sem juros. O manual apresenta valores mínimos divergentes; nossa equipe precisa confirmar a condição aplicável.
[Fontes: Manual: p. 3]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Alerta para a discrepância entre a tabela de crédito e as regras textuais.

---

## Sessão 6: Tratamento de Reclamações
- **Data:** 2026-11-04
- **Objetivo:** Priorizar atendimento humano com empatia sem simular abertura de chamado inexistente.

### Diálogo 6.1 — Reclamação direta
```text
Você: Quero reclamar de uma entrega atrasada
Empório: Sinto muito pelo ocorrido. Posso orientar você a falar com nossa equipe responsável. O prazo previsto para retorno é de até 24 horas úteis; este protótipo não abre chamados automaticamente.
[Fontes: Manual: p. 7]
[Aviso: Necessário atendimento humano — nenhum chamado foi aberto automaticamente.]
```
- **Resultado:** Aprovado. Encaminhamento claro com menção do prazo de retorno (24h úteis) e disclaimer de protótipo.

---

## Template para Novos Registros

Para registrar novas interações de teste, copie e preencha a estrutura abaixo:

```markdown
### Diálogo X.Y — [Breve descrição do caso testado]
- **Data/Hora:** AAAA-MM-DD HH:MM
- **Cenário / Intenção:** [ex.: Consulta de frete / Desconto / Pedido]
- **Entrada do Usuário:**
  `[Mensagem enviada]`
- **Resposta do Assistente:**
  `[Texto retornado pelo Empório]`
- **Fontes Citadas:** `[ex.: Manual: p. X / CSV: ...]`
- **Handoff Disparado:** `Sim` ou `Não`
- **Resultado:** `Aprovado` / `Reprovado` — [Observações sobre comportamento, tom e dados]
```

