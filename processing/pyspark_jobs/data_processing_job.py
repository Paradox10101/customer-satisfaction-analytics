"""
Job de AWS Glue para procesamiento de datos de satisfacción del cliente.

Este job realiza:
- Limpieza y validación de datos
- Transformaciones y enriquecimiento
- Cálculo de métricas de satisfacción
- Particionamiento optimizado para consultas
- Análisis de sentimientos básico
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
import boto3
from datetime import datetime, timedelta
import logging


class CustomerSatisfactionProcessor:
    """Procesador de datos de satisfacción del cliente."""
    
    def __init__(self, glue_context: GlueContext, job_name: str):
        """
        Inicializar el procesador.
        
        Args:
            glue_context: Contexto de AWS Glue
            job_name: Nombre del job
        """
        self.glue_context = glue_context
        self.spark = glue_context.spark_session
        self.job_name = job_name
        
        # Configurar logging
        self.logger = logging.getLogger(job_name)
        self.logger.setLevel(logging.INFO)
        
        # Configurar Spark para optimizaciones
        self.spark.conf.set("spark.sql.adaptive.enabled", "true")
        self.spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
        self.spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
        
    def read_raw_data(self, database_name: str, table_name: str) -> DataFrame:
        """
        Leer datos crudos desde AWS Glue Data Catalog.
        
        Args:
            database_name: Nombre de la base de datos
            table_name: Nombre de la tabla
            
        Returns:
            DataFrame con datos crudos
        """
        try:
            datasource = self.glue_context.create_dynamic_frame.from_catalog(
                database=database_name,
                table_name=table_name,
                transformation_ctx=f"datasource_{table_name}"
            )
            
            df = datasource.toDF()
            self.logger.info(f"Leídos {df.count()} registros de {table_name}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error leyendo {table_name}: {e}")
            raise
    
    def clean_customer_tickets(self, df: DataFrame) -> DataFrame:
        """
        Limpiar y validar datos de tickets de cliente.
        
        Args:
            df: DataFrame con tickets crudos
            
        Returns:
            DataFrame limpio
        """
        self.logger.info("Limpiando datos de customer tickets...")
        
        # Filtrar registros válidos
        df_clean = df.filter(
            (col("satisfaccion_score").between(1, 5)) &
            (col("duracion_minutos") > 0) &
            (col("ticket_id").isNotNull()) &
            (col("cliente_id").isNotNull())
        )
        
        # Estandarizar valores categóricos
        df_clean = df_clean.withColumn(
            "canal_normalizado",
            when(col("canal").isin(["telefono", "phone"]), "telefono")
            .when(col("canal").isin(["chat", "webchat"]), "chat")
            .when(col("canal").isin(["email", "correo"]), "email")
            .when(col("canal").isin(["presencial", "branch"]), "presencial")
            .when(col("canal").isin(["app_movil", "mobile", "app"]), "app_movil")
            .otherwise("otros")
        )
        
        # Crear categorías de satisfacción
        df_clean = df_clean.withColumn(
            "categoria_satisfaccion",
            when(col("satisfaccion_score") >= 4.5, "muy_satisfecho")
            .when(col("satisfaccion_score") >= 3.5, "satisfecho")
            .when(col("satisfaccion_score") >= 2.5, "neutral")
            .when(col("satisfaccion_score") >= 1.5, "insatisfecho")
            .otherwise("muy_insatisfecho")
        )
        
        # Crear categorías de duración
        df_clean = df_clean.withColumn(
            "categoria_duracion",
            when(col("duracion_minutos") <= 5, "rapido")
            .when(col("duracion_minutos") <= 15, "normal")
            .when(col("duracion_minutos") <= 30, "largo")
            .otherwise("muy_largo")
        )
        
        # Convertir fechas
        df_clean = df_clean.withColumn(
            "fecha_creacion",
            to_timestamp(col("fecha_creacion"))
        )
        
        # Agregar columnas de particionamiento
        df_clean = df_clean.withColumn("year", year(col("fecha_creacion"))) \
                           .withColumn("month", month(col("fecha_creacion"))) \
                           .withColumn("day", dayofmonth(col("fecha_creacion")))
        
        self.logger.info(f"Tickets limpiados: {df_clean.count()} registros válidos")
        return df_clean
    
    def clean_nps_surveys(self, df: DataFrame) -> DataFrame:
        """
        Limpiar y procesar encuestas NPS.
        
        Args:
            df: DataFrame con encuestas NPS crudas
            
        Returns:
            DataFrame limpio
        """
        self.logger.info("Procesando encuestas NPS...")
        
        # Filtrar registros válidos
        df_clean = df.filter(
            (col("nps_score").between(0, 10)) &
            (col("encuesta_id").isNotNull()) &
            (col("cliente_id").isNotNull())
        )
        
        # Validar y corregir categorías NPS
        df_clean = df_clean.withColumn(
            "categoria_nps_corregida",
            when(col("nps_score") >= 9, "promotor")
            .when(col("nps_score") >= 7, "neutro")
            .otherwise("detractor")
        )
        
        # Análisis básico de sentimientos en comentarios
        df_clean = df_clean.withColumn(
            "sentiment_score_simple",
            when(
                lower(col("comentario")).rlike(".*(excelente|genial|perfecto|magnifico|increible).*"), 
                1.0
            )
            .when(
                lower(col("comentario")).rlike(".*(bueno|bien|satisfecho|correcto).*"), 
                0.5
            )
            .when(
                lower(col("comentario")).rlike(".*(malo|pesimo|terrible|horrible|awful).*"), 
                -1.0
            )
            .when(
                lower(col("comentario")).rlike(".*(problema|error|fallo|demora|lento).*"), 
                -0.5
            )
            .otherwise(0.0)
        )
        
        # Convertir fechas
        df_clean = df_clean.withColumn(
            "fecha_encuesta",
            to_timestamp(col("fecha_encuesta"))
        )
        
        # Agregar particionamiento
        df_clean = df_clean.withColumn("year", year(col("fecha_encuesta"))) \
                           .withColumn("month", month(col("fecha_encuesta"))) \
                           .withColumn("day", dayofmonth(col("fecha_encuesta")))
        
        self.logger.info(f"Encuestas NPS procesadas: {df_clean.count()} registros")
        return df_clean
    
    def clean_customer_reviews(self, df: DataFrame) -> DataFrame:
        """
        Limpiar y procesar reviews de clientes.
        
        Args:
            df: DataFrame con reviews crudas
            
        Returns:
            DataFrame limpio
        """
        self.logger.info("Procesando customer reviews...")
        
        # Filtrar registros válidos
        df_clean = df.filter(
            (col("calificacion").between(1, 5)) &
            (col("review_id").isNotNull()) &
            (col("texto_review").isNotNull()) &
            (length(col("texto_review")) > 10)  # Reviews con contenido mínimo
        )
        
        # Análisis de sentimientos mejorado
        df_clean = df_clean.withColumn(
            "sentiment_score",
            when(col("calificacion") == 5, 1.0)
            .when(col("calificacion") == 4, 0.5)
            .when(col("calificacion") == 3, 0.0)
            .when(col("calificacion") == 2, -0.5)
            .otherwise(-1.0)
        )
        
        # Categorizar por calificación
        df_clean = df_clean.withColumn(
            "categoria_review",
            when(col("calificacion") >= 4, "positivo")
            .when(col("calificacion") == 3, "neutro")
            .otherwise("negativo")
        )
        
        # Calcular longitud del texto
        df_clean = df_clean.withColumn(
            "longitud_review",
            length(col("texto_review"))
        )
        
        # Convertir fechas
        df_clean = df_clean.withColumn(
            "fecha_review",
            to_timestamp(col("fecha_review"))
        )
        
        # Particionamiento
        df_clean = df_clean.withColumn("year", year(col("fecha_review"))) \
                           .withColumn("month", month(col("fecha_review"))) \
                           .withColumn("day", dayofmonth(col("fecha_review")))
        
        self.logger.info(f"Reviews procesadas: {df_clean.count()} registros")
        return df_clean
    
    def calculate_satisfaction_metrics(self, tickets_df: DataFrame, 
                                     nps_df: DataFrame) -> DataFrame:
        """
        Calcular métricas agregadas de satisfacción.
        
        Args:
            tickets_df: DataFrame de tickets limpio
            nps_df: DataFrame de NPS limpio
            
        Returns:
            DataFrame con métricas agregadas
        """
        self.logger.info("Calculando métricas de satisfacción...")
        
        # Métricas diarias por canal
        daily_metrics = tickets_df.groupBy(
            "year", "month", "day", "canal_normalizado"
        ).agg(
            count("*").alias("total_tickets"),
            avg("satisfaccion_score").alias("satisfaccion_promedio"),
            avg("duracion_minutos").alias("duracion_promedio"),
            sum(when(col("categoria_satisfaccion").isin(["muy_satisfecho", "satisfecho"]), 1)
                .otherwise(0)).alias("tickets_satisfactorios"),
            sum(when(col("resolucion") == "resuelto", 1)
                .otherwise(0)).alias("tickets_resueltos"),
            countDistinct("cliente_id").alias("clientes_unicos")
        )
        
        # Calcular tasas
        daily_metrics = daily_metrics.withColumn(
            "tasa_satisfaccion",
            col("tickets_satisfactorios") / col("total_tickets")
        ).withColumn(
            "tasa_resolucion",
            col("tickets_resueltos") / col("total_tickets")
        )
        
        # Métricas NPS diarias
        nps_daily = nps_df.groupBy("year", "month", "day").agg(
            count("*").alias("total_encuestas"),
            sum(when(col("categoria_nps_corregida") == "promotor", 1)
                .otherwise(0)).alias("promotores"),
            sum(when(col("categoria_nps_corregida") == "detractor", 1)
                .otherwise(0)).alias("detractores"),
            avg("nps_score").alias("nps_promedio")
        )
        
        # Calcular NPS Score
        nps_daily = nps_daily.withColumn(
            "nps_score_calculado",
            ((col("promotores") - col("detractores")) / col("total_encuestas")) * 100
        )
        
        # Combinar métricas
        combined_metrics = daily_metrics.join(
            nps_daily,
            ["year", "month", "day"],
            "full_outer"
        )
        
        # Agregar fecha para facilitar consultas
        combined_metrics = combined_metrics.withColumn(
            "fecha",
            to_date(concat_ws("-", col("year"), col("month"), col("day")))
        )
        
        self.logger.info("Métricas calculadas exitosamente")
        return combined_metrics
    
    def write_processed_data(self, df: DataFrame, output_path: str, 
                           partition_cols: list = None) -> None:
        """
        Escribir datos procesados a S3 en formato Parquet.
        
        Args:
            df: DataFrame a escribir
            output_path: Ruta de salida en S3
            partition_cols: Columnas para particionamiento
        """
        try:
            writer = df.write.mode("overwrite") \
                      .option("compression", "snappy") \
                      .format("parquet")
            
            if partition_cols:
                writer = writer.partitionBy(*partition_cols)
            
            writer.save(output_path)
            
            self.logger.info(f"Datos escritos exitosamente en: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error escribiendo datos en {output_path}: {e}")
            raise
    
    def update_data_catalog(self, database_name: str, table_name: str, 
                          s3_path: str, partition_cols: list = None) -> None:
        """
        Actualizar AWS Glue Data Catalog con nueva tabla.
        
        Args:
            database_name: Nombre de la base de datos
            table_name: Nombre de la tabla
            s3_path: Ruta S3 de los datos
            partition_cols: Columnas de partición
        """
        try:
            glue_client = boto3.client('glue')
            
            # Configuración básica de la tabla
            table_input = {
                'Name': table_name,
                'StorageDescriptor': {
                    'Columns': [],  # Se detectarán automáticamente
                    'Location': s3_path,
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                    }
                }
            }
            
            if partition_cols:
                table_input['PartitionKeys'] = [
                    {'Name': col, 'Type': 'string'} for col in partition_cols
                ]
            
            # Crear o actualizar tabla
            try:
                glue_client.update_table(
                    DatabaseName=database_name,
                    TableInput=table_input
                )
                self.logger.info(f"Tabla {table_name} actualizada en Data Catalog")
            except glue_client.exceptions.EntityNotFoundException:
                glue_client.create_table(
                    DatabaseName=database_name,
                    TableInput=table_input
                )
                self.logger.info(f"Tabla {table_name} creada en Data Catalog")
                
        except Exception as e:
            self.logger.error(f"Error actualizando Data Catalog para {table_name}: {e}")


def main():
    """Función principal del job."""
    # Obtener argumentos del job
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'SOURCE_BUCKET',
        'TARGET_BUCKET',
        'DATABASE_NAME'
    ])
    
    # Inicializar contextos
    sc = SparkContext()
    glue_context = GlueContext(sc)
    job = Job(glue_context)
    job.init(args['JOB_NAME'], args)
    
    # Crear procesador
    processor = CustomerSatisfactionProcessor(glue_context, args['JOB_NAME'])
    
    try:
        # Variables de configuración
        database_name = args.get('DATABASE_NAME', 'customer_satisfaction_db')
        source_bucket = args['SOURCE_BUCKET']
        target_bucket = args['TARGET_BUCKET']
        
        # Leer datos crudos
        tickets_df = processor.read_raw_data(database_name, 'customer_tickets')
        nps_df = processor.read_raw_data(database_name, 'nps_surveys')
        reviews_df = processor.read_raw_data(database_name, 'customer_reviews')
        
        # Procesar datos
        tickets_clean = processor.clean_customer_tickets(tickets_df)
        nps_clean = processor.clean_nps_surveys(nps_df)
        reviews_clean = processor.clean_customer_reviews(reviews_df)
        
        # Calcular métricas
        satisfaction_metrics = processor.calculate_satisfaction_metrics(
            tickets_clean, nps_clean
        )
        
        # Escribir datos procesados
        base_path = f"s3://{target_bucket}/processed-data"
        
        processor.write_processed_data(
            tickets_clean,
            f"{base_path}/customer_tickets_processed/",
            ["year", "month", "day"]
        )
        
        processor.write_processed_data(
            nps_clean,
            f"{base_path}/nps_surveys_processed/",
            ["year", "month", "day"]
        )
        
        processor.write_processed_data(
            reviews_clean,
            f"{base_path}/customer_reviews_processed/",
            ["year", "month", "day"]
        )
        
        processor.write_processed_data(
            satisfaction_metrics,
            f"{base_path}/satisfaction_metrics/",
            ["year", "month", "day"]
        )
        
        # Actualizar Data Catalog
        processor.update_data_catalog(
            database_name, 
            'customer_tickets_processed',
            f"{base_path}/customer_tickets_processed/",
            ["year", "month", "day"]
        )
        
        processor.update_data_catalog(
            database_name,
            'satisfaction_metrics',
            f"{base_path}/satisfaction_metrics/",
            ["year", "month", "day"]
        )
        
        processor.logger.info("Job completado exitosamente")
        
    except Exception as e:
        processor.logger.error(f"Error en el job: {e}")
        raise
    finally:
        job.commit()


if __name__ == "__main__":
    main() 