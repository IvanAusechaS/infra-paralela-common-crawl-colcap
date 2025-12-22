"""
Correlation Engine - News2Market

Motor de cálculo de correlaciones estadísticas entre métricas noticiosas y COLCAP.
Implementa correlación de Pearson y generación de insights.

Autor: Equipo News2Market
Versión: 1.0.0
"""

import logging
from typing import List, Dict, Tuple, Any
from scipy.stats import pearsonr
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """Motor de análisis de correlación"""
    
    def __init__(self):
        """Inicializar motor de correlación"""
        logger.info("✅ CorrelationEngine inicializado")
    
    def get_news_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Obtener métricas agregadas de noticias por fecha
        
        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            
        Returns:
            List[Dict]: Métricas diarias
        """
        # TODO: Implementar consulta real a base de datos
        # Por ahora retorna datos simulados
        
        from datetime import datetime, timedelta
        import random
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        metrics = []
        current_date = start
        
        while current_date <= end:
            metrics.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "volume": random.randint(10, 100),  # Número de artículos
                "keywords": random.randint(50, 500),  # Total de keywords económicas
                "sentiment": random.uniform(-0.5, 0.5)  # Sentimiento promedio
            })
            current_date += timedelta(days=1)
        
        return metrics
    
    def calculate_pearson_correlation(
        self,
        colcap_data: List[Dict[str, Any]],
        news_metrics: List[Dict[str, Any]],
        metric_name: str,
        lag_days: int = 0
    ) -> Tuple[float, float]:
        """
        Calcular correlación de Pearson entre una métrica noticiosa y COLCAP
        
        Args:
            colcap_data: Datos de COLCAP
            news_metrics: Métricas de noticias
            metric_name: Nombre de la métrica a correlacionar
            lag_days: Días de retraso temporal
            
        Returns:
            Tuple[float, float]: (correlación, p-value)
        """
        try:
            # Crear diccionarios por fecha
            colcap_by_date = {d['date']: d['closing_price'] for d in colcap_data}
            news_by_date = {m['date']: m[metric_name] for m in news_metrics}
            
            # Obtener fechas comunes
            common_dates = sorted(set(colcap_by_date.keys()) & set(news_by_date.keys()))
            
            if len(common_dates) < 3:
                logger.warning(f"⚠️ Datos insuficientes para correlación: {len(common_dates)} días")
                return 0.0, 1.0
            
            # Extraer valores para las fechas comunes
            colcap_values = [colcap_by_date[date] for date in common_dates]
            news_values = [news_by_date[date] for date in common_dates]
            
            # Calcular correlación de Pearson
            correlation, p_value = pearsonr(colcap_values, news_values)
            
            logger.info(
                f"✅ Correlación {metric_name}: r={correlation:.3f}, p={p_value:.4f}"
            )
            
            return round(correlation, 4), round(p_value, 4)
            
        except Exception as e:
            logger.error(f"❌ Error calculando correlación: {e}")
            return 0.0, 1.0
    
    def generate_insights(
        self,
        correlations: Dict[str, float],
        p_values: Dict[str, float],
        sample_size: int
    ) -> List[str]:
        """
        Generar insights interpretativos de las correlaciones
        
        Args:
            correlations: Dict con correlaciones calculadas
            p_values: Dict con p-values
            sample_size: Tamaño de la muestra
            
        Returns:
            List[str]: Lista de insights
        """
        insights = []
        
        # Insight sobre tamaño de muestra
        if sample_size < 10:
            insights.append(
                f"⚠️ Tamaño de muestra pequeño ({sample_size} días). "
                "Resultados pueden no ser confiables."
            )
        elif sample_size < 30:
            insights.append(
                f"ℹ️ Tamaño de muestra moderado ({sample_size} días). "
                "Se recomienda más datos para mayor confiabilidad."
            )
        else:
            insights.append(
                f"✅ Tamaño de muestra adecuado ({sample_size} días) "
                "para análisis estadístico."
            )
        
        # Insights por métrica
        for metric, corr in correlations.items():
            p_val = p_values.get(metric, 1.0)
            
            # Interpretar magnitud de correlación
            abs_corr = abs(corr)
            if abs_corr < 0.2:
                strength = "muy débil"
            elif abs_corr < 0.4:
                strength = "débil"
            elif abs_corr < 0.6:
                strength = "moderada"
            elif abs_corr < 0.8:
                strength = "fuerte"
            else:
                strength = "muy fuerte"
            
            # Interpretar dirección
            direction = "positiva" if corr > 0 else "negativa"
            
            # Interpretar significancia estadística
            if p_val < 0.01:
                significance = "altamente significativa (p < 0.01)"
            elif p_val < 0.05:
                significance = "estadísticamente significativa (p < 0.05)"
            elif p_val < 0.1:
                significance = "marginalmente significativa (p < 0.1)"
            else:
                significance = "no significativa estadísticamente"
            
            insight = (
                f"📊 {metric.capitalize()}: Correlación {strength} "
                f"{direction} (r={corr:.3f}), {significance}."
            )
            
            # Agregar interpretación práctica
            if abs_corr > 0.5 and p_val < 0.05:
                if corr > 0:
                    insight += f" Mayor {metric} de noticias tiende a asociarse con mayor valor de COLCAP."
                else:
                    insight += f" Mayor {metric} de noticias tiende a asociarse con menor valor de COLCAP."
            
            insights.append(insight)
        
        return insights
