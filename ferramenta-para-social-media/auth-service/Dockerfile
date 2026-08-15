# Imagem base: Python 3.12 na versão "slim" (enxuta, sem extras desnecessários)
FROM python:3.12-slim

# Diretório de trabalho dentro do container
WORKDIR /code

# Copia só o requirements.txt primeiro (não o projeto inteiro ainda).
# Isso é uma otimização de cache: o Docker só reinstala as dependências
# se o requirements.txt mudar, mesmo que seu código mude toda hora.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Agora sim copia o resto do código do serviço para dentro do container
COPY ./app ./app
COPY criar_usuario.py .

# Documenta (para humanos e ferramentas) que esse serviço escuta na porta 8000.
# Isso não abre a porta sozinho, é só informativo.
# Comando que roda quando o container inicia:
# sobe o servidor uvicorn, servindo o "app" definido em app/main.py,
# escutando em todas as interfaces de rede, na porta 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host \"$SERVICE_HOST\" --port \"$SERVICE_PORT\""]
