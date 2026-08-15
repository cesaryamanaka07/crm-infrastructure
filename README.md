# CRM Infrastructure

Reproducible Docker infrastructure designed to support CRM, automation and artificial intelligence applications.

## Services

- Docker
- Portainer
- PostgreSQL
- Redis
- MinIO
- Cloudflare Tunnel

## Architecture

The infrastructure uses separate Docker networks for application and management services.

```text
management
├── portainer
└── cloudflared

plataforma_network
├── postgres
├── redis
├── minio
├── api-gateway
├── frontend
├── auth-service
├── content-service
└── cloudflared
```

## Application services

- `auth-service`: login, users and JWT issuance;
- `content-service`: authenticated content briefings and editorial status;
- `api-gateway`: single public entry point and internal request routing;
- `Frontend`: React interface for login, dashboard and content creation.
