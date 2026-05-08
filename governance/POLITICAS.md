# Políticas de Seguridad, Gobernanza y Anonimización de Datos

## Información del Proyecto

| Campo | Valor |
|-------|-------|
| **Proyecto** | Customer Satisfaction Analytics |
| **Arquitectura** | Arquitectura Híbrida (AWS + Servicios Externos) |
| **Equipo** | Equipo 1 |
| **Versión** | 1.0 |
| **Fecha** | 11/08/2025 |

---

## 1. Seguridad (IAM y Control de Acceso)

La seguridad de los datos es un pilar fundamental para mitigar riesgos, proteger los activos de información y garantizar el cumplimiento normativo. La implementación de controles robustos es crucial para salvaguardar la confidencialidad, integridad y disponibilidad de la información del proyecto.

Estas políticas se fundamentan en un **enfoque de defensa en profundidad**, aplicando múltiples capas de protección a lo largo de la arquitectura del sistema.

### 1.1 Gestión de Identidad y Acceso (IAM)

Una gestión de acceso efectiva constituye la primera línea de defensa. Las políticas de IAM se diseñarán para asegurar que solo las entidades autorizadas, como usuarios, roles y servicios, puedan acceder a los recursos, y únicamente con los permisos estrictamente necesarios para sus funciones.

#### Principio del Mínimo Privilegio
- Se aplicará de manera rigurosa
- Se prohíbe la asignación de permisos globales como `AdministratorAccess` a usuarios o servicios que no lo requieran
- Cada entidad tendrá únicamente los permisos indispensables para cumplir con sus tareas

#### Estructura de Roles y Políticas IAM
Se crearán roles específicos para cada tarea o microservicio, lo cual facilita la auditoría y el mantenimiento del sistema:

- **DataIngestionRole**: Permisos limitados a `s3:PutObject` en el bucket de la capa raw
- **GlueProcessingRole**: Acceso de lectura y escritura (`s3:GetObject` y `s3:PutObject`) únicamente en las capas processed y curated
- **AthenaQueryRole**: Permisos para ejecutar consultas y leer resultados de un bucket específico de Athena
- **MonitoringRole**: Permisos para acceder a métricas de CloudWatch (`cloudwatch:GetMetricData`) y a logs de CloudTrail (`logs:GetLogEvents`)

#### Autenticación y Gestión de Credenciales
- **Autenticación Multifactor (MFA)**: Obligatorio para todos los usuarios humanos con acceso a la consola de AWS
- **AWS Identity Center (AWS SSO)**: Para centralizar la gestión de identidades, proporcionando autenticación única y consistente
- **Gestión Segura de Claves**: Prohibido el almacenamiento de claves o secretos en el código fuente. Se utilizarán AWS Secrets Manager o GitHub Secrets

---

## 2. Gobernanza de Datos

La gobernanza de datos establece el marco para la gestión integral de la información, garantizando su calidad, accesibilidad y manejo responsable a lo largo de todo su ciclo de vida.

### 2.1 Clasificación y Etiquetado de Datos

Para la correcta aplicación de las políticas de seguridad, los datos se clasificarán según su nivel de sensibilidad:

- **Nivel 1 – Público**: Información no sensible y sin restricciones de acceso
- **Nivel 2 – Interno**: Datos procesados que no contienen Información de Identificación Personal (PII)
- **Nivel 3 – Confidencial**: Datos con PII o información sensible. Sujetos a políticas de anonimización y acceso restringido

### 2.2 Gestión del Ciclo de Vida de Datos

Se implementarán políticas de ciclo de vida para optimizar los costos de almacenamiento y asegurar que la retención de datos cumpla con los requisitos del negocio y normativos:

- **Capa raw**: Retención de 90 días, después archivado a S3 Glacier Instant Retrieval
- **Capa processed**: Retención de 180 días
- **Capa curated**: Retención indefinida o según políticas de negocio definidas

### 2.3 Auditoría y Trazabilidad

La capacidad de auditar y rastrear todas las acciones sobre los datos es fundamental para la seguridad y el cumplimiento:

- **AWS CloudTrail**: Habilitado para registrar todos los eventos y llamadas a la API de AWS. Logs conservados por 365 días en bucket S3 con políticas de inmutabilidad
- **AWS CloudWatch**: Para monitoreo de rendimiento, errores y costos, y configuración de alarmas sobre eventos críticos

---

## 3. Anonimización y Protección de PII

La protección de la Información de Identificación Personal (PII) es un requisito fundamental para cumplir con regulaciones como el GDPR y la ISO/IEC 27001. La anonimización de datos es un proceso técnico clave para reducir el riesgo de exposición de información sensible.

### 3.1 Alcance y Técnicas de Anonimización

#### Alcance
La anonimización se aplicará a todos los datos clasificados como Confidencial o de Nivel 3 que contengan PII. Este proceso se ejecutará antes de que los datos sean transferidos de la capa raw a la capa processed.

#### Técnicas de Anonimización
Se implementará una combinación de las siguientes técnicas, según el tipo de dato:

- **Seudonimización**: Reemplazo de identificadores directos por identificadores artificiales
- **Enmascaramiento**: Ocultación parcial de los datos
- **Hashing con Sal**: Aplicación de algoritmo criptográfico SHA-256 con valor aleatorio (salt) para garantizar irreversibilidad
- **Agregación**: Presentación de datos en formato resumido para evitar identificación individual

### 3.2 Cumplimiento Normativo y Estándares

La implementación de estas políticas se alinea con los siguientes marcos de seguridad y protección de datos:

- **GDPR**: Cumplimiento de principios de protección de datos por diseño y por defecto (Artículo 25) y medidas de seguridad del tratamiento (Artículo 32)
- **ISO/IEC 27001**: Adopción de controles relevantes del Anexo A, como gestión de acceso (A.9), criptografía (A.10) y cumplimiento legal (A.18)

---

## Referencias

- AWS Identity and Access Management (IAM). https://aws.amazon.com/iam/
- AWS CloudTrail. https://aws.amazon.com/cloudtrail/
- ISO/IEC 27001:2013 - Information technology — Security techniques — Information security management systems — Requirements. (2013). International Organization for Standardization.
- GDPR (General Data Protection Regulation) - EUR-Lex. (2016). https://eur-lex.europa.eu/eli/reg/2016/679/oj
- Reid, J., et al. (2018). Data Anonymization Techniques: A Tutorial. ACM Computing Surveys.