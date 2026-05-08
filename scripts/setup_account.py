#!/usr/bin/env python3
"""
Configuracion inicial de cuenta AWS para Customer Satisfaction Analytics.

Verifica credenciales, permisos IAM, presencia de Terraform y configura
entorno local (.env, github_secrets_template.json) para deployment.

Uso:
    # Configurar variables de entorno antes de ejecutar:
    export AWS_ACCOUNT_ID=123456789012
    export AWS_REGION=us-east-1
    export NOTIFICATION_EMAIL=tu-correo@ejemplo.com
    python scripts/setup_account.py
"""

import boto3
import os
import json
import subprocess
import sys
from pathlib import Path

# Configuracion via variables de entorno (NO hardcodear cuentas reales)
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "").strip()
AWS_REGION = os.getenv("AWS_REGION", "us-east-1").strip()
IAM_USER = os.getenv("IAM_USER", "").strip()
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "your-email@example.com").strip()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check_aws_config():
    """Verificar credenciales AWS activas."""
    print("Verificando configuracion AWS...")
    if not AWS_ACCOUNT_ID:
        print("ERROR: AWS_ACCOUNT_ID no esta seteado. Exporta la variable de entorno.")
        return False
    try:
        identity = boto3.client('sts').get_caller_identity()
        print(f"  Cuenta AWS detectada: {identity['Account']}")
        print(f"  Identidad ARN: {identity['Arn']}")
        if identity['Account'] != AWS_ACCOUNT_ID:
            print(f"  ERROR: cuenta detectada distinta a la esperada ({AWS_ACCOUNT_ID})")
            return False
        return True
    except Exception as e:
        print(f"  ERROR verificando AWS config: {e}")
        return False


def check_terraform_setup():
    """Verificar Terraform CLI y archivo .tfvars."""
    print("\nVerificando Terraform...")
    try:
        result = subprocess.run(
            ['terraform', '--version'], capture_output=True, text=True
        )
        if result.returncode != 0:
            print("  ERROR: Terraform CLI no esta instalado")
            return False
        print(f"  {result.stdout.splitlines()[0]}")

        tfvars_path = PROJECT_ROOT / "infra" / "terraform" / "terraform.tfvars"
        if not tfvars_path.exists():
            print(f"  ERROR: archivo {tfvars_path} no existe")
            print("  Copialo desde terraform.tfvars.example y editalo")
            return False
        print(f"  terraform.tfvars encontrado: {tfvars_path}")
        return True
    except FileNotFoundError:
        print("  ERROR: 'terraform' no esta en PATH")
        return False


def validate_s3_bucket_names():
    """Verificar disponibilidad de los nombres de bucket S3."""
    print("\nValidando nombres de buckets S3...")
    buckets = [
        f"customer-satisfaction-data-lake-{AWS_ACCOUNT_ID}-dev",
        f"customer-satisfaction-athena-results-{AWS_ACCOUNT_ID}-dev",
        f"customer-satisfaction-logs-{AWS_ACCOUNT_ID}-dev",
    ]
    s3 = boto3.client('s3')
    for bucket_name in buckets:
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"  Existe: {bucket_name}")
        except s3.exceptions.NoSuchBucket:
            print(f"  Disponible para crear: {bucket_name}")
        except Exception as e:
            print(f"  ADVERTENCIA en {bucket_name}: {e}")


def check_iam_permissions():
    """Verificar permisos IAM por servicio."""
    print("\nVerificando permisos IAM por servicio...")
    services = ['s3', 'glue', 'athena', 'cloudwatch', 'budgets']
    for service in services:
        try:
            client = boto3.client(service)
            if service == 's3':
                client.list_buckets()
            elif service == 'glue':
                client.get_databases()
            elif service == 'athena':
                client.list_work_groups()
            elif service == 'cloudwatch':
                client.list_metrics(MaxRecords=1)
            elif service == 'budgets':
                client.describe_budgets(AccountId=AWS_ACCOUNT_ID, MaxResults=1)
            print(f"  {service.upper()}: OK")
        except Exception as e:
            print(f"  {service.upper()}: {str(e)[:100]}")


def create_github_secrets_template():
    """Generar template github_secrets_template.json con placeholders."""
    print("\nGenerando github_secrets_template.json...")
    secrets_template = {
        "AWS_ACCESS_KEY_ID": "PLACEHOLDER_NO_COMMITEAR",
        "AWS_SECRET_ACCESS_KEY": "PLACEHOLDER_NO_COMMITEAR",
        "AWS_REGION": AWS_REGION,
        "AWS_ACCOUNT_ID": AWS_ACCOUNT_ID,
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "NOTIFICATION_EMAIL": NOTIFICATION_EMAIL,
    }
    out = PROJECT_ROOT / "github_secrets_template.json"
    out.write_text(json.dumps(secrets_template, indent=2), encoding='utf-8')
    print(f"  Generado: {out}")
    print("  IMPORTANTE: completa los valores reales en GitHub Settings > Secrets, NO en este archivo")


def setup_local_environment():
    """Crear archivo .env local con configuracion del proyecto."""
    print("\nConfigurando entorno local...")
    try:
        req_file = PROJECT_ROOT / "requirements.txt"
        if req_file.exists():
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(req_file)],
                check=True,
            )
            print("  Dependencias instaladas")

        env_content = f"""# Configuracion local generada por scripts/setup_account.py
AWS_ACCOUNT_ID={AWS_ACCOUNT_ID}
AWS_REGION={AWS_REGION}
PROJECT_PREFIX=cs-analytics-{AWS_ACCOUNT_ID}
S3_DATA_LAKE_BUCKET=customer-satisfaction-data-lake-{AWS_ACCOUNT_ID}-dev
S3_ATHENA_RESULTS_BUCKET=customer-satisfaction-athena-results-{AWS_ACCOUNT_ID}-dev
S3_LOGS_BUCKET=customer-satisfaction-logs-{AWS_ACCOUNT_ID}-dev
GLUE_DATABASE=customer_satisfaction_db_{AWS_ACCOUNT_ID}
ATHENA_WORKGROUP=customer-satisfaction-wg-{AWS_ACCOUNT_ID}
"""
        env_path = PROJECT_ROOT / ".env"
        env_path.write_text(env_content, encoding='utf-8')
        print(f"  .env creado: {env_path} (excluido por .gitignore)")
    except subprocess.CalledProcessError as e:
        print(f"  ERROR instalando dependencias: {e}")
    except Exception as e:
        print(f"  ERROR configurando entorno: {e}")


def run_cost_check():
    """Ejecutar aws_cost_monitor.py si existe."""
    print("\nVerificacion de costos...")
    cost_script = PROJECT_ROOT / "scripts" / "aws_cost_monitor.py"
    if not cost_script.exists():
        print("  aws_cost_monitor.py no encontrado, omitiendo")
        return
    try:
        result = subprocess.run(
            [sys.executable, str(cost_script)], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  OK")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"  ADVERTENCIA: {result.stderr[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")


def print_next_steps():
    print("\n" + "=" * 60)
    print("CONFIGURACION COMPLETADA")
    print("=" * 60)
    print("""
Proximos pasos:

1) EDITAR infra/terraform/terraform.tfvars
   - notification_email
   - cualquier override del .example

2) DEPLOY:
   cd infra/terraform/
   terraform init
   terraform plan
   terraform apply

3) CONFIGURAR GITHUB SECRETS:
   - Usar github_secrets_template.json como referencia
   - GitHub > Settings > Secrets and variables > Actions
   - NO commitear valores reales

4) GENERAR DATOS DE PRUEBA:
   python scripts/data_simulator.py
   python ingestion/scripts/s3_uploader.py

5) DASHBOARD LOCAL:
   streamlit run streamlit_app.py

6) MONITOREO DE COSTOS:
   python scripts/aws_cost_monitor.py
""")


def main():
    print("Setup de cuenta AWS - Customer Satisfaction Analytics")
    print(f"  AWS Account ID: {AWS_ACCOUNT_ID or '(no seteado)'}")
    print(f"  IAM user (opcional): {IAM_USER or '(no seteado)'}")
    print(f"  Region: {AWS_REGION}")
    print("=" * 60)

    if not check_aws_config():
        print("\nFix: configura AWS CLI con 'aws configure' y exporta AWS_ACCOUNT_ID")
        return False
    if not check_terraform_setup():
        print("\nFix: instala Terraform CLI y crea terraform.tfvars")
        return False

    validate_s3_bucket_names()
    check_iam_permissions()
    create_github_secrets_template()
    setup_local_environment()
    run_cost_check()
    print_next_steps()
    return True


if __name__ == "__main__":
    try:
        ok = main()
        sys.exit(0 if ok else 1)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)
