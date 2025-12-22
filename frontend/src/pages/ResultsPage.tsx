/**
 * ResultsPage - News2Market
 * 
 * Página para visualizar análisis históricos de correlación
 */

import { useEffect, useState } from 'react';
import { api, type CorrelationResponse } from '../services/api';
import jsPDF from 'jspdf';
import './ResultsPage.scss';

const ResultsPage = () => {
  const [results, setResults] = useState<CorrelationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const data = await api.getCorrelationResults();
        setResults(data);
      } catch (err: any) {
        setError(err.message || 'Error al cargar resultados');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  const downloadPDF = (result: CorrelationResponse, index: number) => {
    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(20);
    doc.text('News2Market - Análisis de Correlación', 20, 20);
    
    // Analysis info
    doc.setFontSize(12);
    doc.text(`Análisis #${index + 1}`, 20, 35);
    doc.text(`Job ID: ${result.job_id}`, 20, 45);
    doc.text(`Tamaño de muestra: ${result.sample_size} días`, 20, 55);
    
    // Correlations
    doc.setFontSize(14);
    doc.text('Correlaciones:', 20, 70);
    doc.setFontSize(11);
    
    let yPos = 80;
    Object.entries(result.correlations).forEach(([metric, value]) => {
      doc.text(`${metric}: ${value.toFixed(3)}`, 30, yPos);
      yPos += 10;
    });
    
    // P-values
    if (result.p_values && Object.keys(result.p_values).length > 0) {
      doc.setFontSize(14);
      doc.text('P-values:', 20, yPos + 10);
      doc.setFontSize(11);
      yPos += 20;
      
      Object.entries(result.p_values).forEach(([metric, value]) => {
        doc.text(`${metric}: ${value.toFixed(4)}`, 30, yPos);
        yPos += 10;
      });
    }
    
    // Insights
    if (result.insights && result.insights.length > 0) {
      doc.setFontSize(14);
      doc.text('Insights:', 20, yPos + 10);
      doc.setFontSize(10);
      yPos += 20;
      
      result.insights.forEach((insight, idx) => {
        const lines = doc.splitTextToSize(`${idx + 1}. ${insight}`, 170);
        doc.text(lines, 30, yPos);
        yPos += lines.length * 7;
        
        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }
      });
    }
    
    doc.save(`analisis-correlacion-${result.job_id.slice(0, 8)}.pdf`);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="results-page">
      <header className="page-header">
        <h1>Resultados históricos</h1>
        <p>Análisis de correlación realizados anteriormente</p>
      </header>

      {results.length === 0 ? (
        <div className="empty-state card">
          <span className="empty-icon">—</span>
          <h3>No hay resultados disponibles</h3>
          <p>Realiza tu primer análisis de correlación para ver resultados aquí</p>
        </div>
      ) : (
        <div className="results-grid">
          {results.map((result, index) => (
            <div key={index} className="result-card card">
              <div className="result-header">
                <h3>Análisis #{index + 1}</h3>
                <div className="header-actions">
                  <span className="job-id">{result.job_id.slice(0, 8)}</span>
                  <button 
                    className="button secondary small"
                    onClick={() => downloadPDF(result, index)}
                    title="Descargar PDF"
                  >
                    Descargar PDF
                  </button>
                </div>
              </div>

              <div className="result-meta">
                <div className="meta-item">
                  <span className="meta-label">Muestra:</span>
                  <span className="meta-value">{result.sample_size} días</span>
                </div>
              </div>

              <div className="correlations">
                <h4>Correlaciones</h4>
                {Object.entries(result.correlations).map(([metric, value]) => (
                  <div key={metric} className="correlation-item">
                    <span className="metric-name">{metric}</span>
                    <div className="correlation-bar">
                      <div
                        className={`bar-fill ${value > 0 ? 'positive' : 'negative'}`}
                        style={{ width: `${Math.abs(value) * 100}%` }}
                      ></div>
                    </div>
                    <span className="correlation-value">
                      {value.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>

              {result.insights && result.insights.length > 0 && (
                <div className="insights-preview">
                  <h4>Insights principales</h4>
                  <ul>
                    {result.insights.slice(0, 2).map((insight, idx) => (
                      <li key={idx}>{insight}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ResultsPage;
