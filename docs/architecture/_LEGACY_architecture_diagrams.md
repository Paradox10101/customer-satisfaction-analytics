# 🏗️ **Diagramas de Arquitectura del Proyecto**

## 📊 **Opciones para Generar Diagramas**

### **🟢 Recomendadas (Gratis y Fáciles)**

1. **🎨 Draw.io (diagrams.net)**
   - **URL**: https://app.diagrams.net/
   - **Costo**: Gratis
   - **Ventajas**: Plantillas AWS, iconos oficiales, exporta PNG/SVG
   - **Uso**: Abrir navegador → Seleccionar plantilla AWS → Arrastrar componentes

2. **🔧 Lucidchart**
   - **URL**: https://lucidchart.com
   - **Costo**: Gratis (3 documentos)
   - **Ventajas**: Plantillas profesionales, colaboración en tiempo real
   - **Uso**: Crear cuenta → AWS Architecture → Drag & Drop

3. **📝 Mermaid (Código)**
   - **Integración**: GitHub, VS Code, documentación
   - **Costo**: Gratis
   - **Ventajas**: Versionado con Git, editable como código
   - **Uso**: Escribir código → Se renderiza automáticamente

---

## 🏗️ **Diagrama Mermaid (Código)**

### **Arquitectura Completa Actual**

```mermaid
graph TB
    subgraph "👤 USUARIO"
        U1[🧑‍💼 Data Analyst]
        U2[👨‍💻 Data Engineer]
        U3[🤖 ML Engineer]
    end

    subgraph "🌐 SERVICIOS EXTERNOS (GRATIS)"
        EXT1[📊 Streamlit Cloud<br/>Dashboard Principal<br/>$0.00]
        EXT2[🤖 GitHub Actions<br/>2000 min/mes<br/>CI/CD Pipeline]
        EXT3[🧠 Google Colab<br/>GPU/TPU Gratis<br/>ML Training]
        EXT4[📈 Grafana Cloud<br/>10K series<br/>Monitoring]
        EXT5[💬 Slack<br/>10K msgs/mes<br/>Alertas]
        EXT6[🐳 Docker Hub<br/>Public repos<br/>Containers]
    end
    
    subgraph "☁️ AWS FREE TIER"
        subgraph "🗂️ STORAGE"
            S3_RAW[📥 S3 Raw Data<br/>JSON, CSV<br/>~100MB]
            S3_PROC[⚙️ S3 Processed<br/>Parquet<br/>~200MB]
            S3_CUR[📊 S3 Curated<br/>Analytics Ready<br/>~200MB]
        end
        
        subgraph "🔧 PROCESSING"
            GLUE_CAT[📚 Glue Catalog<br/>Metadata<br/>Schema Registry]
            GLUE_ETL[🔧 Glue ETL Jobs<br/>10 hrs/mes<br/>Data Transform]
            ATHENA[🔍 Athena<br/>1GB queries/mes<br/>SQL Analytics]
        end
        
        subgraph "📊 MONITORING"
            CW_LOGS[📋 CloudWatch Logs<br/>1GB/mes<br/>Application Logs]
            CW_METRICS[📈 CloudWatch Metrics<br/>Free tier<br/>System Metrics]
            BUDGET[💰 AWS Budget<br/>$1 Alert<br/>Cost Protection]
        end
        
        subgraph "🛡️ SECURITY"
            IAM[🔐 IAM Roles<br/>Always Free<br/>Access Control]
            VPC[🌐 VPC Basic<br/>Free tier<br/>Network Security]
        end
    end
    
    subgraph "💻 LOCAL/DOCKER"
        DOCKER[🐳 Docker Compose<br/>Local Development<br/>Multi-container]
        LOCAL[💻 Local Scripts<br/>Data Generation<br/>Cost Monitoring]
    end

    %% Conexiones Usuario
    U1 --> EXT1
    U2 --> EXT2
    U3 --> EXT3
    
    %% Flujo de Datos Principal
    LOCAL --> S3_RAW
    S3_RAW --> GLUE_ETL
    GLUE_ETL --> S3_PROC
    S3_PROC --> GLUE_ETL
    GLUE_ETL --> S3_CUR
    
    %% Consultas y Analytics
    S3_CUR --> ATHENA
    GLUE_CAT --> ATHENA
    ATHENA --> EXT1
    
    %% ML Pipeline
    S3_CUR --> EXT3
    EXT3 --> S3_PROC
    
    %% Monitoreo
    GLUE_ETL --> CW_LOGS
    ATHENA --> CW_METRICS
    CW_METRICS --> BUDGET
    BUDGET --> EXT5
    
    %% CI/CD
    EXT2 --> GLUE_ETL
    EXT2 --> LOCAL
    EXT2 --> EXT1
    
    %% Visualización
    ATHENA --> EXT4
    CW_METRICS --> EXT4
    
    %% Docker
    DOCKER --> EXT1
    DOCKER --> LOCAL
    
    %% Estilos
    classDef awsFree fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef external fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef local fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef user fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class S3_RAW,S3_PROC,S3_CUR,GLUE_CAT,GLUE_ETL,ATHENA,CW_LOGS,CW_METRICS,BUDGET,IAM,VPC awsFree
    class EXT1,EXT2,EXT3,EXT4,EXT5,EXT6 external
    class DOCKER,LOCAL local
    class U1,U2,U3 user
```

### **Flujo de Datos Simplificado**

```mermaid
flowchart LR
    A[📥 Raw Data<br/>CSV/JSON] --> B[🔧 Glue ETL<br/>Transform]
    B --> C[📊 Processed Data<br/>Parquet]
    C --> D[🔍 Athena<br/>SQL Queries]
    D --> E[📈 Streamlit<br/>Dashboard]
    
    F[🤖 GitHub Actions] --> B
    G[🧠 Google Colab] --> C
    H[📊 CloudWatch] --> I[💬 Slack Alerts]
    
    style A fill:#ffebee
    style B fill:#e8f5e8
    style C fill:#e3f2fd
    style D fill:#f3e5f5
    style E fill:#fff3e0
```

### **Costos y Límites**

```mermaid
pie title Distribución de Recursos (Free Tier)
    "S3 Storage: 500MB / 5GB" : 10
    "Athena Queries: 1GB / 5GB" : 20
    "Glue Processing: 10h / 1000h" : 1
    "CloudWatch Logs: 1GB / 5GB" : 20
    "Reserva Seguridad" : 49
```

---

## 🎨 **Draw.io Template**

### **Pasos para crear en Draw.io:**

1. **Abrir**: https://app.diagrams.net/
2. **Seleccionar**: "Create New Diagram"
3. **Plantilla**: "AWS Architecture"
4. **Componentes AWS**:
   - S3 Bucket (3 instancias: Raw, Processed, Curated)
   - AWS Glue (ETL + Catalog)
   - Amazon Athena
   - CloudWatch
   - IAM Role
   - VPC
5. **Servicios Externos**:
   - Streamlit logo
   - GitHub Actions
   - Google Colab
   - Grafana
   - Slack
6. **Conectores**: Flechas indicando flujo de datos

### **Iconos y Colores Sugeridos**

| Categoría | Color | Servicios |
|-----------|-------|-----------|
| **AWS Free** | 🔵 Azul | S3, Athena, Glue, CloudWatch |
| **Externos** | 🟢 Verde | Streamlit, GitHub, Colab |
| **Local** | 🟠 Naranja | Docker, Scripts |
| **Usuarios** | 🟣 Morado | Data Team |

---

## 📱 **Otros Diagramas Útiles**

### **🔄 Diagrama de Deployment**

```mermaid
graph TD
    A[👨‍💻 Developer] --> B[📝 Git Push]
    B --> C[🤖 GitHub Actions]
    C --> D[🏗️ Terraform Apply]
    D --> E[☁️ AWS Resources]
    E --> F[📊 Dashboard Deploy]
    F --> G[✅ Production Ready]
    
    H[💰 Cost Monitor] --> I{💸 Cost > $1?}
    I -->|Yes| J[🚨 Alert & Destroy]
    I -->|No| K[✅ Continue]
```

### **🛡️ Diagrama de Seguridad**

```mermaid
graph TB
    subgraph "🔐 SECURITY LAYERS"
        A[🛡️ IAM Roles<br/>Least Privilege]
        B[🌐 VPC Security<br/>Network Isolation]
        C[🔒 S3 Encryption<br/>Data Protection]
        D[📊 CloudWatch<br/>Monitoring]
        E[💰 Budget Alerts<br/>Cost Protection]
    end
    
    F[👤 User Access] --> A
    A --> B
    B --> C
    C --> D
    D --> E
```

---

## 🛠️ **Herramientas Adicionales**

### **📐 Para Diagramas Técnicos**
- **Cloudcraft**: https://cloudcraft.co/ (AWS específico)
- **AWS Architecture Center**: https://aws.amazon.com/architecture/
- **Creately**: https://creately.com/ (Templates AWS)

### **🎯 Para Presentaciones**
- **Canva**: Plantillas de arquitectura
- **PowerPoint**: SmartArt + iconos AWS
- **Google Slides**: Diagramas colaborativos

---

## 📄 **Exportar Diagramas**

### **Formatos Recomendados**
- **PNG**: Para documentación y README
- **SVG**: Para escalabilidad
- **PDF**: Para presentaciones
- **Draw.io XML**: Para edición futura

### **Ubicación en el Proyecto**
```
docs/
├── architecture_diagrams.md
├── diagrams/
│   ├── architecture_overview.png
│   ├── data_flow.png
│   ├── cost_distribution.png
│   ├── deployment_flow.png
│   └── security_layers.png
└── draw_io_sources/
    ├── architecture.drawio
    └── data_flow.drawio
```

---

## 🎯 **Próximos Pasos**

1. **Crear diagrama principal** en Draw.io
2. **Exportar como PNG** 
3. **Actualizar README** con imagen
4. **Crear diagramas específicos** por proceso
5. **Mantener actualizado** con cambios del proyecto
