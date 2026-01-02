/**
 * ResultsPage - News2Market
 *
 * Página para visualizar análisis históricos de correlación
 */

import { useEffect, useState } from "react";
import { api, type CorrelationResponse, notify } from "../services/api";
import jsPDF from "jspdf";
import ConfirmModal from "../components/ConfirmModal";
import "./ResultsPage.scss";

const ResultsPage = () => {
  const [results, setResults] = useState<CorrelationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    jobId: string;
    index: number;
  }>({ isOpen: false, jobId: "", index: 0 });

  useEffect(() => {
    window.scrollTo(0, 0);

    const fetchResults = async () => {
      try {
        const data = await api.getCorrelationResults();
        setResults(data);
      } catch (err: any) {
        setError(err.message || "Error al cargar resultados");
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  const generateCorrelationChart = (
    correlations: Record<string, number>
  ): string => {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 300;
    const ctx = canvas.getContext("2d")!;

    // Background
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const metrics = Object.keys(correlations);
    const values = Object.values(correlations);
    const barWidth = 100;
    const spacing = 180;
    const chartHeight = 200;
    const baseY = 250;

    // Draw grid lines
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = 50 + (chartHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(50, y);
      ctx.lineTo(750, y);
      ctx.stroke();
    }

    // Draw bars
    metrics.forEach((metric, index) => {
      const value = values[index];
      const x = 80 + index * spacing;
      const barHeight = Math.abs(value) * chartHeight;
      const barY = value >= 0 ? baseY - barHeight : baseY;

      // Bar color
      const color = value >= 0 ? "#10b981" : "#dc2626";
      ctx.fillStyle = color;
      ctx.fillRect(x, barY, barWidth, barHeight);

      // Bar border
      ctx.strokeStyle = value >= 0 ? "#047857" : "#b91c1c";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, barY, barWidth, barHeight);

      // Value label
      ctx.fillStyle = "#111827";
      ctx.font = "bold 14px Arial";
      ctx.textAlign = "center";
      ctx.fillText(value.toFixed(3), x + barWidth / 2, barY - 10);

      // Metric label
      ctx.font = "12px Arial";
      ctx.fillText(metric.toUpperCase(), x + barWidth / 2, baseY + 20);
    });

    // Axis labels
    ctx.fillStyle = "#6b7280";
    ctx.font = "10px Arial";
    ctx.textAlign = "right";
    const labels = ["1.0", "0.5", "0.0", "-0.5", "-1.0"];
    labels.forEach((label, i) => {
      ctx.fillText(label, 45, 50 + (chartHeight / 4) * i + 5);
    });

    return canvas.toDataURL("image/png");
  };

  const downloadPDF = async (result: CorrelationResponse, index: number) => {
    try {
      // Obtener información de workers activos
      const workersData = await api.getActiveWorkers();
      
      const doc = new jsPDF();

      // === PAGE 1: HEADER & OVERVIEW ===
      // Header background
      doc.setFillColor(30, 64, 175); // #1e40af
      doc.rect(0, 0, 210, 40, "F");

      // Title
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(24);
      doc.setFont("helvetica", "bold");
      doc.text("News2Market", 105, 15, { align: "center" });

      doc.setFontSize(16);
      doc.text("Análisis de Correlación", 105, 27, { align: "center" });

      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.text(
        `Generado: ${new Date().toLocaleDateString(
          "es-ES"
        )} ${new Date().toLocaleTimeString("es-ES")}`,
        105,
        35,
        { align: "center" }
      );

      // Analysis info box
      doc.setFillColor(249, 250, 251); // #f9fafb
      doc.rect(15, 50, 180, 42, "F");
      doc.setDrawColor(229, 231, 235);
      doc.rect(15, 50, 180, 42, "S");

      doc.setTextColor(30, 64, 175);
      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.text(`Análisis #${index + 1}`, 20, 60);

      doc.setTextColor(17, 24, 39);
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.text(`Job ID: ${result.job_id}`, 20, 70);
      doc.text(`Tamaño de muestra: ${result.sample_size} días`, 20, 77);
      doc.text(`Workers activos: ${workersData.active_workers}`, 20, 84);

      // === CORRELATION CHART ===
      doc.setTextColor(30, 64, 175);
      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.text("Gráfico de Correlaciones", 20, 100);

      const chartImage = generateCorrelationChart(result.correlations);
      doc.addImage(chartImage, "PNG", 15, 105, 180, 90);

      // === CORRELATION VALUES TABLE ===
      let yPos = 205;
      doc.setTextColor(30, 64, 175);
      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.text("Valores de Correlación", 20, yPos);

      yPos += 8;
      doc.setFillColor(30, 64, 175);
      doc.rect(15, yPos, 180, 8, "F");

      doc.setTextColor(255, 255, 255);
      doc.setFontSize(10);
      doc.setFont("helvetica", "bold");
      doc.text("Métrica", 20, yPos + 6);
      doc.text("Correlación", 100, yPos + 6);
      doc.text("P-value", 150, yPos + 6);

      yPos += 10;
      doc.setTextColor(17, 24, 39);
      doc.setFont("helvetica", "normal");

      Object.entries(result.correlations).forEach(([metric, value]) => {
        // Alternate row colors
        if (Object.keys(result.correlations).indexOf(metric) % 2 === 0) {
          doc.setFillColor(249, 250, 251);
          doc.rect(15, yPos - 4, 180, 8, "F");
        }

        doc.text(metric.toUpperCase(), 20, yPos);

        // Color code correlation value
        const corr = value.toFixed(3);
        if (value >= 0.5) {
          doc.setTextColor(16, 185, 129); // green
        } else if (value <= -0.5) {
          doc.setTextColor(220, 38, 38); // red
        } else {
          doc.setTextColor(107, 114, 128); // gray
        }
        doc.setFont("helvetica", "bold");
        doc.text(corr, 100, yPos);

        doc.setTextColor(17, 24, 39);
        doc.setFont("helvetica", "normal");
        const pValue = result.p_values[metric];
        const pValueStr = pValue < 0.001 ? "< 0.001" : pValue.toFixed(4);
        doc.text(pValueStr, 150, yPos);

        yPos += 8;
      });

      // === PAGE 2: INSIGHTS ===
      if (result.insights && result.insights.length > 0) {
        doc.addPage();

        // Header
        doc.setFillColor(30, 64, 175);
        doc.rect(0, 0, 210, 30, "F");
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(18);
        doc.setFont("helvetica", "bold");
        doc.text("Insights del Análisis", 105, 20, { align: "center" });

        yPos = 45;
        doc.setTextColor(17, 24, 39);
        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");

        result.insights.forEach((insight, idx) => {
          if (yPos > 270) {
            doc.addPage();
            yPos = 20;
          }

          // Clean text: remove emojis and problematic characters
          const cleanInsight = insight
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, "") // Remove emojis
            .replace(/[^\x00-\x7F\u00C0-\u017F]/g, "") // Keep only ASCII + Latin-1
            .replace(/\s+/g, " ") // Normalize whitespace
            .trim();

          // Insight box
          const lines = doc.splitTextToSize(cleanInsight, 160);
          const boxHeight = lines.length * 5 + 10;

          doc.setFillColor(249, 250, 251);
          doc.rect(15, yPos - 5, 180, boxHeight, "F");
          doc.setDrawColor(229, 231, 235);
          doc.rect(15, yPos - 5, 180, boxHeight, "S");

          // Insight number
          doc.setFillColor(30, 64, 175);
          doc.circle(25, yPos + 2, 4, "F");
          doc.setTextColor(255, 255, 255);
          doc.setFont("helvetica", "bold");
          doc.setFontSize(8);
          doc.text((idx + 1).toString(), 25, yPos + 3, { align: "center" });

          // Insight text
          doc.setTextColor(17, 24, 39);
          doc.setFontSize(10);
          doc.setFont("helvetica", "normal");
          doc.text(lines, 35, yPos);

          yPos += boxHeight + 5;
        });
      }

      // Footer on all pages
      const pageCount = doc.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFillColor(249, 250, 251);
        doc.rect(0, 287, 210, 10, "F");
        doc.setTextColor(107, 114, 128);
        doc.setFontSize(8);
        doc.text(`Página ${i} de ${pageCount}`, 105, 293, { align: "center" });
        doc.text("News2Market © 2025", 20, 293);
      }

      doc.save(`News2Market_Analisis_${result.job_id.slice(5, 13)}.pdf`);
      notify.success("PDF descargado exitosamente");
    } catch (error) {
      console.error("Error generating PDF:", error);
      notify.error("Error al generar el PDF");
    }
  };

  const deleteResult = async (jobId: string, index: number) => {
    setConfirmModal({ isOpen: true, jobId, index });
  };

  const handleConfirmDelete = async () => {
    const { jobId } = confirmModal;
    setConfirmModal({ isOpen: false, jobId: "", index: 0 });

    try {
      await api.deleteCorrelationResult(jobId);
      setResults(results.filter((r) => r.job_id !== jobId));
      notify.success("Análisis eliminado exitosamente");
    } catch (error) {
      console.error("Error deleting result:", error);
      notify.error("Error al eliminar el análisis");
    }
  };

  const handleCancelDelete = () => {
    setConfirmModal({ isOpen: false, jobId: "", index: 0 });
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
          <span className="empty-icon">-</span>
          <h3>No hay resultados disponibles</h3>
          <p>
            Realiza tu primer análisis de correlación para ver resultados aquí
          </p>
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
                  <button
                    className="button danger small"
                    onClick={() => deleteResult(result.job_id, index)}
                    title="Eliminar análisis"
                  >
                    Eliminar
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
                        className={`bar-fill ${
                          value > 0 ? "positive" : "negative"
                        }`}
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

      <ConfirmModal
        isOpen={confirmModal.isOpen}
        title="Confirmar eliminación"
        message={`¿Estás seguro de eliminar el Análisis #${confirmModal.index + 1}? Esta acción no se puede deshacer.`}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        confirmText="Eliminar"
        cancelText="Cancelar"
      />
    </div>
  );
};

export default ResultsPage;
