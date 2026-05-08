# Documentación del proyecto

Customer Satisfaction Analytics — diplomado **Advanced Data Engineer (DMC)**.

Este directorio agrupa la documentación técnica, decisiones de arquitectura, costos y deployment. Para arrancar el proyecto, leer primero el [README principal del repo](../README.md).

---

## Estructura

```text
docs/
├── README.md                       ← este archivo (índice)
├── architecture/                            ← diagramas y descripción de la arquitectura
│   ├── ARQUITECTURA_AS_IS.html               ← diagrama AS-IS (lo que se desplegó) — banner verde
│   ├── ARQUITECTURA_TO_BE.html               ← diagrama TO-BE (aspiracional, NO desplegada) — banner violeta
│   ├── DIAGRAMA_ARQUITECTURA_DETALLADO.md    ← descripción detallada del scope real
│   └── _LEGACY_*                             ← material original del TO-BE (drawio, svg, md de justificación)
├── costs/
│   └── COSTOS.md                   ← análisis de costos por servicio
├── deployment/
│   └── DESPLIEGUE.md               ← guía de despliegue paso a paso
├── infrastructure/
│   └── INFRAESTRUCTURA.md          ← detalles de Terraform y recursos AWS
├── aws_free_tier_analysis.md       ← análisis de límites Free Tier vs. uso real
├── external_services_guide.md      ← integración con Streamlit Cloud, GitHub, etc.
├── context.md                      ← contexto académico inicial del proyecto
└── project_summary.md              ← resumen ejecutivo
```

> Las políticas de seguridad y gobernanza viven en [`../governance/POLITICAS.md`](../governance/POLITICAS.md), que es donde corresponden semánticamente.

---

## Por dónde empezar

| Si vienes a… | Lee primero |
|---|---|
| **Entender el proyecto y arrancarlo** | [`../README.md`](../README.md) (raíz) |
| **Ver la arquitectura visual** | [`architecture/ARQUITECTURA_AS_IS.html`](architecture/ARQUITECTURA_AS_IS.html) |
| **Implementación técnica detallada** | [`architecture/DIAGRAMA_ARQUITECTURA_DETALLADO.md`](architecture/DIAGRAMA_ARQUITECTURA_DETALLADO.md) |
| **Desplegar en AWS** | [`deployment/DESPLIEGUE.md`](deployment/DESPLIEGUE.md) |
| **Validar que entras en Free Tier** | [`aws_free_tier_analysis.md`](aws_free_tier_analysis.md) |
| **Ver presupuesto/costos** | [`costs/COSTOS.md`](costs/COSTOS.md) |
| **Políticas de seguridad/gobernanza** | [`../governance/POLITICAS.md`](../governance/POLITICAS.md) |

---

## Dos arquitecturas: TO-BE (aspiracional) vs AS-IS (real)

El proyecto tiene **dos diagramas pareados** que cuentan la historia completa de las decisiones técnicas:

| Diagrama | Archivo | Banner | Qué representa |
|---|---|---|---|
| **AS-IS** | [`ARQUITECTURA_AS_IS.html`](architecture/ARQUITECTURA_AS_IS.html) | 🟢 verde · "DESPLEGADO" | Lo que efectivamente se construyó: Lakehouse Free Tier (S3 + Glue + Athena + Streamlit) desplegado vía Terraform. |
| **TO-BE** | [`ARQUITECTURA_TO_BE.html`](architecture/ARQUITECTURA_TO_BE.html) | 🟣 violeta · "NO DESPLEGADO" | Arquitectura empresarial aspiracional inicial (Kinesis, API Gateway, EMR, Redshift, Bedrock, SageMaker) que se diseñó al inicio pero **no se implementó**. |

Ambos HTMLs comparten el mismo lenguaje visual; el banner superior los distingue al instante. Mostrar ambos comunica intencionalidad: hubo **un diseño ambicioso inicial** y se aterrizó a una **versión ejecutable real bajo Free Tier** — exactamente la conversación que se tiene en proyectos reales cuando aparecen restricciones de presupuesto.

Los archivos `_LEGACY_*` (drawio editable, SVGs antiguos, `JUSTIFICACION_TECNICA.md` con la fundamentación servicio-por-servicio del TO-BE) se preservan como evidencia del proceso de diseño.

Para el detalle del estado de cada componente (qué se desplegó vs qué quedó como definición), ver la sección [**Estado de implementación**](../README.md#5-estado-de-implementación-as-is-vs-to-be) en el README principal.

---

## Convenciones

- Diagramas editables (`.drawio`) van junto a su versión renderizada (`.html`/`.svg`).
- Documentos en español, código y nombres de archivo en inglés.
- Decisiones técnicas con costo asociado se documentan en `costs/COSTOS.md`.
