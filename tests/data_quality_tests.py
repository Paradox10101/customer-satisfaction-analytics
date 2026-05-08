"""
Tests de calidad de datos para el proyecto de análisis de satisfacción del cliente.

Valida:
- Integridad de datos simulados
- Consistencia entre datasets
- Rangos de valores válidos
- Completitud de datos
"""

import pandas as pd
import numpy as np
import pytest
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
import logging

# Configurar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Validador de calidad de datos."""
    
    def __init__(self, data_dir: str = "data/simulated"):
        """
        Inicializar validador.
        
        Args:
            data_dir: Directorio con datos a validar
        """
        self.data_dir = data_dir
        self.datasets = {}
        self.validation_results = {}
        
    def load_datasets(self) -> None:
        """Cargar todos los datasets disponibles."""
        dataset_files = {
            'customer_tickets': 'customer_tickets.csv',
            'nps_surveys': 'nps_surveys.csv', 
            'customer_reviews': 'customer_reviews.csv',
            'conversation_transcripts': 'conversation_transcripts.csv'
        }
        
        for name, filename in dataset_files.items():
            file_path = os.path.join(self.data_dir, filename)
            if os.path.exists(file_path):
                try:
                    self.datasets[name] = pd.read_csv(file_path)
                    logger.info(f"Cargado {name}: {len(self.datasets[name])} registros")
                except Exception as e:
                    logger.error(f"Error cargando {name}: {e}")
                    self.datasets[name] = None
            else:
                logger.warning(f"Archivo no encontrado: {file_path}")
                self.datasets[name] = None
    
    def validate_customer_tickets(self) -> Dict:
        """Validar dataset de tickets de cliente."""
        df = self.datasets.get('customer_tickets')
        if df is None:
            return {"status": "error", "message": "Dataset no disponible"}
        
        issues = []
        stats = {}
        
        # 1. Validar estructura de datos
        required_columns = [
            'ticket_id', 'fecha_creacion', 'cliente_id', 'canal', 
            'departamento', 'tipo_consulta', 'duracion_minutos', 
            'resolucion', 'satisfaccion_score', 'agente_id'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Columnas faltantes: {missing_columns}")
        
        # 2. Validar completitud
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                null_percentage = (null_count / len(df)) * 100
                stats[f"{col}_null_percentage"] = null_percentage
                
                if null_percentage > 5:  # Más del 5% de nulos
                    issues.append(f"Muchos nulos en {col}: {null_percentage:.1f}%")
        
        # 3. Validar rangos de valores
        if 'satisfaccion_score' in df.columns:
            invalid_scores = df[
                (df['satisfaccion_score'] < 1) | 
                (df['satisfaccion_score'] > 5) |
                df['satisfaccion_score'].isnull()
            ]
            if len(invalid_scores) > 0:
                issues.append(f"Scores de satisfacción inválidos: {len(invalid_scores)} registros")
            
            stats['satisfaccion_promedio'] = df['satisfaccion_score'].mean()
            stats['satisfaccion_std'] = df['satisfaccion_score'].std()
        
        if 'duracion_minutos' in df.columns:
            invalid_duration = df[
                (df['duracion_minutos'] <= 0) | 
                (df['duracion_minutos'] > 480) |  # Más de 8 horas
                df['duracion_minutos'].isnull()
            ]
            if len(invalid_duration) > 0:
                issues.append(f"Duraciones inválidas: {len(invalid_duration)} registros")
            
            stats['duracion_promedio'] = df['duracion_minutos'].mean()
            stats['duracion_mediana'] = df['duracion_minutos'].median()
        
        # 4. Validar valores categóricos
        if 'canal' in df.columns:
            expected_channels = ['telefono', 'chat', 'email', 'presencial', 'app_movil']
            invalid_channels = df[~df['canal'].isin(expected_channels)]
            if len(invalid_channels) > 0:
                issues.append(f"Canales inválidos: {len(invalid_channels)} registros")
            
            stats['distribucion_canales'] = df['canal'].value_counts().to_dict()
        
        if 'resolucion' in df.columns:
            expected_resolutions = ['resuelto', 'escalado', 'pendiente', 'cerrado_sin_resolucion']
            invalid_resolutions = df[~df['resolucion'].isin(expected_resolutions)]
            if len(invalid_resolutions) > 0:
                issues.append(f"Resoluciones inválidas: {len(invalid_resolutions)} registros")
        
        # 5. Validar unicidad de IDs
        if 'ticket_id' in df.columns:
            duplicate_ids = df['ticket_id'].duplicated().sum()
            if duplicate_ids > 0:
                issues.append(f"IDs duplicados: {duplicate_ids}")
        
        # 6. Validar fechas
        if 'fecha_creacion' in df.columns:
            try:
                df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
                
                # Verificar rango de fechas razonable
                min_date = df['fecha_creacion'].min()
                max_date = df['fecha_creacion'].max()
                today = datetime.now()
                
                if min_date < today - timedelta(days=730):  # Más de 2 años atrás
                    issues.append(f"Fechas muy antiguas: {min_date}")
                
                if max_date > today + timedelta(days=1):  # Fechas futuras
                    issues.append(f"Fechas futuras: {max_date}")
                
                stats['rango_fechas'] = {
                    'min': min_date.isoformat(),
                    'max': max_date.isoformat()
                }
                
            except Exception as e:
                issues.append(f"Error procesando fechas: {e}")
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "stats": stats,
            "total_records": len(df)
        }
    
    def validate_nps_surveys(self) -> Dict:
        """Validar dataset de encuestas NPS."""
        df = self.datasets.get('nps_surveys')
        if df is None:
            return {"status": "error", "message": "Dataset no disponible"}
        
        issues = []
        stats = {}
        
        # Validar NPS scores
        if 'nps_score' in df.columns:
            invalid_nps = df[
                (df['nps_score'] < 0) | 
                (df['nps_score'] > 10) |
                df['nps_score'].isnull()
            ]
            if len(invalid_nps) > 0:
                issues.append(f"NPS scores inválidos: {len(invalid_nps)} registros")
            
            stats['nps_promedio'] = df['nps_score'].mean()
            stats['distribucion_nps'] = df['nps_score'].value_counts().sort_index().to_dict()
        
        # Validar categorías NPS
        if 'categoria_nps' in df.columns:
            expected_categories = ['promotor', 'neutro', 'detractor']
            invalid_categories = df[~df['categoria_nps'].isin(expected_categories)]
            if len(invalid_categories) > 0:
                issues.append(f"Categorías NPS inválidas: {len(invalid_categories)} registros")
            
            stats['distribucion_categorias'] = df['categoria_nps'].value_counts().to_dict()
        
        # Validar coherencia entre score y categoría
        if 'nps_score' in df.columns and 'categoria_nps' in df.columns:
            # Verificar que promotores tengan score 9-10
            promotores_invalidos = df[
                (df['categoria_nps'] == 'promotor') & 
                (df['nps_score'] < 9)
            ]
            if len(promotores_invalidos) > 0:
                issues.append(f"Promotores con score < 9: {len(promotores_invalidos)}")
            
            # Verificar que detractores tengan score 0-6
            detractores_invalidos = df[
                (df['categoria_nps'] == 'detractor') & 
                (df['nps_score'] > 6)
            ]
            if len(detractores_invalidos) > 0:
                issues.append(f"Detractores con score > 6: {len(detractores_invalidos)}")
        
        # Validar comentarios
        if 'comentario' in df.columns:
            empty_comments = df[df['comentario'].isnull() | (df['comentario'] == '')].shape[0]
            if empty_comments > len(df) * 0.1:  # Más del 10% vacío
                issues.append(f"Muchos comentarios vacíos: {empty_comments}")
            
            stats['longitud_promedio_comentario'] = df['comentario'].str.len().mean()
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "stats": stats,
            "total_records": len(df)
        }
    
    def validate_customer_reviews(self) -> Dict:
        """Validar dataset de reviews de clientes."""
        df = self.datasets.get('customer_reviews')
        if df is None:
            return {"status": "error", "message": "Dataset no disponible"}
        
        issues = []
        stats = {}
        
        # Validar calificaciones
        if 'calificacion' in df.columns:
            invalid_ratings = df[
                (df['calificacion'] < 1) | 
                (df['calificacion'] > 5) |
                df['calificacion'].isnull()
            ]
            if len(invalid_ratings) > 0:
                issues.append(f"Calificaciones inválidas: {len(invalid_ratings)} registros")
            
            stats['calificacion_promedio'] = df['calificacion'].mean()
            stats['distribucion_calificaciones'] = df['calificacion'].value_counts().sort_index().to_dict()
        
        # Validar texto de reviews
        if 'texto_review' in df.columns:
            empty_reviews = df[df['texto_review'].isnull() | (df['texto_review'] == '')].shape[0]
            if empty_reviews > 0:
                issues.append(f"Reviews vacías: {empty_reviews}")
            
            # Verificar longitud mínima
            short_reviews = df[df['texto_review'].str.len() < 10].shape[0]
            if short_reviews > len(df) * 0.1:
                issues.append(f"Muchas reviews muy cortas: {short_reviews}")
            
            stats['longitud_promedio_review'] = df['texto_review'].str.len().mean()
        
        # Validar plataformas
        if 'plataforma' in df.columns:
            expected_platforms = ['google', 'facebook', 'trustpilot', 'web_oficial']
            invalid_platforms = df[~df['plataforma'].isin(expected_platforms)]
            if len(invalid_platforms) > 0:
                issues.append(f"Plataformas inválidas: {len(invalid_platforms)} registros")
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "stats": stats,
            "total_records": len(df)
        }
    
    def validate_conversation_transcripts(self) -> Dict:
        """Validar dataset de transcripciones."""
        df = self.datasets.get('conversation_transcripts')
        if df is None:
            return {"status": "error", "message": "Dataset no disponible"}
        
        issues = []
        stats = {}
        
        # Validar sentiment scores
        if 'sentiment_score' in df.columns:
            invalid_sentiment = df[
                (df['sentiment_score'] < -1) | 
                (df['sentiment_score'] > 1) |
                df['sentiment_score'].isnull()
            ]
            if len(invalid_sentiment) > 0:
                issues.append(f"Sentiment scores inválidos: {len(invalid_sentiment)} registros")
            
            stats['sentiment_promedio'] = df['sentiment_score'].mean()
        
        # Validar satisfacción estimada
        if 'satisfaccion_estimada' in df.columns:
            invalid_satisfaction = df[
                (df['satisfaccion_estimada'] < 1) | 
                (df['satisfaccion_estimada'] > 5) |
                df['satisfaccion_estimada'].isnull()
            ]
            if len(invalid_satisfaction) > 0:
                issues.append(f"Satisfacción estimada inválida: {len(invalid_satisfaction)} registros")
        
        # Validar transcripciones
        if 'transcript_texto' in df.columns:
            empty_transcripts = df[df['transcript_texto'].isnull() | (df['transcript_texto'] == '')].shape[0]
            if empty_transcripts > 0:
                issues.append(f"Transcripciones vacías: {empty_transcripts}")
            
            stats['longitud_promedio_transcript'] = df['transcript_texto'].str.len().mean()
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "stats": stats,
            "total_records": len(df)
        }
    
    def validate_cross_dataset_consistency(self) -> Dict:
        """Validar consistencia entre datasets."""
        issues = []
        stats = {}
        
        # Verificar que tengamos todos los datasets
        available_datasets = [name for name, df in self.datasets.items() if df is not None]
        expected_datasets = ['customer_tickets', 'nps_surveys', 'customer_reviews', 'conversation_transcripts']
        missing_datasets = [name for name in expected_datasets if name not in available_datasets]
        
        if missing_datasets:
            issues.append(f"Datasets faltantes: {missing_datasets}")
        
        # Verificar volúmenes relativos
        if len(available_datasets) >= 2:
            volumes = {name: len(self.datasets[name]) for name in available_datasets}
            stats['volumenes'] = volumes
            
            # Verificar que tickets sea el dataset más grande
            if 'customer_tickets' in volumes:
                tickets_volume = volumes['customer_tickets']
                for name, volume in volumes.items():
                    if name != 'customer_tickets' and volume > tickets_volume:
                        issues.append(f"{name} tiene más registros que tickets: {volume} vs {tickets_volume}")
        
        # Verificar rangos de fechas consistentes
        date_ranges = {}
        for name, df in self.datasets.items():
            if df is not None:
                date_cols = [col for col in df.columns if 'fecha' in col.lower()]
                if date_cols:
                    try:
                        df[date_cols[0]] = pd.to_datetime(df[date_cols[0]])
                        date_ranges[name] = {
                            'min': df[date_cols[0]].min(),
                            'max': df[date_cols[0]].max()
                        }
                    except (ValueError, TypeError):
                        # columna sin formato de fecha valido — saltar
                        pass
        
        if len(date_ranges) > 1:
            min_dates = [dr['min'] for dr in date_ranges.values()]
            max_dates = [dr['max'] for dr in date_ranges.values()]
            
            # Verificar que los rangos se solapen razonablemente
            global_min = min(min_dates)
            global_max = max(max_dates)
            
            for name, dr in date_ranges.items():
                # Cada dataset debería tener datos en al menos 50% del rango global
                dataset_range = (dr['max'] - dr['min']).days
                global_range = (global_max - global_min).days
                
                if dataset_range < global_range * 0.3:
                    issues.append(f"{name} tiene rango de fechas muy limitado")
        
        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "stats": stats
        }
    
    def run_all_validations(self) -> Dict:
        """Ejecutar todas las validaciones."""
        logger.info("Iniciando validación de calidad de datos...")
        
        # Cargar datasets
        self.load_datasets()
        
        # Ejecutar validaciones individuales
        validations = {
            'customer_tickets': self.validate_customer_tickets(),
            'nps_surveys': self.validate_nps_surveys(),
            'customer_reviews': self.validate_customer_reviews(),
            'conversation_transcripts': self.validate_conversation_transcripts(),
            'cross_dataset_consistency': self.validate_cross_dataset_consistency()
        }
        
        # Calcular resumen
        total_issues = sum(len(v.get('issues', [])) for v in validations.values())
        passed_validations = sum(1 for v in validations.values() if v.get('status') == 'pass')
        total_validations = len(validations)
        
        summary = {
            'overall_status': 'pass' if total_issues == 0 else 'fail',
            'total_issues': total_issues,
            'passed_validations': passed_validations,
            'total_validations': total_validations,
            'success_rate': (passed_validations / total_validations) * 100,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'summary': summary,
            'validations': validations
        }


# ===== PYTEST TESTS =====

@pytest.fixture
def validator():
    """Fixture para crear validador."""
    return DataQualityValidator()

def test_data_directory_exists(validator):
    """Test que el directorio de datos existe."""
    assert os.path.exists(validator.data_dir), f"Directorio de datos no existe: {validator.data_dir}"

def test_datasets_can_be_loaded(validator):
    """Test que los datasets se pueden cargar."""
    validator.load_datasets()
    
    # Al menos un dataset debe estar disponible
    available_datasets = [name for name, df in validator.datasets.items() if df is not None]
    assert len(available_datasets) > 0, "No se pudo cargar ningún dataset"

def test_customer_tickets_validation(validator):
    """Test validación de tickets de cliente."""
    validator.load_datasets()
    result = validator.validate_customer_tickets()
    
    if result['status'] != 'error':  # Si el dataset existe
        assert result['total_records'] > 0, "Dataset de tickets vacío"
        assert len(result['issues']) < 10, f"Demasiados issues: {result['issues']}"

def test_nps_surveys_validation(validator):
    """Test validación de encuestas NPS."""
    validator.load_datasets()
    result = validator.validate_nps_surveys()
    
    if result['status'] != 'error':
        assert result['total_records'] > 0, "Dataset de NPS vacío"
        assert len(result['issues']) < 5, f"Demasiados issues: {result['issues']}"

def test_customer_reviews_validation(validator):
    """Test validación de reviews."""
    validator.load_datasets()
    result = validator.validate_customer_reviews()
    
    if result['status'] != 'error':
        assert result['total_records'] > 0, "Dataset de reviews vacío"
        assert len(result['issues']) < 5, f"Demasiados issues: {result['issues']}"

def test_conversation_transcripts_validation(validator):
    """Test validación de transcripciones."""
    validator.load_datasets()
    result = validator.validate_conversation_transcripts()
    
    if result['status'] != 'error':
        assert result['total_records'] > 0, "Dataset de transcripciones vacío"
        assert len(result['issues']) < 5, f"Demasiados issues: {result['issues']}"

def test_cross_dataset_consistency(validator):
    """Test consistencia entre datasets."""
    validator.load_datasets()
    result = validator.validate_cross_dataset_consistency()
    
    assert len(result['issues']) < 3, f"Problemas de consistencia: {result['issues']}"

def test_overall_data_quality(validator):
    """Test de calidad general."""
    result = validator.run_all_validations()
    
    # Al menos 70% de validaciones deben pasar
    assert result['summary']['success_rate'] >= 70, \
        f"Tasa de éxito muy baja: {result['summary']['success_rate']}%"
    
    # No más de 20 issues en total
    assert result['summary']['total_issues'] <= 20, \
        f"Demasiados issues: {result['summary']['total_issues']}"


def main():
    """Función principal para ejecutar validaciones."""
    validator = DataQualityValidator()
    results = validator.run_all_validations()
    
    print("\n" + "="*60)
    print("🔍 REPORTE DE CALIDAD DE DATOS")
    print("="*60)
    
    summary = results['summary']
    print(f"📊 Estado General: {'✅ PASS' if summary['overall_status'] == 'pass' else '❌ FAIL'}")
    print(f"📈 Tasa de Éxito: {summary['success_rate']:.1f}%")
    print(f"🔢 Validaciones Pasadas: {summary['passed_validations']}/{summary['total_validations']}")
    print(f"⚠️ Total de Issues: {summary['total_issues']}")
    print(f"🕐 Timestamp: {summary['timestamp']}")
    
    print("\n" + "-"*60)
    print("📋 DETALLES POR DATASET")
    print("-"*60)
    
    for name, validation in results['validations'].items():
        status_icon = "✅" if validation['status'] == 'pass' else "❌" if validation['status'] == 'fail' else "⚠️"
        print(f"\n{status_icon} {name.replace('_', ' ').title()}")
        
        if 'total_records' in validation:
            print(f"   📊 Registros: {validation['total_records']:,}")
        
        if validation['issues']:
            print(f"   ⚠️ Issues:")
            for issue in validation['issues']:
                print(f"      • {issue}")
        
        if validation.get('stats'):
            print(f"   📈 Estadísticas:")
            for key, value in validation['stats'].items():
                if isinstance(value, dict):
                    print(f"      • {key}: {dict(list(value.items())[:3])}")  # Mostrar solo primeros 3
                elif isinstance(value, float):
                    print(f"      • {key}: {value:.2f}")
                else:
                    print(f"      • {key}: {value}")
    
    print("\n" + "="*60)
    
    # Retornar código de salida
    return 0 if summary['overall_status'] == 'pass' else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 