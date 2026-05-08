# Docker — preservado, no ejecutado

Esta carpeta contiene definiciones de containerización (`Dockerfile`, `docker-compose.yml`, `entrypoint.sh`) que **no se ejecutaron durante el proyecto académico**.

El Streamlit Dashboard se corrió **directamente con Python local** (`streamlit run streamlit_app.py`), sin Docker. Los servicios AWS desplegados con Terraform (S3, Glue, Athena, IAM) son serverless y tampoco usan estos containers.

Los archivos se preservan como referencia para una eventual reactivación del proyecto, pero no representan parte de lo entregado/sustentado. Por eso **Docker no aparece como tecnología en el stack** del [README principal](../README.md) ni en el [diagrama AS-IS](../docs/architecture/ARQUITECTURA_AS_IS.html).

## Si en el futuro se quiere usar

```bash
# Desde la raíz del repo
docker compose -f docker/docker-compose.yml up --build
# Streamlit estaría en http://localhost:8501
```

Variables de entorno requeridas (ver `docker-compose.yml`): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_DATA_BUCKET`, `S3_RESULTS_BUCKET`, `ATHENA_WORKGROUP`.
