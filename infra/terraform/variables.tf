# Variables principales del proyecto
variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "customer-satisfaction-analytics"
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "El nombre del proyecto debe contener solo letras minúsculas, números y guiones."
  }
}

variable "environment" {
  description = "Ambiente de deployment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "El ambiente debe ser dev, staging o prod."
  }
}

variable "aws_region" {
  description = "Región AWS donde se deployarán los recursos"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "ID de la cuenta AWS"
  type        = string
  default     = ""  # configurar via terraform.tfvars (NO commitear)
}

# Variables para S3
variable "data_bucket_name" {
  description = "Nombre base del bucket S3 para el Data Lake"
  type        = string
  default     = "customer-satisfaction-data-lake"
}

variable "enable_versioning" {
  description = "Habilitar versionado en el bucket S3"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Habilitar cifrado en el bucket S3"
  type        = bool
  default     = true
}

# Variables para AWS Glue
variable "glue_database_name" {
  description = "Nombre de la base de datos en AWS Glue Data Catalog"
  type        = string
  default     = "customer_satisfaction_db"
}

variable "crawler_schedule" {
  description = "Programación del crawler (formato cron)"
  type        = string
  default     = "cron(0 6 * * ? *)"  # Diariamente a las 6 AM UTC
}

variable "glue_job_timeout" {
  description = "Timeout en minutos para jobs de Glue"
  type        = number
  default     = 60
}

variable "glue_worker_type" {
  description = "Tipo de worker para jobs de Glue (G.1X, G.2X, G.025X)"
  type        = string
  default     = "G.1X"
  
  validation {
    condition     = contains(["G.025X", "G.1X", "G.2X"], var.glue_worker_type)
    error_message = "Worker type debe ser G.025X, G.1X o G.2X."
  }
}

variable "glue_number_of_workers" {
  description = "Número de workers para jobs de Glue"
  type        = number
  default     = 2
}

# Variables para Athena
variable "athena_bytes_scanned_cutoff" {
  description = "Límite de bytes escaneados por consulta en Athena (en bytes)"
  type        = number
  default     = 1073741824  # 1 GB
}

# Variables para lifecycle de S3
variable "raw_data_ia_transition_days" {
  description = "Días para transición de raw data a IA"
  type        = number
  default     = 30
}

variable "raw_data_glacier_transition_days" {
  description = "Días para transición de raw data a Glacier"
  type        = number
  default     = 90
}

variable "raw_data_deep_archive_transition_days" {
  description = "Días para transición de raw data a Deep Archive"
  type        = number
  default     = 365
}

variable "processed_data_ia_transition_days" {
  description = "Días para transición de processed data a IA"
  type        = number
  default     = 60
}

variable "processed_data_glacier_transition_days" {
  description = "Días para transición de processed data a Glacier"
  type        = number
  default     = 180
}

variable "logs_retention_days" {
  description = "Días de retención para logs"
  type        = number
  default     = 2555  # 7 años para cumplimiento
}

# Variables para etiquetado
variable "additional_tags" {
  description = "Tags adicionales para aplicar a todos los recursos"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Centro de costos para billing"
  type        = string
  default     = "analytics"
}

variable "owner" {
  description = "Propietario del proyecto"
  type        = string
  default     = "data-team"
}

# Variables para configuración de red (para futuras extensiones)
variable "vpc_cidr" {
  description = "CIDR block para VPC (si se requiere VPC personalizada)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_vpc_endpoints" {
  description = "Habilitar VPC endpoints para servicios AWS"
  type        = bool
  default     = false
}

# Variables para monitoring y alertas
variable "enable_cloudwatch_alarms" {
  description = "Habilitar alarmas de CloudWatch"
  type        = bool
  default     = true
}

variable "monitoring_enabled" {
  description = "Habilitar monitoreo avanzado"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email para notificaciones de alarmas"
  type        = string
  default     = ""
}

# Variables para buckets S3 específicos
variable "s3_athena_results_bucket" {
  description = "Nombre del bucket S3 para resultados de Athena"
  type        = string
  default     = "customer-satisfaction-athena-results"
}

variable "s3_logs_bucket" {
  description = "Nombre del bucket S3 para logs"
  type        = string
  default     = "customer-satisfaction-logs"
}

# Variables para presupuesto
variable "budget_amount" {
  description = "Cantidad del presupuesto en USD"
  type        = number
  default     = 1.00
}

variable "budget_time_unit" {
  description = "Unidad de tiempo para el presupuesto"
  type        = string
  default     = "MONTHLY"
}

# Variables para backup y disaster recovery
variable "enable_cross_region_replication" {
  description = "Habilitar replicación cross-region"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Días de retención para backups"
  type        = number
  default     = 30
}

# Variables para servicios externos (THIRD-PARTY INTEGRATIONS)
variable "external_dashboard_provider" {
  description = "Proveedor de dashboard externo (streamlit, grafana, superset)"
  type        = string
  default     = "streamlit"
  
  validation {
    condition     = contains(["streamlit", "grafana", "superset", "local"], var.external_dashboard_provider)
    error_message = "Dashboard provider debe ser streamlit, grafana, superset o local."
  }
}

variable "external_streamlit_config" {
  description = "Configuración para Streamlit externo"
  type = object({
    host_url    = string
    port        = number
    auth_token  = string
  })
  default = {
    host_url   = "localhost"
    port       = 8501
    auth_token = ""
  }
}

variable "external_grafana_config" {
  description = "Configuración para Grafana Cloud o self-hosted"
  type = object({
    url         = string
    api_key     = string
    org_id      = string
    datasource  = string
  })
  default = {
    url        = ""
    api_key    = ""
    org_id     = ""
    datasource = "athena"
  }
}

variable "external_data_processor" {
  description = "Procesador de datos externo (local, docker, kubernetes)"
  type        = string
  default     = "local"
  
  validation {
    condition     = contains(["local", "docker", "kubernetes", "github-actions"], var.external_data_processor)
    error_message = "Data processor debe ser local, docker, kubernetes o github-actions."
  }
}

variable "github_actions_config" {
  description = "Configuración para GitHub Actions como procesador"
  type = object({
    repository      = string
    workflow_file   = string
    trigger_webhook = string
  })
  default = {
    repository      = ""
    workflow_file   = "data-processing.yml"
    trigger_webhook = ""
  }
}

variable "external_ml_platform" {
  description = "Plataforma ML externa (local, colab, kaggle, huggingface)"
  type        = string
  default     = "local"
  
  validation {
    condition     = contains(["local", "colab", "kaggle", "huggingface", "paperspace"], var.external_ml_platform)
    error_message = "ML platform debe ser local, colab, kaggle, huggingface o paperspace."
  }
}

# Variables para integraciones de notificaciones externas
variable "slack_webhook_url" {
  description = "URL del webhook de Slack para notificaciones"
  type        = string
  default     = ""
  sensitive   = true
}

variable "discord_webhook_url" {
  description = "URL del webhook de Discord para notificaciones"
  type        = string
  default     = ""
  sensitive   = true
}

variable "telegram_config" {
  description = "Configuración para notificaciones de Telegram"
  type = object({
    bot_token = string
    chat_id   = string
  })
  default = {
    bot_token = ""
    chat_id   = ""
  }
  sensitive = true
}

# Variables para almacenamiento externo adicional
variable "external_backup_config" {
  description = "Configuración para backup externo"
  type = object({
    provider    = string  # "gdrive", "dropbox", "onedrive", "local"
    credentials = string
    folder_path = string
  })
  default = {
    provider    = "local"
    credentials = ""
    folder_path = "./backups"
  }
  sensitive = true
} 