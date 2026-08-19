"""Templates mínimos usados para criar workflows via API do n8n."""


def workflow_inicial(nome: str) -> dict:
    return {
        "name": nome,
        "active": False,
        "settings": {},
        "nodes": [
            {
                "parameters": {"httpMethod": "POST", "path": "evolution-inbound", "responseMode": "onReceived", "options": {}},
                "id": "evolution-webhook",
                "name": "EvolutionAPI Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [0, 0],
                "webhookId": "evolution-inbound",
            },
            {
                "parameters": {"respondWith": "json", "responseBody": "={{ { ok: true, received: true } }}", "options": {}},
                "id": "acknowledge-event",
                "name": "Acknowledgement",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [280, 0],
            },
        ],
        "connections": {
            "EvolutionAPI Webhook": {"main": [[{"node": "Acknowledgement", "type": "main", "index": 0}]]}
        },
        "tags": [],
    }
