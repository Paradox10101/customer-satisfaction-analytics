"""
Modelo de Machine Learning para predicción de satisfacción del cliente.

Este módulo implementa:
- Modelos de clasificación y regresión para satisfacción
- Feature engineering avanzado
- Validación cruzada y métricas de evaluación
- Interpretabilidad con SHAP
- Pipeline completo de entrenamiento y predicción
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import logging

# Machine Learning
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve
)

# Advanced ML
import xgboost as xgb
import lightgbm as lgb
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

# Feature Selection
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.feature_selection import RFE

# Interpretabilidad
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    warnings.warn("SHAP no disponible. Instalar con: pip install shap")

# Validación de modelos
from sklearn.model_selection import TimeSeriesSplit
import optuna

warnings.filterwarnings('ignore')


class SatisfactionPredictor:
    """Predictor de satisfacción del cliente usando Machine Learning."""
    
    def __init__(self, task_type: str = 'classification', random_state: int = 42):
        """
        Inicializar el predictor.
        
        Args:
            task_type: 'classification' o 'regression'
            random_state: Semilla para reproducibilidad
        """
        self.task_type = task_type
        self.random_state = random_state
        self.models = {}
        self.preprocessor = None
        self.feature_names = None
        self.target_encoder = None
        self.is_fitted = False
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Inicializar modelos
        self._setup_models()
    
    def _setup_models(self):
        """Configurar modelos base."""
        if self.task_type == 'classification':
            self.models = {
                'random_forest': RandomForestClassifier(
                    n_estimators=100,
                    random_state=self.random_state,
                    n_jobs=-1
                ),
                'logistic_regression': LogisticRegression(
                    random_state=self.random_state,
                    max_iter=1000
                ),
                'xgboost': xgb.XGBClassifier(
                    random_state=self.random_state,
                    eval_metric='logloss'
                ),
                'lightgbm': lgb.LGBMClassifier(
                    random_state=self.random_state,
                    verbose=-1
                )
            }
        else:  # regression
            self.models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    random_state=self.random_state,
                    n_jobs=-1
                ),
                'linear_regression': LinearRegression(),
                'xgboost': xgb.XGBRegressor(
                    random_state=self.random_state
                ),
                'lightgbm': lgb.LGBMRegressor(
                    random_state=self.random_state,
                    verbose=-1
                )
            }
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crear características avanzadas para el modelo.
        
        Args:
            df: DataFrame con datos de tickets
            
        Returns:
            DataFrame con características engineered
        """
        features_df = df.copy()
        
        # 1. Características temporales
        if 'fecha_creacion' in features_df.columns:
            features_df['fecha_creacion'] = pd.to_datetime(features_df['fecha_creacion'])
            features_df['hora'] = features_df['fecha_creacion'].dt.hour
            features_df['dia_semana'] = features_df['fecha_creacion'].dt.dayofweek
            features_df['mes'] = features_df['fecha_creacion'].dt.month
            features_df['trimestre'] = features_df['fecha_creacion'].dt.quarter
            features_df['es_fin_semana'] = (features_df['dia_semana'] >= 5).astype(int)
            features_df['es_horario_pico'] = (
                (features_df['hora'].between(9, 11)) | 
                (features_df['hora'].between(14, 16))
            ).astype(int)
        
        # 2. Características de duración
        if 'duracion_minutos' in features_df.columns:
            features_df['duracion_log'] = np.log1p(features_df['duracion_minutos'])
            features_df['duracion_categoria'] = pd.cut(
                features_df['duracion_minutos'],
                bins=[0, 5, 15, 30, np.inf],
                labels=['rapido', 'normal', 'largo', 'muy_largo']
            )
            features_df['es_duracion_extrema'] = (
                (features_df['duracion_minutos'] < 2) | 
                (features_df['duracion_minutos'] > 60)
            ).astype(int)
        
        # 3. Características por agente
        if 'agente_id' in features_df.columns:
            agente_stats = features_df.groupby('agente_id').agg({
                'satisfaccion_score': ['mean', 'count', 'std'],
                'duracion_minutos': 'mean'
            }).fillna(0)
            
            agente_stats.columns = [
                'agente_satisfaccion_promedio',
                'agente_total_tickets',
                'agente_satisfaccion_std',
                'agente_duracion_promedio'
            ]
            
            features_df = features_df.merge(
                agente_stats,
                left_on='agente_id',
                right_index=True,
                how='left'
            )
        
        # 4. Características por canal
        if 'canal' in features_df.columns:
            canal_stats = features_df.groupby('canal').agg({
                'satisfaccion_score': 'mean',
                'duracion_minutos': 'mean'
            })
            
            canal_stats.columns = [
                'canal_satisfaccion_promedio',
                'canal_duracion_promedio'
            ]
            
            features_df = features_df.merge(
                canal_stats,
                left_on='canal',
                right_index=True,
                how='left'
            )
        
        # 5. Características de cliente VIP
        if 'cliente_vip' in features_df.columns:
            features_df['cliente_vip_int'] = features_df['cliente_vip'].astype(int)
        
        # 6. Características de resolución
        if 'resolucion' in features_df.columns:
            features_df['es_resuelto'] = (features_df['resolucion'] == 'resuelto').astype(int)
            features_df['es_escalado'] = (features_df['resolucion'] == 'escalado').astype(int)
        
        # 7. Características de prioridad
        if 'prioridad' in features_df.columns:
            prioridad_map = {'baja': 1, 'media': 2, 'alta': 3, 'critica': 4}
            features_df['prioridad_numerica'] = features_df['prioridad'].map(prioridad_map)
        
        # 8. Interacciones entre características
        if 'canal' in features_df.columns and 'es_fin_semana' in features_df.columns:
            features_df['canal_fin_semana'] = (
                features_df['canal'] + '_' + 
                features_df['es_fin_semana'].astype(str)
            )
        
        # 9. Características estadísticas
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['satisfaccion_score']:  # No incluir target
                Q1 = features_df[col].quantile(0.25)
                Q3 = features_df[col].quantile(0.75)
                features_df[f'{col}_es_outlier'] = (
                    (features_df[col] < Q1 - 1.5*(Q3-Q1)) |
                    (features_df[col] > Q3 + 1.5*(Q3-Q1))
                ).astype(int)
        
        self.logger.info(f"Características creadas: {features_df.shape[1]} columnas")
        return features_df
    
    def prepare_data(self, df: pd.DataFrame, target_column: str = 'satisfaccion_score') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Preparar datos para entrenamiento.
        
        Args:
            df: DataFrame con datos
            target_column: Nombre de la columna objetivo
            
        Returns:
            Tupla (X, y) con características y target
        """
        # Crear características
        df_features = self.create_features(df)
        
        # Separar características y target
        if target_column not in df_features.columns:
            raise ValueError(f"Columna target '{target_column}' no encontrada")
        
        y = df_features[target_column].copy()
        
        # Seleccionar características relevantes
        feature_columns = [
            'duracion_minutos', 'duracion_log', 'hora', 'dia_semana', 'mes',
            'es_fin_semana', 'es_horario_pico', 'es_duracion_extrema',
            'prioridad_numerica', 'cliente_vip_int', 'es_resuelto', 'es_escalado'
        ]
        
        # Agregar características calculadas si existen
        calculated_features = [col for col in df_features.columns if 
                             any(prefix in col for prefix in ['agente_', 'canal_']) and 
                             col not in ['agente_id', 'canal']]
        feature_columns.extend(calculated_features)
        
        # Características categóricas para encoding
        categorical_features = ['canal', 'departamento', 'tipo_consulta', 'resolucion']
        
        # Filtrar columnas que existen
        existing_numeric = [col for col in feature_columns if col in df_features.columns]
        existing_categorical = [col for col in categorical_features if col in df_features.columns]
        
        X = df_features[existing_numeric + existing_categorical].copy()
        
        # Convertir target si es clasificación
        if self.task_type == 'classification':
            # Crear categorías de satisfacción
            if y.min() >= 1 and y.max() <= 5:  # Escala 1-5
                y_cat = pd.cut(y, bins=[0, 2.5, 3.5, 5], labels=['bajo', 'medio', 'alto'])
                self.target_encoder = LabelEncoder()
                y = self.target_encoder.fit_transform(y_cat)
        
        self.feature_names = X.columns.tolist()
        self.logger.info(f"Datos preparados: {X.shape[0]} muestras, {X.shape[1]} características")
        
        return X, y
    
    def create_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        """
        Crear pipeline de preprocesamiento.
        
        Args:
            X: DataFrame con características
            
        Returns:
            Preprocesador configurado
        """
        # Identificar tipos de columnas
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Pipeline para características numéricas
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # Pipeline para características categóricas
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        
        # Combinar transformadores
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ]
        )
        
        return preprocessor
    
    def train_models(self, X: pd.DataFrame, y: pd.Series, 
                    test_size: float = 0.2, cv_folds: int = 5) -> Dict:
        """
        Entrenar y evaluar múltiples modelos.
        
        Args:
            X: Características
            y: Variable objetivo
            test_size: Proporción de datos para test
            cv_folds: Número de folds para validación cruzada
            
        Returns:
            Diccionario con resultados de entrenamiento
        """
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state,
            stratify=y if self.task_type == 'classification' else None
        )
        
        # Crear preprocesador
        self.preprocessor = self.create_preprocessor(X_train)
        
        # Resultados
        results = {
            'models': {},
            'best_model': None,
            'best_score': -np.inf if self.task_type == 'regression' else 0,
            'feature_importance': {},
            'test_predictions': {}
        }
        
        # Métrica de evaluación
        scoring = 'neg_mean_squared_error' if self.task_type == 'regression' else 'accuracy'
        
        for model_name, model in self.models.items():
            self.logger.info(f"Entrenando {model_name}...")
            
            try:
                # Pipeline completo
                pipeline = Pipeline([
                    ('preprocessor', self.preprocessor),
                    ('model', model)
                ])
                
                # Validación cruzada
                cv_scores = cross_val_score(
                    pipeline, X_train, y_train, 
                    cv=cv_folds, scoring=scoring, n_jobs=-1
                )
                
                # Entrenar en todos los datos de entrenamiento
                pipeline.fit(X_train, y_train)
                
                # Predicciones en test
                y_pred = pipeline.predict(X_test)
                
                # Calcular métricas
                if self.task_type == 'classification':
                    test_score = accuracy_score(y_test, y_pred)
                    metrics = {
                        'accuracy': test_score,
                        'precision': precision_score(y_test, y_pred, average='weighted'),
                        'recall': recall_score(y_test, y_pred, average='weighted'),
                        'f1': f1_score(y_test, y_pred, average='weighted')
                    }
                    
                    # AUC si es binario
                    if len(np.unique(y)) == 2:
                        y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
                        metrics['auc'] = roc_auc_score(y_test, y_pred_proba)
                else:
                    test_score = -mean_squared_error(y_test, y_pred)  # Negativo para maximizar
                    metrics = {
                        'mse': mean_squared_error(y_test, y_pred),
                        'mae': mean_absolute_error(y_test, y_pred),
                        'r2': r2_score(y_test, y_pred)
                    }
                
                # Guardar resultados
                results['models'][model_name] = {
                    'pipeline': pipeline,
                    'cv_scores': cv_scores,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'test_score': test_score,
                    'metrics': metrics
                }
                
                results['test_predictions'][model_name] = y_pred
                
                # Actualizar mejor modelo
                if test_score > results['best_score']:
                    results['best_score'] = test_score
                    results['best_model'] = model_name
                
                # Feature importance (si disponible)
                if hasattr(pipeline.named_steps['model'], 'feature_importances_'):
                    importance = pipeline.named_steps['model'].feature_importances_
                    # Obtener nombres de características después del preprocessing
                    feature_names = self._get_feature_names_after_preprocessing(pipeline)
                    results['feature_importance'][model_name] = dict(zip(feature_names, importance))
                
                self.logger.info(f"{model_name} - CV: {cv_scores.mean():.4f} (±{cv_scores.std():.4f}), Test: {test_score:.4f}")
                
            except Exception as e:
                self.logger.error(f"Error entrenando {model_name}: {e}")
                continue
        
        # Marcar como entrenado
        self.is_fitted = True
        
        # Guardar datos de test para análisis
        results['X_test'] = X_test
        results['y_test'] = y_test
        
        return results
    
    def _get_feature_names_after_preprocessing(self, pipeline) -> List[str]:
        """Obtener nombres de características después del preprocessing."""
        try:
            # Para ColumnTransformer con OneHotEncoder
            preprocessor = pipeline.named_steps['preprocessor']
            
            # Características numéricas
            numeric_features = preprocessor.transformers_[0][2]
            
            # Características categóricas (después de OneHot)
            categorical_features = []
            if len(preprocessor.transformers_) > 1:
                cat_transformer = preprocessor.transformers_[1][1]
                if hasattr(cat_transformer.named_steps['onehot'], 'get_feature_names_out'):
                    cat_feature_names = cat_transformer.named_steps['onehot'].get_feature_names_out()
                    categorical_features = cat_feature_names.tolist()
            
            return list(numeric_features) + categorical_features

        except (KeyError, AttributeError, ValueError):
            # Fallback a nombres genericos si la pipeline no tiene los steps esperados
            n_features = pipeline.named_steps['model'].n_features_in_
            return [f'feature_{i}' for i in range(n_features)]
    
    def optimize_hyperparameters(self, X: pd.DataFrame, y: pd.Series, 
                                model_name: str = 'xgboost', n_trials: int = 100) -> Dict:
        """
        Optimizar hiperparámetros usando Optuna.
        
        Args:
            X: Características
            y: Variable objetivo
            model_name: Nombre del modelo a optimizar
            n_trials: Número de trials para optimización
            
        Returns:
            Mejores parámetros encontrados
        """
        def objective(trial):
            # Parámetros específicos por modelo
            if model_name == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
                }
                if self.task_type == 'classification':
                    model = xgb.XGBClassifier(**params, random_state=self.random_state)
                else:
                    model = xgb.XGBRegressor(**params, random_state=self.random_state)
                    
            elif model_name == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                    'max_depth': trial.suggest_int('max_depth', 5, 20),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5)
                }
                if self.task_type == 'classification':
                    model = RandomForestClassifier(**params, random_state=self.random_state)
                else:
                    model = RandomForestRegressor(**params, random_state=self.random_state)
            else:
                raise ValueError(f"Optimización no implementada para {model_name}")
            
            # Pipeline con preprocesamiento
            pipeline = Pipeline([
                ('preprocessor', self.create_preprocessor(X)),
                ('model', model)
            ])
            
            # Validación cruzada
            scoring = 'neg_mean_squared_error' if self.task_type == 'regression' else 'accuracy'
            scores = cross_val_score(pipeline, X, y, cv=3, scoring=scoring)
            
            return scores.mean()
        
        # Optimización
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        self.logger.info(f"Mejores parámetros para {model_name}: {study.best_params}")
        self.logger.info(f"Mejor score: {study.best_value:.4f}")
        
        return {
            'best_params': study.best_params,
            'best_score': study.best_value,
            'study': study
        }
    
    def analyze_feature_importance(self, results: Dict, top_n: int = 15) -> None:
        """
        Analizar y visualizar importancia de características.
        
        Args:
            results: Resultados del entrenamiento
            top_n: Número de características top a mostrar
        """
        if not results['feature_importance']:
            self.logger.warning("No hay datos de feature importance disponibles")
            return
        
        # Crear subplot para cada modelo
        n_models = len(results['feature_importance'])
        fig, axes = plt.subplots(1, n_models, figsize=(6*n_models, 8))
        
        if n_models == 1:
            axes = [axes]
        
        for idx, (model_name, importance) in enumerate(results['feature_importance'].items()):
            # Ordenar por importancia
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
            features, values = zip(*sorted_features)
            
            # Graficar
            axes[idx].barh(range(len(features)), values)
            axes[idx].set_yticks(range(len(features)))
            axes[idx].set_yticklabels(features)
            axes[idx].set_title(f'Feature Importance - {model_name.title()}')
            axes[idx].set_xlabel('Importancia')
        
        plt.tight_layout()
        plt.show()
    
    def generate_shap_analysis(self, results: Dict, X_sample: Optional[pd.DataFrame] = None) -> None:
        """
        Generar análisis SHAP para interpretabilidad.
        
        Args:
            results: Resultados del entrenamiento
            X_sample: Muestra de datos para análisis (opcional)
        """
        if not SHAP_AVAILABLE:
            self.logger.warning("SHAP no disponible")
            return
        
        best_model_name = results['best_model']
        best_pipeline = results['models'][best_model_name]['pipeline']
        
        if X_sample is None:
            X_sample = results['X_test'].sample(min(100, len(results['X_test'])))
        
        try:
            # Transformar datos
            X_transformed = best_pipeline.named_steps['preprocessor'].transform(X_sample)
            
            # Crear explainer
            explainer = shap.TreeExplainer(best_pipeline.named_steps['model'])
            shap_values = explainer.shap_values(X_transformed)
            
            # Visualizaciones SHAP
            plt.figure(figsize=(12, 8))
            
            # Summary plot
            shap.summary_plot(shap_values, X_transformed, 
                            feature_names=self._get_feature_names_after_preprocessing(best_pipeline),
                            show=False)
            plt.title(f'SHAP Summary - {best_model_name.title()}')
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            self.logger.error(f"Error en análisis SHAP: {e}")
    
    def predict(self, X: pd.DataFrame, model_name: str = None) -> np.ndarray:
        """
        Hacer predicciones con el modelo entrenado.
        
        Args:
            X: Características para predicción
            model_name: Nombre del modelo a usar (usa el mejor si es None)
            
        Returns:
            Predicciones
        """
        if not self.is_fitted:
            raise ValueError("Modelo no entrenado. Ejecutar train_models() primero.")
        
        if model_name is None:
            model_name = self.best_model_name
        
        pipeline = self.trained_models[model_name]['pipeline']
        return pipeline.predict(X)
    
    def save_model(self, results: Dict, filepath: str) -> None:
        """
        Guardar modelo entrenado.
        
        Args:
            results: Resultados del entrenamiento
            filepath: Ruta donde guardar el modelo
        """
        model_data = {
            'best_model_name': results['best_model'],
            'best_pipeline': results['models'][results['best_model']]['pipeline'],
            'feature_names': self.feature_names,
            'task_type': self.task_type,
            'target_encoder': self.target_encoder,
            'training_results': results
        }
        
        joblib.dump(model_data, filepath)
        self.logger.info(f"Modelo guardado en: {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str) -> 'SatisfactionPredictor':
        """
        Cargar modelo guardado.
        
        Args:
            filepath: Ruta del modelo guardado
            
        Returns:
            Instancia del predictor cargado
        """
        model_data = joblib.load(filepath)
        
        predictor = cls(task_type=model_data['task_type'])
        predictor.best_model_name = model_data['best_model_name']
        predictor.trained_models = {
            model_data['best_model_name']: {
                'pipeline': model_data['best_pipeline']
            }
        }
        predictor.feature_names = model_data['feature_names']
        predictor.target_encoder = model_data['target_encoder']
        predictor.is_fitted = True
        
        return predictor


def main():
    """Función principal para demo del predictor."""
    # Simular datos de ejemplo
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'ticket_id': [f'TKT-{i:06d}' for i in range(n_samples)],
        'fecha_creacion': pd.date_range('2024-01-01', periods=n_samples, freq='4H'),
        'cliente_id': [f'CLI-{np.random.randint(1000, 9999)}' for _ in range(n_samples)],
        'canal': np.random.choice(['telefono', 'chat', 'email', 'presencial'], n_samples),
        'departamento': np.random.choice(['soporte', 'ventas', 'tecnico'], n_samples),
        'tipo_consulta': np.random.choice(['consulta', 'reclamo', 'solicitud'], n_samples),
        'duracion_minutos': np.random.lognormal(2, 1, n_samples),
        'resolucion': np.random.choice(['resuelto', 'escalado', 'pendiente'], n_samples),
        'prioridad': np.random.choice(['baja', 'media', 'alta'], n_samples),
        'cliente_vip': np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
        'agente_id': [f'AGT-{np.random.randint(1, 20):03d}' for _ in range(n_samples)]
    }
    
    # Crear target basado en características
    satisfaction_base = 3.5
    for i in range(n_samples):
        score = satisfaction_base
        
        # Ajustar por canal
        if data['canal'][i] == 'presencial':
            score += 0.5
        elif data['canal'][i] == 'chat':
            score += 0.3
        elif data['canal'][i] == 'email':
            score -= 0.2
        
        # Ajustar por duración
        if data['duracion_minutos'][i] > 30:
            score -= 0.8
        elif data['duracion_minutos'][i] < 5:
            score += 0.3
        
        # Ajustar por resolución
        if data['resolucion'][i] == 'resuelto':
            score += 0.7
        elif data['resolucion'][i] == 'escalado':
            score -= 0.5
        
        # Agregar ruido
        score += np.random.normal(0, 0.5)
        
        # Limitar entre 1 y 5
        data['satisfaccion_score'] = data.get('satisfaccion_score', []) + [max(1, min(5, score))]
    
    # Crear DataFrame
    df = pd.DataFrame(data)
    
    print("=== Demo del Predictor de Satisfacción ===")
    print(f"Dataset: {df.shape[0]} muestras, {df.shape[1]} características")
    print(f"Satisfacción promedio: {df['satisfaccion_score'].mean():.2f}")
    print(f"Distribución por canal:\n{df.groupby('canal')['satisfaccion_score'].mean()}")
    
    # Crear y entrenar predictor
    predictor = SatisfactionPredictor(task_type='regression')
    
    # Preparar datos
    X, y = predictor.prepare_data(df)
    
    # Entrenar modelos
    results = predictor.train_models(X, y)
    
    # Mostrar resultados
    print(f"\n=== Resultados del Entrenamiento ===")
    print(f"Mejor modelo: {results['best_model']}")
    print(f"Mejor score: {results['best_score']:.4f}")
    
    for model_name, model_results in results['models'].items():
        print(f"\n{model_name.title()}:")
        print(f"  CV Score: {model_results['cv_mean']:.4f} (±{model_results['cv_std']:.4f})")
        print(f"  Test Score: {model_results['test_score']:.4f}")
        for metric, value in model_results['metrics'].items():
            print(f"  {metric.upper()}: {value:.4f}")
    
    # Análisis de feature importance
    predictor.analyze_feature_importance(results)
    
    # Guardar modelo
    predictor.save_model(results, 'satisfaction_model.joblib')
    print(f"\nModelo guardado exitosamente!")


if __name__ == "__main__":
    main() 