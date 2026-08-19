# n8n — domínio, proxy e integração com a plataforma

## Domínio oficial

O domínio público canônico do n8n é:

```text
https://workflow.cesaryamanaka.com.br
```

Na Cloudflare, configure o hostname para encaminhar ao n8n local:

```text
workflow.cesaryamanaka.com.br  ->  http://localhost:5678
```

Se o `cloudflared` estiver em um contêiner separado, `localhost` significa o próprio contêiner do túnel. Nesse caso, use um endereço alcançável pelo túnel, por exemplo:

```text
http://n8n:5678
```

ou coloque o `cloudflared` e o `n8n` na mesma rede Docker. Não use `localhost:5678` se o túnel estiver em outro contêiner.

## Rotas que devem ser preservadas

O proxy/túnel deve encaminhar o hostname inteiro, sem reescrever ou remover caminhos:

- `/` — painel web e login;
- `/workflow/*` — designer de workflows;
- `/webhook/*` — webhooks publicados, incluindo `/webhook/evolution-inbound`;
- `/api/v1/*` — API REST usada pelo `automation-service`;
- `/rest/*` — chamadas internas do editor;
- `/push/*` — atualizações em tempo real do editor.

Também devem ser preservados os headers `Host`, `X-Forwarded-Proto`, `X-Forwarded-For` e a conexão de upgrade para WebSocket. A rota `/api/v1/*` deve retornar JSON do n8n, não HTML de uma tela de login do Cloudflare Access.

## Configuração do n8n

O Compose do n8n deve manter:

```env
N8N_HOST=workflow.cesaryamanaka.com.br
N8N_PROTOCOL=https
N8N_EDITOR_BASE_URL=https://workflow.cesaryamanaka.com.br
WEBHOOK_URL=https://workflow.cesaryamanaka.com.br/
N8N_PROXY_HOPS=1
N8N_SECURE_COOKIE=true
```

Após o proprietário inicial ser criado, não é necessário habilitar cadastro público. O n8n deve ser administrado pelo usuário proprietário e pelos mecanismos de convite/permissão da própria instalação. Não apague o banco nem altere a chave de criptografia para bloquear novos usuários.

## Chaves

`N8N_ENCRYPTION_KEY` e `N8N_API_KEY` têm funções diferentes:

- `N8N_ENCRYPTION_KEY`: fica somente no servidor/contêiner n8n e deve permanecer estável; protege credenciais persistidas;
- `N8N_API_KEY`: é criada no painel do n8n e configurada somente no `automation-service` para listar, criar, vincular, ativar e pausar workflows.

Configuração do `automation-service`:

```env
N8N_API_URL=https://workflow.cesaryamanaka.com.br
N8N_API_KEY=<chave-gerada-no-painel-do-n8n>
```

Nunca coloque `N8N_API_KEY` no frontend, no bundle JavaScript ou em query string. Não use `N8N_ENCRYPTION_KEY` como API key.

## Uso dentro da plataforma

A aba `/n8n` da plataforma oferece:

- listagem de workflows por cliente;
- criação de um workflow inicial pela API, quando `N8N_API_KEY` está válida;
- vínculo/desvínculo por cliente;
- ativação e pausa;
- abertura do painel n8n;
- abertura direta do designer em `/workflow/{id}`;
- consulta de execuções recentes.

O designer é aberto em nova aba pelo botão **Designer** de cada workflow. O botão **Abrir painel n8n** abre a página inicial do n8n. A abertura em nova aba é intencional: preserva cookies de sessão, CSP, Cloudflare Access e WebSocket do editor. Embutir o designer em `iframe` pode ser bloqueado pelo próprio n8n ou pelo proxy e não é o caminho recomendado.

## Fluxo EvolutionAPI → n8n → Typebot

A EvolutionAPI deve enviar eventos para:

```text
https://workflow.cesaryamanaka.com.br/webhook/evolution-inbound
```

Esse webhook só fica ativo quando um workflow publicado no n8n possui esse caminho. O workflow deve filtrar eventos `MESSAGES_UPSERT`, identificar a instância/cliente, chamar o Typebot e enviar a resposta pela EvolutionAPI.

## Bloquear novos cadastros

Depois que o usuário proprietário for criado, não recrie o banco para bloquear cadastros. A administração de usuários deve ser feita pelas configurações de usuários/permissões da própria instalação do n8n. Mantenha `N8N_ENCRYPTION_KEY` estável.

## Testes externos

Depois de ajustar a Cloudflare, valide:

```bash
curl -I https://workflow.cesaryamanaka.com.br/
curl -i https://workflow.cesaryamanaka.com.br/api/v1/workflows
```

O segundo comando sem `X-N8N-API-KEY` pode retornar `401`, o que é esperado. O importante é não retornar `302` para uma página de login, `404` do proxy ou `502` do gateway.

A API autenticada deve ser testada usando a chave apenas no terminal seguro ou pelo `automation-service`; não registre a chave em logs.
