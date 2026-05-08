#!/usr/bin/env python3
"""
🎯 CONFIGURACIÓN RÁPIDA - SERVICIOS EXTERNOS
Customer Satisfaction Analytics
"""

import webbrowser
import subprocess
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = PROJECT_ROOT / "infra" / "terraform"

def mostrar_estado_actual():
    """Mostrar estado actual de la infraestructura"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║             ✅ INFRAESTRUCTURA AWS DESPLEGADA                    ║
║                Customer Satisfaction Analytics                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Obtener outputs de Terraform
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=str(TERRAFORM_DIR),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            outputs = json.loads(result.stdout)
            print("🏗️ RECURSOS AWS ACTIVOS:")
            for key, value in outputs.items():
                print(f"   📋 {key}: {value['value']}")
        else:
            print("⚠️ No se pudieron obtener los outputs de Terraform")
            
    except Exception as e:
        print(f"⚠️ Error verificando Terraform: {e}")

def configurar_streamlit_cloud():
    """Configurar Streamlit Cloud"""
    print("\n🚀 CONFIGURANDO STREAMLIT CLOUD")
    print("=" * 60)
    
    print("📋 PASOS A SEGUIR EN STREAMLIT.IO:")
    print("1. 🌐 Ve a: https://streamlit.io/cloud")
    print("2. 🔑 Haz clic en 'Sign up' (esquina superior derecha)")
    print("3. 🐙 Selecciona 'Continue with GitHub'")
    print("4. ✅ Autoriza Streamlit Cloud en GitHub")
    print("5. ➕ Haz clic en 'New app'")
    print("6. 📂 Completa los campos:")
    
    config = {
        "Repository": "<USER>/customer-satisfaction-analytics",
        "Branch": "Edgardo",
        "Main file path": "analytics/streamlit_dashboard/app.py",
        "App URL": "customer-satisfaction-analytics-dashboard",
        "Main file path": "analytics/streamlit_dashboard/app.py"
    }
    
    for key, value in config.items():
        print(f"   • {key}: {value}")
    
    print("\n🔐 Variables de entorno (Streamlit → Settings → Secrets):")
    secrets = [
        'AWS_ACCESS_KEY_ID = "tu_access_key"',
        'AWS_SECRET_ACCESS_KEY = "tu_secret_key"',
        'AWS_DEFAULT_REGION = "us-east-1"', 
        'S3_DATA_BUCKET = "customer-satisfaction-analytics-data-lake-dev-<RANDOM_SUFFIX>"',
        'S3_RESULTS_BUCKET = "customer-satisfaction-analytics-athena-results-dev-<RANDOM_SUFFIX>"',
        'ATHENA_WORKGROUP = "customer-satisfaction-analytics-workgroup-dev"'
    ]
    
    for secret in secrets:
        print(f"   🔑 {secret}")
    
    abrir = input("\n¿Abrir Streamlit Cloud en navegador? (y/n): ")
    if abrir.lower() == 'y':
        webbrowser.open("https://streamlit.io/cloud")
    
    return input("✅ ¿Streamlit Cloud configurado? (y/n): ").lower() == 'y'

def configurar_github_secrets():
    """Configurar GitHub Secrets"""
    print("\n🔐 CONFIGURANDO GITHUB SECRETS")
    print("=" * 60)
    
    print("📝 Pasos:")
    print("1. Ve a tu repositorio en GitHub")
    print("2. Settings → Secrets and variables → Actions") 
    print("3. Agregar estos secrets:")
    
    secrets = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", 
        "AWS_DEFAULT_REGION",
        "NOTIFICATION_EMAIL"
    ]
    
    for secret in secrets:
        print(f"   🔑 {secret}")
    
    print("\n💡 Valores recomendados:")
    print("   🌍 AWS_DEFAULT_REGION = us-east-1")
    print("   📧 NOTIFICATION_EMAIL = your-email@example.com")
    
    abrir = input("\n¿Abrir GitHub Secrets en navegador? (y/n): ")
    if abrir.lower() == 'y':
        webbrowser.open("https://github.com/<USER>/customer-satisfaction-analytics/settings/secrets/actions")
    
    return input("✅ ¿GitHub Secrets configurado? (y/n): ").lower() == 'y'

def configurar_google_colab():
    """Configurar Google Colab"""
    print("\n🧠 CONFIGURANDO GOOGLE COLAB")
    print("=" * 60)
    
    print("📋 Información:")
    print("   🔗 URL: https://colab.research.google.com")
    print("   📧 Usar cuenta Google existente")
    print("   💰 Plan: Gratuito (GPU limitada)")
    print("   🎯 Propósito: Notebooks ML y análisis")
    
    abrir = input("\n¿Abrir Google Colab en navegador? (y/n): ")
    if abrir.lower() == 'y':
        webbrowser.open("https://colab.research.google.com")
    
    return input("✅ ¿Google Colab configurado? (y/n): ").lower() == 'y'

def mostrar_proximos_pasos():
    """Mostrar próximos pasos después de configuración"""
    print("\n" + "=" * 70)
    print("🎯 PRÓXIMOS PASOS DE IMPLEMENTACIÓN")
    print("=" * 70)
    
    fases = [
        ("FASE 1", "Generar datos sintéticos", "1-2 días", [
            "python scripts/data_simulator.py",
            "python ingestion/scripts/s3_uploader.py"
        ]),
        ("FASE 2", "Pipeline ETL completo", "2-3 días", [
            "Configurar AWS Glue Crawlers",
            "Crear jobs de transformación",
            "Implementar arquitectura medallón"
        ]),
        ("FASE 3", "Analytics y ML", "2-3 días", [
            "Análisis de sentimientos (NLP)",
            "Modelo predicción satisfacción",
            "KPIs automáticos (CSAT, NPS)"
        ]),
        ("FASE 4", "Dashboards y visualización", "1-2 días", [
            "Dashboard Streamlit funcional", 
            "Reportes QuickSight",
            "APIs para consultas"
        ])
    ]
    
    for fase, nombre, tiempo, tareas in fases:
        print(f"\n📅 {fase}: {nombre} ({tiempo})")
        for tarea in tareas:
            print(f"   • {tarea}")
    
    print(f"\n🎊 PROYECTO COMPLETO: 6-10 días")
    print(f"💰 COSTO TOTAL: $0 (usando Free Tier)")

def mostrar_arquitectura_medallon():
    """Explicar la arquitectura medallón"""
    print(f"\n🏗️ ARQUITECTURA MEDALLÓN IMPLEMENTADA")
    print("=" * 60)
    
    capas = [
        ("🥉 BRONZE LAYER", "Datos crudos sin procesar", [
            "S3 bucket: customer-satisfaction-analytics-data-lake-dev-<RANDOM_SUFFIX>/bronze/",
            "Formatos: CSV, JSON, Parquet",
            "Fuentes: Tickets, encuestas, reviews, datasets externos"
        ]),
        ("🥈 SILVER LAYER", "Datos limpios y validados", [
            "S3 bucket: customer-satisfaction-analytics-data-lake-dev-<RANDOM_SUFFIX>/silver/",
            "Transformaciones: Limpieza, normalización, deduplicación",
            "Formato: Delta Lake / Apache Iceberg",
            "Particionado: Por fecha, canal, tipo"
        ]),
        ("🥇 GOLD LAYER", "Datos analíticos listos", [
            "S3 bucket: customer-satisfaction-analytics-data-lake-dev-<RANDOM_SUFFIX>/gold/",
            "Agregaciones: KPIs, métricas de negocio",
            "Modelos: Datasets para ML y BI", 
            "Views: Optimizadas para consultas"
        ])
    ]
    
    for capa, descripcion, detalles in capas:
        print(f"\n{capa}: {descripcion}")
        for detalle in detalles:
            print(f"   • {detalle}")

def main():
    """Función principal"""
    mostrar_estado_actual()
    
    print("\n🎯 Vamos a configurar los servicios externos paso a paso...")
    input("Presiona ENTER para continuar...")
    
    servicios_completados = []
    
    # Configurar servicios
    if configurar_streamlit_cloud():
        servicios_completados.append("Streamlit Cloud")
    
    if configurar_github_secrets():
        servicios_completados.append("GitHub Secrets")
    
    if configurar_google_colab():
        servicios_completados.append("Google Colab")
    
    # Mostrar resumen
    print(f"\n🎉 SERVICIOS CONFIGURADOS: {len(servicios_completados)}/3")
    for servicio in servicios_completados:
        print(f"   ✅ {servicio}")
    
    if len(servicios_completados) == 3:
        print("\n🎊 ¡CONFIGURACIÓN EXTERNA COMPLETADA!")
        mostrar_arquitectura_medallon()
        mostrar_proximos_pasos()
        
        print(f"\n🚀 ¡Ya puedes empezar con la implementación!")
        print(f"📖 Consulta: GUIA_CONFIGURACION_PASO_A_PASO.md")
    else:
        print(f"\n⏳ Completa los servicios restantes para continuar")
    
    print(f"\n💾 Recuerda: Puedes usar 'terraform destroy' cuando termines para evitar costos")

if __name__ == "__main__":
    main()
