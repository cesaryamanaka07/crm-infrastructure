# Social Service

Microserviço responsável pelo OAuth e pelas conexões com Meta e LinkedIn.

- App secrets e URLs existem somente no `.env`.
- Access e refresh tokens são criptografados antes de chegar ao PostgreSQL.
- O parâmetro OAuth `state` é aleatório, armazenado como hash e expira em 10 minutos.
- O callback público passa pelo API Gateway.

Antes de subir, crie os aplicativos nos portais Meta for Developers e LinkedIn
Developers, cadastre os callbacks HTTPS e preencha o `.env`.
