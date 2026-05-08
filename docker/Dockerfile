# Customer Satisfaction Analytics - External Services Container
# Costo: $0.00 (usando servicios gratuitos)

FROM python:3.9-slim

LABEL maintainer="Customer Satisfaction Analytics Team"
LABEL description="External services container for AWS-free analytics"
LABEL cost="$0.00"

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV AWS_DEFAULT_REGION=us-east-1

# Crear usuario no-root
RUN groupadd -r analytics && useradd -r -g analytics analytics

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Crear directorios de trabajo
WORKDIR /app
RUN mkdir -p /app/data /app/logs /app/config

# Copiar requirements
COPY requirements-external.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements-external.txt

# Copiar código de la aplicación
COPY analytics/streamlit_dashboard/ ./streamlit_dashboard/
COPY scripts/ ./scripts/
COPY ingestion/scripts/ ./ingestion/
COPY processing/ ./processing/

# Copiar archivos de configuración
COPY docker/config/ ./config/
COPY docker/entrypoint.sh .

# Hacer el script ejecutable
RUN chmod +x entrypoint.sh

# Cambiar propietario
RUN chown -R analytics:analytics /app

# Cambiar a usuario no-root
USER analytics

# Exponer puertos
EXPOSE 8501 8502 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando de entrada
ENTRYPOINT ["./entrypoint.sh"]
CMD ["streamlit"]
