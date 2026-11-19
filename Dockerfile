FROM python:3.12-slim

WORKDIR /app

# Copiar los archivos de la aplicación web y el servidor de persistencia
COPY server.py index.html dashboard.html README.md ./

# Directorio de volumen persistente para los archivos Excel (Balance P&G y Tickets TKT)
RUN mkdir -p /app/data
VOLUME ["/app/data"]

ENV PORT=8089
EXPOSE 8089

CMD ["python", "server.py"]
