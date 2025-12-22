/**
 * HomePage - News2Market
 * 
 * Página de inicio con overview del proyecto
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import './HomePage.scss';

const HomePage = () => {
  const [stats, setStats] = useState<any>(null);
  const [isHealthy, setIsHealthy] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Health check
        const healthy = await api.healthCheck();
        setIsHealthy(healthy);

        // Obtener estadísticas
        if (healthy) {
          const statsData = await api.getProcessingStats();
          setStats(statsData);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="home-page">
      <header className="hero">
        <h1>📰 News2Market</h1>
        <p className="subtitle">
          Sistema distribuido para análisis de correlación entre noticias económicas
          y el índice COLCAP
        </p>
        
        <div className="status-indicator">
          <span className={`status-dot ${isHealthy ? 'online' : 'offline'}`}></span>
          <span className="status-text">
            {isHealthy ? 'Sistema operativo' : 'Sistema desconectado'}
          </span>
        </div>
      </header>

      <section className="features">
        <h2>Características principales</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <span className="feature-icon">🔍</span>
            <h3>Adquisición de datos</h3>
            <p>
              Extracción automática de noticias económicas desde Common Crawl
              con filtros específicos para el mercado colombiano.
            </p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">🧹</span>
            <h3>Procesamiento de texto</h3>
            <p>
              Limpieza, extracción de keywords económicas, análisis de sentimiento
              y procesamiento paralelo con múltiples workers.
            </p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">📊</span>
            <h3>Análisis de correlación</h3>
            <p>
              Cálculo de correlación de Pearson entre métricas noticiosas y
              el índice COLCAP con análisis temporal.
            </p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">☁️</span>
            <h3>Infraestructura escalable</h3>
            <p>
              Despliegue en AWS EKS con Kubernetes, autoescalado horizontal
              y balanceo de carga automático.
            </p>
          </div>
        </div>
      </section>

      {stats && (
        <section className="stats-section">
          <h2>Estadísticas del sistema</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.total_articles || 0}</div>
              <div className="stat-label">Artículos procesados</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.total_keywords || 0}</div>
              <div className="stat-label">Keywords económicas</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {stats.avg_sentiment ? stats.avg_sentiment.toFixed(2) : '0.00'}
              </div>
              <div className="stat-label">Sentimiento promedio</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.active_workers || 0}</div>
              <div className="stat-label">Workers activos</div>
            </div>
          </div>
        </section>
      )}

      <section className="cta-section">
        <h2>¿Listo para comenzar?</h2>
        <p>Inicia un nuevo análisis de correlación entre noticias y COLCAP</p>
        <Link to="/analysis" className="button primary">
          Iniciar análisis
        </Link>
      </section>
    </div>
  );
};

export default HomePage;
