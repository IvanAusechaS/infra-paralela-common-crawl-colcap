/**
 * HomePage - News2Market
 * Landing page with project overview and system status
 */

import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { api, notify } from "../services/api";
import "./HomePage.scss";

const HomePage = () => {
  const [stats, setStats] = useState<any>(null);
  const [isHealthy, setIsHealthy] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const notificationShownRef = useRef(false);

  useEffect(() => {
    window.scrollTo(0, 0);

    const fetchData = async () => {
      try {
        const healthy = await api.healthCheck();
        setIsHealthy(healthy);

        if (healthy) {
          // Get real stats from backend
          try {
            const correlationResults = await api.getCorrelationResults(100);
            const statsData = {
              totalArticles: correlationResults.reduce(
                (sum, r) => sum + r.sample_size,
                0
              ),
              totalAnalyses: correlationResults.length,
              avgCorrelation:
                correlationResults.length > 0
                  ? correlationResults.reduce((sum, r) => {
                      const avgCorr =
                        Object.values(r.correlations).reduce(
                          (a, b) => a + Math.abs(b),
                          0
                        ) / Object.keys(r.correlations).length;
                      return sum + avgCorr;
                    }, 0) / correlationResults.length
                  : 0,
              activeWorkers: 4, // Static for now
            };
            setStats(statsData);
          } catch (err) {
            console.error("Error loading stats:", err);
            setStats({
              totalArticles: 0,
              totalAnalyses: 0,
              avgCorrelation: 0,
              activeWorkers: 0,
            });
          }

          if (!notificationShownRef.current) {
            notify.success("Sistema conectado correctamente");
            notificationShownRef.current = true;
          }
        } else {
          if (!notificationShownRef.current) {
            notify.warning("Sistema no disponible");
            notificationShownRef.current = true;
          }
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        if (!notificationShownRef.current) {
          notify.error("Error al conectar con el sistema");
          notificationShownRef.current = true;
        }
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
        <h1>News2Market</h1>
        <p className="subtitle">
          Sistema distribuido para análisis de correlación entre noticias
          económicas y el índice COLCAP
        </p>

        <div className="status-indicator">
          <span
            className={`status-dot ${isHealthy ? "online" : "offline"}`}
          ></span>
          <span className="status-text">
            {isHealthy ? "Sistema operativo" : "Sistema desconectado"}
          </span>
        </div>
      </header>

      <section className="features">
        <h2>Características principales</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </div>
            <h3>Adquisición de datos</h3>
            <p>
              Extracción automática de noticias económicas desde Common Crawl
              con filtros específicos para el mercado colombiano.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <h3>Procesamiento de texto</h3>
            <p>
              Limpieza, extracción de keywords económicas, análisis de
              sentimiento y procesamiento paralelo con múltiples workers.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="20" x2="12" y2="10" />
                <line x1="18" y1="20" x2="18" y2="4" />
                <line x1="6" y1="20" x2="6" y2="16" />
              </svg>
            </div>
            <h3>Análisis de correlación</h3>
            <p>
              Cálculo de correlación de Pearson entre métricas noticiosas y el
              índice COLCAP con análisis temporal.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            </div>
            <h3>Infraestructura escalable</h3>
            <p>
              Despliegue en AWS EKS con Kubernetes, autoescalado horizontal y
              balanceo de carga automático.
            </p>
          </div>
        </div>
      </section>

      {stats && (
        <section className="stats-section">
          <h2>Estadísticas del sistema</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
              <div className="stat-value">{stats.totalArticles || 0}</div>
              <div className="stat-label">Días de datos analizados</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="12" y1="20" x2="12" y2="10" />
                  <line x1="18" y1="20" x2="18" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="16" />
                </svg>
              </div>
              <div className="stat-value">{stats.totalAnalyses || 0}</div>
              <div className="stat-label">Análisis completados</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </div>
              <div className="stat-value">
                {stats.avgCorrelation
                  ? stats.avgCorrelation.toFixed(2)
                  : "0.00"}
              </div>
              <div className="stat-label">Correlación promedio</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="9 11 12 14 22 4" />
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              </div>
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
