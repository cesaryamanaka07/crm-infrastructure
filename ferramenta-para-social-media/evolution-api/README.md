# Evolution API

Stack isolada para WhatsApp da plataforma CRM.

## Arquitetura

```text
WhatsApp
  ↕
Evolution API
  ↕ webhook/API
n8n
  ↕ HTTP API
Typebot Viewer
```

A Evolution API mantém PostgreSQL e Redis próprios para não compartilhar dados ou cache com o Typebot.

## Configuração inicial

1. Copie `.env.example` para `.env`.
2. Gere valores fortes para `AUTHENTICATION_API_KEY` e `EVOLUTION_DB_PASSWORD`.
3. Confirme que `evo.cesaryamanaka.com.br` aponta para o proxy/túnel que encaminha para a porta local `8081`.
4. Confirme que a rede externa existe:

```bash
docker network create plataforma_network 2>/dev/null || true
```

5. Valide e suba a stack:

```bash
docker compose config --quiet
docker compose up -d
```

## Fluxo n8n/Typebot

A integração nativa Evolution–Typebot pode existir em versões compatíveis da Evolution API, mas o fluxo recomendado para esta plataforma é controlado pelo n8n:

1. A instância Evolution recebe uma mensagem e chama o webhook de entrada do n8n.
2. O n8n filtra eventos de mensagem recebida e identifica a instância/cliente.
3. O n8n mantém o identificador da conversa e chama o Typebot Viewer/API conforme o contrato adotado.
4. O n8n chama a Evolution API para enviar a resposta pelo endpoint da instância.
5. Eventos de envio/entrega podem ser processados em outro ramo do n8n.

A URL do webhook deve ser pública e autenticada. Não coloque a chave da Evolution em query string; use header `apikey` ou credencial segura do n8n.

## Verificações

```bash
docker compose ps
docker compose logs --tail=100 evolution-api
curl -fsS http://127.0.0.1:${EVOLUTION_HOST_PORT}/ >/dev/null
```

A chave real deve permanecer somente no `.env`, que não deve ser versionado.


## Acesso interno e externo

O `automation-service` acessa a Evolution pela rede Docker usando `http://evolution-api:8080`. O domínio `https://evo.cesaryamanaka.com.br` é reservado para acesso externo e deve apontar para a porta local `8081` do host. Webhooks continuam usando a URL pública configurada em `EVOLUTION_WEBHOOK_URL`.
