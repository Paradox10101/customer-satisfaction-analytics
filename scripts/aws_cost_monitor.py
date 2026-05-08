#!/usr/bin/env python3
"""
Monitor de Costos AWS - Customer Satisfaction Analytics
Account: <AWS_ACCOUNT_ID> (<IAM_USER>)
Script para mantener el proyecto dentro de la capa gratuita de AWS.

Funciones:
- 📊 Monitorea uso de S3, Athena, Glue, CloudWatch
- ⚠️ Alertas automáticas antes de superar límites
- 🧹 Limpieza automática de datos antiguos
- 📧 Notificaciones por email/Slack
- 💰 Estimación de costos en tiempo real
"""

import boto3
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import argparse
import os
import requests
import pandas as pd

# Configuración específica para cuenta <AWS_ACCOUNT_ID>
AWS_ACCOUNT_ID = "<AWS_ACCOUNT_ID>"
AWS_REGION = "us-east-1"
PROJECT_PREFIX = "cs-analytics-<AWS_ACCOUNT_ID>"

# Configuración de buckets específicos
S3_BUCKETS = {
    "data_lake": f"customer-satisfaction-data-lake-{AWS_ACCOUNT_ID}-dev",
    "athena_results": f"customer-satisfaction-athena-results-{AWS_ACCOUNT_ID}-dev",
    "logs": f"customer-satisfaction-logs-{AWS_ACCOUNT_ID}-dev"
}

# Configuración de recursos
GLUE_DATABASE = f"customer_satisfaction_db_{AWS_ACCOUNT_ID}"
ATHENA_WORKGROUP = f"customer-satisfaction-wg-{AWS_ACCOUNT_ID}"

class AWSCostMonitor:
    """Monitor de costos AWS para capa gratuita - Cuenta <AWS_ACCOUNT_ID>."""
    
    def __init__(self, region: str = 'us-east-1'):
        """
        Inicializar monitor de costos.
        
        Args:
            region: Región AWS a monitorear
        """
        self.region = region
        self.setup_logging()
        self.setup_aws_clients()
        
        # Límites de capa gratuita (12 meses)
        self.free_tier_limits = {
            's3_storage_gb': 5.0,
            's3_get_requests': 20000,
            's3_put_requests': 2000,
            'athena_data_scanned_gb': 5.0,
            'glue_dpu_hours': 1000000,  # 1M horas
            'cloudwatch_logs_gb': 5.0,
            'cloudwatch_metrics': 10
        }
        
        # Costos después de capa gratuita
        self.pricing = {
            's3_storage_per_gb': 0.023,  # USD por GB/mes
            's3_get_per_1000': 0.0004,  # USD por 1000 requests
            's3_put_per_1000': 0.005,   # USD por 1000 requests
            'athena_per_gb_scanned': 5.0,  # USD por GB escaneado
            'glue_per_dpu_hour': 0.44,   # USD por DPU-hora
            'cloudwatch_logs_per_gb': 0.50,  # USD por GB/mes
            'cloudwatch_metrics_per_metric': 0.30  # USD por métrica/mes
        }
    
    def setup_logging(self):
        """Configurar logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('aws_cost_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_aws_clients(self):
        """Configurar clientes AWS."""
        try:
            self.s3 = boto3.client('s3', region_name=self.region)
            self.athena = boto3.client('athena', region_name=self.region)
            self.glue = boto3.client('glue', region_name=self.region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            self.logs = boto3.client('logs', region_name=self.region)
            self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer siempre us-east-1
            
            self.logger.info("✅ Clientes AWS configurados correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando clientes AWS: {e}")
            raise
    
    def get_s3_usage(self, bucket_prefix: str = 'customer-satisfaction') -> Dict:
        """
        Obtener uso de S3.
        
        Args:
            bucket_prefix: Prefijo de buckets a monitorear
            
        Returns:
            Diccionario con métricas de uso de S3
        """
        try:
            # Listar buckets que coincidan con el prefijo
            buckets = self.s3.list_buckets()['Buckets']
            target_buckets = [b['Name'] for b in buckets if bucket_prefix in b['Name']]
            
            total_size_bytes = 0
            total_objects = 0
            get_requests = 0
            put_requests = 0
            
            for bucket_name in target_buckets:
                try:
                    # Obtener métricas de CloudWatch para el bucket
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=1)
                    
                    # Tamaño del bucket
                    size_metrics = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 24 horas
                        Statistics=['Average']
                    )
                    
                    if size_metrics['Datapoints']:
                        total_size_bytes += size_metrics['Datapoints'][-1]['Average']
                    
                    # Número de objetos
                    objects_metrics = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='NumberOfObjects',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=['Average']
                    )
                    
                    if objects_metrics['Datapoints']:
                        total_objects += objects_metrics['Datapoints'][-1]['Average']
                    
                    # Requests (últimos 30 días)
                    start_time_30d = end_time - timedelta(days=30)
                    
                    get_metrics = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='AllRequests',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket_name},
                            {'Name': 'FilterId', 'Value': 'EntireBucket'}
                        ],
                        StartTime=start_time_30d,
                        EndTime=end_time,
                        Period=2592000,  # 30 días
                        Statistics=['Sum']
                    )
                    
                    if get_metrics['Datapoints']:
                        get_requests += get_metrics['Datapoints'][-1]['Sum']
                
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudieron obtener métricas para bucket {bucket_name}: {e}")
                    continue
            
            usage = {
                'total_size_gb': total_size_bytes / (1024**3),
                'total_objects': int(total_objects),
                'get_requests_monthly': int(get_requests),
                'put_requests_monthly': int(put_requests),  # Estimado
                'buckets_monitored': len(target_buckets),
                'free_tier_usage_percent': (total_size_bytes / (1024**3)) / self.free_tier_limits['s3_storage_gb'] * 100
            }
            
            self.logger.info(f"📊 Uso S3: {usage['total_size_gb']:.2f}GB de {self.free_tier_limits['s3_storage_gb']}GB")
            return usage
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo uso de S3: {e}")
            return {'error': str(e)}
    
    def get_athena_usage(self, workgroup: str = 'customer-satisfaction-workgroup') -> Dict:
        """
        Obtener uso de Athena.
        
        Args:
            workgroup: Workgroup de Athena a monitorear
            
        Returns:
            Diccionario con métricas de uso de Athena
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)  # Últimos 30 días
            
            # Obtener métricas de datos escaneados
            data_scanned_metrics = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Athena',
                MetricName='DataScannedInBytes',
                Dimensions=[
                    {'Name': 'WorkGroup', 'Value': workgroup}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=2592000,  # 30 días
                Statistics=['Sum']
            )
            
            data_scanned_bytes = 0
            if data_scanned_metrics['Datapoints']:
                data_scanned_bytes = data_scanned_metrics['Datapoints'][-1]['Sum']
            
            # Obtener número de queries
            query_metrics = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Athena',
                MetricName='QueryExecutionTime',
                Dimensions=[
                    {'Name': 'WorkGroup', 'Value': workgroup}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=2592000,
                Statistics=['SampleCount']
            )
            
            total_queries = 0
            if query_metrics['Datapoints']:
                total_queries = query_metrics['Datapoints'][-1]['SampleCount']
            
            usage = {
                'data_scanned_gb': data_scanned_bytes / (1024**3),
                'total_queries_monthly': int(total_queries),
                'avg_data_per_query_mb': (data_scanned_bytes / (1024**2)) / max(total_queries, 1),
                'free_tier_usage_percent': (data_scanned_bytes / (1024**3)) / self.free_tier_limits['athena_data_scanned_gb'] * 100
            }
            
            self.logger.info(f"📊 Uso Athena: {usage['data_scanned_gb']:.2f}GB de {self.free_tier_limits['athena_data_scanned_gb']}GB")
            return usage
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo uso de Athena: {e}")
            return {'error': str(e)}
    
    def get_glue_usage(self) -> Dict:
        """Obtener uso de AWS Glue."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            # Obtener métricas de DPU hours
            dpu_metrics = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Glue',
                MetricName='glue.driver.aggregate.numCompletedTasks',
                StartTime=start_time,
                EndTime=end_time,
                Period=2592000,
                Statistics=['Sum']
            )
            
            # Obtener jobs de Glue para calcular uso
            jobs = self.glue.list_jobs()['JobNames']
            total_dpu_hours = 0
            
            for job_name in jobs:
                if 'customer-satisfaction' in job_name.lower():
                    try:
                        runs = self.glue.get_job_runs(JobName=job_name, MaxResults=50)
                        
                        for run in runs['JobRuns']:
                            if run['JobRunState'] == 'SUCCEEDED':
                                start_time_run = run.get('StartedOn')
                                end_time_run = run.get('CompletedOn')
                                
                                if start_time_run and end_time_run:
                                    duration_hours = (end_time_run - start_time_run).total_seconds() / 3600
                                    dpu_count = run.get('AllocatedCapacity', 2)  # Default 2 DPU
                                    total_dpu_hours += duration_hours * dpu_count
                    
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error obteniendo runs para job {job_name}: {e}")
                        continue
            
            usage = {
                'dpu_hours_monthly': total_dpu_hours,
                'jobs_monitored': len([j for j in jobs if 'customer-satisfaction' in j.lower()]),
                'free_tier_usage_percent': total_dpu_hours / self.free_tier_limits['glue_dpu_hours'] * 100
            }
            
            self.logger.info(f"📊 Uso Glue: {usage['dpu_hours_monthly']:.2f}h de {self.free_tier_limits['glue_dpu_hours']}h")
            return usage
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo uso de Glue: {e}")
            return {'error': str(e)}
    
    def get_cloudwatch_usage(self) -> Dict:
        """Obtener uso de CloudWatch."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            # Obtener tamaño de logs
            log_groups = self.logs.describe_log_groups()['logGroups']
            total_log_size_bytes = 0
            
            for log_group in log_groups:
                if 'customer-satisfaction' in log_group['logGroupName'].lower() or \
                   '/aws/glue' in log_group['logGroupName'] or \
                   '/aws/athena' in log_group['logGroupName']:
                    total_log_size_bytes += log_group.get('storedBytes', 0)
            
            # Obtener métricas personalizadas
            custom_metrics = self.cloudwatch.list_metrics(
                Namespace='CustomerSatisfaction'
            )['Metrics']
            
            usage = {
                'logs_size_gb': total_log_size_bytes / (1024**3),
                'custom_metrics_count': len(custom_metrics),
                'log_groups_monitored': len([lg for lg in log_groups if 
                                           'customer-satisfaction' in lg['logGroupName'].lower()]),
                'logs_free_tier_usage_percent': (total_log_size_bytes / (1024**3)) / self.free_tier_limits['cloudwatch_logs_gb'] * 100,
                'metrics_free_tier_usage_percent': len(custom_metrics) / self.free_tier_limits['cloudwatch_metrics'] * 100
            }
            
            self.logger.info(f"📊 Uso CloudWatch: {usage['logs_size_gb']:.2f}GB logs, {usage['custom_metrics_count']} métricas")
            return usage
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo uso de CloudWatch: {e}")
            return {'error': str(e)}
    
    def calculate_estimated_costs(self, usage_data: Dict) -> Dict:
        """
        Calcular costos estimados después de capa gratuita.
        
        Args:
            usage_data: Datos de uso de todos los servicios
            
        Returns:
            Diccionario con costos estimados
        """
        costs = {
            's3_cost': 0.0,
            'athena_cost': 0.0,
            'glue_cost': 0.0,
            'cloudwatch_cost': 0.0,
            'total_monthly_cost': 0.0
        }
        
        # Costos S3
        if 's3' in usage_data and 'error' not in usage_data['s3']:
            s3_data = usage_data['s3']
            excess_storage = max(0, s3_data['total_size_gb'] - self.free_tier_limits['s3_storage_gb'])
            excess_get_requests = max(0, s3_data['get_requests_monthly'] - self.free_tier_limits['s3_get_requests'])
            excess_put_requests = max(0, s3_data['put_requests_monthly'] - self.free_tier_limits['s3_put_requests'])
            
            costs['s3_cost'] = (
                excess_storage * self.pricing['s3_storage_per_gb'] +
                (excess_get_requests / 1000) * self.pricing['s3_get_per_1000'] +
                (excess_put_requests / 1000) * self.pricing['s3_put_per_1000']
            )
        
        # Costos Athena
        if 'athena' in usage_data and 'error' not in usage_data['athena']:
            athena_data = usage_data['athena']
            excess_data_scanned = max(0, athena_data['data_scanned_gb'] - self.free_tier_limits['athena_data_scanned_gb'])
            costs['athena_cost'] = excess_data_scanned * self.pricing['athena_per_gb_scanned']
        
        # Costos Glue
        if 'glue' in usage_data and 'error' not in usage_data['glue']:
            glue_data = usage_data['glue']
            excess_dpu_hours = max(0, glue_data['dpu_hours_monthly'] - self.free_tier_limits['glue_dpu_hours'])
            costs['glue_cost'] = excess_dpu_hours * self.pricing['glue_per_dpu_hour']
        
        # Costos CloudWatch
        if 'cloudwatch' in usage_data and 'error' not in usage_data['cloudwatch']:
            cw_data = usage_data['cloudwatch']
            excess_logs = max(0, cw_data['logs_size_gb'] - self.free_tier_limits['cloudwatch_logs_gb'])
            excess_metrics = max(0, cw_data['custom_metrics_count'] - self.free_tier_limits['cloudwatch_metrics'])
            
            costs['cloudwatch_cost'] = (
                excess_logs * self.pricing['cloudwatch_logs_per_gb'] +
                excess_metrics * self.pricing['cloudwatch_metrics_per_metric']
            )
        
        # Costo total
        costs['total_monthly_cost'] = sum([
            costs['s3_cost'],
            costs['athena_cost'],
            costs['glue_cost'],
            costs['cloudwatch_cost']
        ])
        
        return costs
    
    def check_alerts(self, usage_data: Dict) -> List[Dict]:
        """
        Verificar alertas basadas en umbrales.
        
        Args:
            usage_data: Datos de uso de servicios
            
        Returns:
            Lista de alertas generadas
        """
        alerts = []
        
        # Umbrales de alerta (% de uso de capa gratuita)
        warning_threshold = 80.0  # 80%
        critical_threshold = 95.0  # 95%
        
        # Alertas S3
        if 's3' in usage_data and 'error' not in usage_data['s3']:
            s3_usage_percent = usage_data['s3']['free_tier_usage_percent']
            
            if s3_usage_percent >= critical_threshold:
                alerts.append({
                    'service': 'S3',
                    'level': 'CRITICAL',
                    'message': f'Uso S3 crítico: {s3_usage_percent:.1f}% de la capa gratuita',
                    'action': 'Ejecutar limpieza inmediata de datos antiguos'
                })
            elif s3_usage_percent >= warning_threshold:
                alerts.append({
                    'service': 'S3',
                    'level': 'WARNING',
                    'message': f'Uso S3 alto: {s3_usage_percent:.1f}% de la capa gratuita',
                    'action': 'Considerar comprimir o archivar datos antiguos'
                })
        
        # Alertas Athena
        if 'athena' in usage_data and 'error' not in usage_data['athena']:
            athena_usage_percent = usage_data['athena']['free_tier_usage_percent']
            
            if athena_usage_percent >= critical_threshold:
                alerts.append({
                    'service': 'Athena',
                    'level': 'CRITICAL',
                    'message': f'Uso Athena crítico: {athena_usage_percent:.1f}% de la capa gratuita',
                    'action': 'Optimizar queries y usar más LIMIT clauses'
                })
            elif athena_usage_percent >= warning_threshold:
                alerts.append({
                    'service': 'Athena',
                    'level': 'WARNING',
                    'message': f'Uso Athena alto: {athena_usage_percent:.1f}% de la capa gratuita',
                    'action': 'Revisar y optimizar consultas frecuentes'
                })
        
        return alerts
    
    def cleanup_old_data(self, bucket_name: str, days_to_keep: int = 90) -> Dict:
        """
        Limpiar datos antiguos de S3.
        
        Args:
            bucket_name: Nombre del bucket
            days_to_keep: Días de datos a mantener
            
        Returns:
            Resultado de la limpieza
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_objects = []
            total_size_freed = 0
            
            # Listar objetos antiguos
            paginator = self.s3.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                            # Solo eliminar de raw-data/ para conservar processed/curated
                            if obj['Key'].startswith('raw-data/') and obj['Key'].endswith('.csv'):
                                try:
                                    self.s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                                    deleted_objects.append(obj['Key'])
                                    total_size_freed += obj['Size']
                                    
                                except Exception as e:
                                    self.logger.warning(f"⚠️ No se pudo eliminar {obj['Key']}: {e}")
            
            result = {
                'objects_deleted': len(deleted_objects),
                'size_freed_mb': total_size_freed / (1024**2),
                'cutoff_date': cutoff_date.isoformat(),
                'status': 'success'
            }
            
            self.logger.info(f"🧹 Limpieza completada: {result['objects_deleted']} objetos, {result['size_freed_mb']:.2f}MB liberados")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def send_alert_email(self, alerts: List[Dict], recipient: str, 
                        smtp_server: str = 'smtp.gmail.com', smtp_port: int = 587,
                        sender_email: str = None, sender_password: str = None):
        """Enviar alertas por email."""
        if not alerts or not all([recipient, sender_email, sender_password]):
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = "🚨 AWS Cost Monitor - Alertas Customer Satisfaction Analytics"
            
            # Crear contenido HTML
            html_content = """
            <html>
            <body>
                <h2>🚨 Alertas de Uso AWS</h2>
                <p>Se han detectado los siguientes alertas en tu proyecto Customer Satisfaction Analytics:</p>
                <ul>
            """
            
            for alert in alerts:
                color = '#dc3545' if alert['level'] == 'CRITICAL' else '#ffc107'
                html_content += f"""
                <li style="color: {color};">
                    <strong>{alert['service']} - {alert['level']}</strong><br>
                    {alert['message']}<br>
                    <em>Acción recomendada: {alert['action']}</em>
                </li><br>
                """
            
            html_content += """
                </ul>
                <p>Revisa el dashboard de monitoreo para más detalles.</p>
                <p><small>Generado automáticamente por AWS Cost Monitor</small></p>
            </body>
            </html>
            """
            
            msg.attach(MimeText(html_content, 'html'))
            
            # Enviar email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"📧 Alerta enviada por email a {recipient}")
            
        except Exception as e:
            self.logger.error(f"❌ Error enviando email: {e}")
    
    def send_slack_notification(self, alerts: List[Dict], webhook_url: str):
        """Enviar notificación a Slack."""
        if not alerts or not webhook_url:
            return
        
        try:
            # Crear mensaje Slack
            color = "danger" if any(a['level'] == 'CRITICAL' for a in alerts) else "warning"
            
            slack_message = {
                "attachments": [
                    {
                        "color": color,
                        "title": "🚨 AWS Cost Monitor - Customer Satisfaction Analytics",
                        "fields": []
                    }
                ]
            }
            
            for alert in alerts:
                slack_message["attachments"][0]["fields"].append({
                    "title": f"{alert['service']} - {alert['level']}",
                    "value": f"{alert['message']}\n*Acción:* {alert['action']}",
                    "short": False
                })
            
            # Enviar a Slack
            response = requests.post(webhook_url, json=slack_message)
            
            if response.status_code == 200:
                self.logger.info("📱 Notificación enviada a Slack")
            else:
                self.logger.error(f"❌ Error enviando a Slack: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"❌ Error enviando notificación Slack: {e}")
    
    def generate_report(self, usage_data: Dict, costs: Dict, alerts: List[Dict]) -> str:
        """Generar reporte completo de uso y costos."""
        report = f"""
# 📊 AWS Cost Monitor Report - Customer Satisfaction Analytics
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 💰 Resumen de Costos
- **Costo estimado mensual:** ${costs['total_monthly_cost']:.2f}
- **S3:** ${costs['s3_cost']:.2f}
- **Athena:** ${costs['athena_cost']:.2f}
- **Glue:** ${costs['glue_cost']:.2f}
- **CloudWatch:** ${costs['cloudwatch_cost']:.2f}

## 📊 Uso de Servicios

### S3 Storage
"""
        
        if 's3' in usage_data and 'error' not in usage_data['s3']:
            s3_data = usage_data['s3']
            report += f"""
- **Almacenamiento:** {s3_data['total_size_gb']:.2f}GB de {self.free_tier_limits['s3_storage_gb']}GB ({s3_data['free_tier_usage_percent']:.1f}%)
- **Objetos:** {s3_data['total_objects']:,}
- **Requests GET (mensual):** {s3_data['get_requests_monthly']:,}
- **Buckets monitoreados:** {s3_data['buckets_monitored']}
"""
        
        if 'athena' in usage_data and 'error' not in usage_data['athena']:
            athena_data = usage_data['athena']
            report += f"""
### Amazon Athena
- **Datos escaneados:** {athena_data['data_scanned_gb']:.2f}GB de {self.free_tier_limits['athena_data_scanned_gb']}GB ({athena_data['free_tier_usage_percent']:.1f}%)
- **Queries (mensual):** {athena_data['total_queries_monthly']:,}
- **Promedio por query:** {athena_data['avg_data_per_query_mb']:.2f}MB
"""
        
        if 'cloudwatch' in usage_data and 'error' not in usage_data['cloudwatch']:
            cw_data = usage_data['cloudwatch']
            report += f"""
### CloudWatch
- **Logs:** {cw_data['logs_size_gb']:.2f}GB de {self.free_tier_limits['cloudwatch_logs_gb']}GB ({cw_data['logs_free_tier_usage_percent']:.1f}%)
- **Métricas personalizadas:** {cw_data['custom_metrics_count']} de {self.free_tier_limits['cloudwatch_metrics']} ({cw_data['metrics_free_tier_usage_percent']:.1f}%)
"""
        
        # Alertas
        if alerts:
            report += "\n## 🚨 Alertas Activas\n"
            for alert in alerts:
                report += f"- **{alert['level']}** - {alert['service']}: {alert['message']}\n"
        else:
            report += "\n## ✅ Sin Alertas\nTodos los servicios están dentro de los límites seguros.\n"
        
        report += f"""
## 💡 Recomendaciones
1. **Optimizar queries Athena:** Usar LIMIT y WHERE clauses para reducir datos escaneados
2. **Comprimir datos S3:** Usar formato Parquet con compresión GZIP
3. **Limpieza automática:** Eliminar datos raw antiguos (>90 días)
4. **Monitoreo continuo:** Ejecutar este script diariamente

---
*Generado automáticamente por AWS Cost Monitor*
"""
        return report
    
    def run_full_monitor(self, bucket_prefix: str = 'customer-satisfaction',
                        athena_workgroup: str = 'customer-satisfaction-workgroup',
                        cleanup_old_data: bool = False,
                        notification_email: str = None,
                        slack_webhook: str = None) -> Dict:
        """
        Ejecutar monitoreo completo.
        
        Args:
            bucket_prefix: Prefijo de buckets S3 a monitorear
            athena_workgroup: Workgroup de Athena
            cleanup_old_data: Si ejecutar limpieza automática
            notification_email: Email para notificaciones
            slack_webhook: Webhook de Slack para notificaciones
            
        Returns:
            Resultado completo del monitoreo
        """
        self.logger.info("🚀 Iniciando monitoreo completo de costos AWS...")
        
        # Recopilar datos de uso
        usage_data = {
            's3': self.get_s3_usage(bucket_prefix),
            'athena': self.get_athena_usage(athena_workgroup),
            'glue': self.get_glue_usage(),
            'cloudwatch': self.get_cloudwatch_usage()
        }
        
        # Calcular costos
        costs = self.calculate_estimated_costs(usage_data)
        
        # Verificar alertas
        alerts = self.check_alerts(usage_data)
        
        # Limpieza automática si está habilitada
        cleanup_result = None
        if cleanup_old_data and 's3' in usage_data:
            s3_usage_percent = usage_data['s3'].get('free_tier_usage_percent', 0)
            if s3_usage_percent > 80:  # Solo limpiar si está cerca del límite
                buckets = self.s3.list_buckets()['Buckets']
                for bucket in buckets:
                    if bucket_prefix in bucket['Name']:
                        cleanup_result = self.cleanup_old_data(bucket['Name'])
                        break
        
        # Enviar notificaciones
        if alerts:
            if notification_email:
                self.send_alert_email(
                    alerts, 
                    notification_email,
                    sender_email=os.getenv('SMTP_EMAIL'),
                    sender_password=os.getenv('SMTP_PASSWORD')
                )
            
            if slack_webhook:
                self.send_slack_notification(alerts, slack_webhook)
        
        # Generar reporte
        report = self.generate_report(usage_data, costs, alerts)
        
        # Guardar reporte
        report_filename = f"aws_cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        result = {
            'usage_data': usage_data,
            'costs': costs,
            'alerts': alerts,
            'cleanup_result': cleanup_result,
            'report_file': report_filename,
            'status': 'success'
        }
        
        self.logger.info(f"✅ Monitoreo completado. Reporte guardado en: {report_filename}")
        return result


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description='Monitor de costos AWS para Customer Satisfaction Analytics')
    parser.add_argument('--region', default='us-east-1', help='Región AWS')
    parser.add_argument('--bucket-prefix', default='customer-satisfaction', help='Prefijo de buckets S3')
    parser.add_argument('--athena-workgroup', default='customer-satisfaction-workgroup', help='Workgroup de Athena')
    parser.add_argument('--cleanup', action='store_true', help='Ejecutar limpieza automática')
    parser.add_argument('--email', help='Email para notificaciones')
    parser.add_argument('--slack-webhook', help='Webhook de Slack')
    parser.add_argument('--quiet', action='store_true', help='Modo silencioso')
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Crear monitor
    monitor = AWSCostMonitor(region=args.region)
    
    # Ejecutar monitoreo
    result = monitor.run_full_monitor(
        bucket_prefix=args.bucket_prefix,
        athena_workgroup=args.athena_workgroup,
        cleanup_old_data=args.cleanup,
        notification_email=args.email,
        slack_webhook=args.slack_webhook
    )
    
    # Mostrar resumen
    if not args.quiet:
        print("\n" + "="*50)
        print("📊 RESUMEN DE MONITOREO")
        print("="*50)
        print(f"💰 Costo estimado mensual: ${result['costs']['total_monthly_cost']:.2f}")
        print(f"🚨 Alertas generadas: {len(result['alerts'])}")
        print(f"📄 Reporte guardado en: {result['report_file']}")
        
        if result['alerts']:
            print("\n🚨 ALERTAS:")
            for alert in result['alerts']:
                print(f"  • {alert['service']} - {alert['level']}: {alert['message']}")
        else:
            print("\n✅ Todo dentro de los límites de la capa gratuita")


if __name__ == "__main__":
    main() 