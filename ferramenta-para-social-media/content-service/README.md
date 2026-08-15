# Content Service

Microserviço responsável pelos briefings e pelo ciclo editorial dos conteúdos.

## Responsabilidades

- criar e listar briefings;
- consultar, editar e excluir um briefing;
- garantir que cada usuário acesse apenas os próprios conteúdos;
- enviar o briefing ao OmniRoute e gerar conteúdos estruturados com IA;
- gerar imagens opcionais com paleta, tipografia, proporção e download;
- aplicar um framework principal e múltiplas técnicas de escrita ao briefing.
- solicitar lotes de Post, Carrossel, Reels e Story;
- definir narrativas independentes por formato e para as legendas;
- registrar a faixa de tamanho esperada para as legendas.

O serviço valida o JWT emitido pelo `auth-service`. Por enquanto, os dois serviços
usam a mesma `SECRET_KEY` e o algoritmo `HS256`.

## Endpoints

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Estado do serviço |
| `POST` | `/conteudos` | Cria um briefing |
| `GET` | `/conteudos` | Lista os briefings do usuário |
| `GET` | `/conteudos/{id}` | Consulta um briefing |
| `POST` | `/conteudos/{id}/gerar` | Gera os textos do briefing com o OmniRoute |
| `POST` | `/conteudos/{id}/gerar-imagens` | Gera imagens opcionais para o briefing |
| `PATCH` | `/conteudos/{id}` | Atualiza parcialmente um briefing |
| `DELETE` | `/conteudos/{id}` | Exclui um briefing |

As rotas de conteúdo exigem `Authorization: Bearer <token>`.

## Execução

1. Copie `.env.example` para `.env`.
2. Use no `content-service` a mesma `SECRET_KEY` do `auth-service`.
3. Garanta que PostgreSQL e a rede externa `plataforma_network` estejam ativos.
4. Configure `OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY` e
   `OMNIROUTE_TEXT_MODEL`. A chave deve ser criada no painel do OmniRoute.
5. Execute:

```bash
docker compose up -d --build
```

O endereço externo, o bind e as portas são definidos exclusivamente no `.env`.
A documentação OpenAPI fica disponível na rota `/docs` do serviço.

O Alembic executa automaticamente as migrations antes da API iniciar. A migration
preserva a tabela `content.conteudos` existente, adiciona o catálogo de técnicas,
a relação muitos-para-muitos e os campos de lote, narrativa e tamanho da legenda.

## Exemplo de criação

```json
{
  "intencao": "Ensinar organização de conteúdo",
  "tema": "Calendário editorial",
  "perspectiva": "Abordagem prática para autônomos",
  "modelo": "AIDA",
  "tom_de_voz": "Educativo",
  "quantidades": {
    "post_unico": 2,
    "carrossel": 1,
    "reels": 3,
    "story": 4
  },
  "narrativas": {
    "post_unico": "Direta",
    "carrossel": "Educacional",
    "reels": "Storytelling",
    "story": "Bastidores",
    "legenda": "Conversacional"
  },
  "tamanho_legenda": "longa",
  "tecnicas": ["copywriting", "prova_social", "curiosidade"],
  "observacoes": "Finalizar com uma chamada para salvar o post",
  "status": "pronto_para_gerar"
}
```
