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
└── cloudflared
