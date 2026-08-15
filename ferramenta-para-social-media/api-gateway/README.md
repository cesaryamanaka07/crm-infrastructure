# API Gateway

Ponto único de entrada da aplicação. O gateway mantém os microserviços privados
na rede Docker e encaminha as requisições conforme o caminho:

| Caminho público | Destino interno |
| --- | --- |
| `/api/auth/*` | `auth-service` |
| `/api/content/*` | `content-service` |

O frontend usa seu próprio domínio e chama este gateway por um único domínio de
API. Qualquer caminho fora de `/api/*` retorna `404`.

Os endereços internos, hosts e portas são configurados exclusivamente no `.env`.

## Inicialização

```bash
docker compose up -d --build
```

O Cloudflare Tunnel deve apontar o domínio principal para o `api-gateway`, usando
a porta interna definida no `.env`. A rota `/gateway-health` verifica o gateway.
