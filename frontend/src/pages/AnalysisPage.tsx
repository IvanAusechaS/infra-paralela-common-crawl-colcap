/**
 * AnalysisPage - News2Market
 * 
 * Página para configurar y ejecutar análisis de correlación
 */

import { useState } from 'react';
import { api, type CorrelationRequest, type CorrelationResponse } from '../services/api';
import CorrelationChart from '../components/CorrelationChart';
import { notify } from '../services/api';
import './AnalysisPage.scss';

const AnalysisPage = () => {
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [lagDays, setLagDays] = useState<number>(0);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['volume', 'keywords', 'sentiment']);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<CorrelationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const availableMetrics = [
    { value: 'volume', label: 'Volumen de noticias' },
    { value: 'keywords', label: 'Keywords económicas' },
    { value: 'sentiment', label: 'Sentimiento promedio' },
  ];

  const handleMetricToggle = (metric: string) => {
    setSelectedMetrics(prev =>
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    // Validaciones
    if (!startDate || !endDate) {
      setError('Por favor selecciona ambas fechas');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('La fecha de inicio debe ser anterior a la fecha de fin');
      return;
    }

    if (selectedMetrics.length === 0) {
      setError('Selecciona al menos una métrica');
      return;
    }

    setLoading(true);

    try {
      const request: CorrelationRequest = {
        start_date: startDate,
        end_date: endDate,
        metrics: selectedMetrics,
        lag_days: lagDays,
      };

      const response = await api.calculateCorrelation(request);
      setResult(response);
      notify.success('Análisis completado exitosamente');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al calcular correlación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-page">
      <header className="page-header">
        <h1>Análisis de Correlación</h1>
        <p>Configura los parámetros para analizar la correlación entre noticias y COLCAP</p>
      </header>

      <div className="analysis-container">
        <div className="form-section card">
          <h2>Configuración del análisis</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="start-date">Fecha de inicio</label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="end-date">Fecha de fin</label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="lag-days">Días de lag temporal</label>
              <input
                id="lag-days"
                type="number"
                min="0"
                max="30"
                value={lagDays}
                onChange={(e) => setLagDays(Number(e.target.value))}
                className="input"
              />
              <span className="input-help">
                Retraso entre eventos noticiosos y efecto en COLCAP (0-30 días)
              </span>
            </div>

            <div className="form-group">
              <label>Métricas a analizar</label>
              <div className="checkbox-group">
                {availableMetrics.map(metric => (
                  <label key={metric.value} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={selectedMetrics.includes(metric.value)}
                      onChange={() => handleMetricToggle(metric.value)}
                    />
                    <span>{metric.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {error && <div className="error">{error}</div>}

            <button
              type="submit"
              className="button primary"
              disabled={loading}
            >
              {loading ? 'Analizando...' : 'Calcular correlación'}
            </button>
          </form>
        </div>

        {result && (
          <div className="results-section">
            <div className="card">
              <h2>Resultados del análisis</h2>
              <div className="result-info">
                <p><strong>Job ID:</strong> {result.job_id}</p>
                <p><strong>Tamaño de muestra:</strong> {result.sample_size} días</p>
              </div>
            </div>

            <div className="card">
              <h3>Correlaciones calculadas</h3>
              <CorrelationChart
                correlations={result.correlations}
                pValues={result.p_values}
              />
            </div>

            {result.insights && result.insights.length > 0 && (
              <div className="card">
                <h3>Insights del análisis</h3>
                <ul className="insights-list">
                  {result.insights.map((insight, index) => (
                    <li key={index} className="insight-item">
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPage;
