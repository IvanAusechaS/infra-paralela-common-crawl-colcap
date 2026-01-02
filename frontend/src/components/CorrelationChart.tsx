/**
 * CorrelationChart Component - News2Market
 * 
 * Gráfico de barras para visualizar correlaciones con Recharts
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import './CorrelationChart.scss';

interface CorrelationChartProps {
  correlations: Record<string, number>;
  pValues: Record<string, number>;
}

const CorrelationChart = ({ correlations, pValues }: CorrelationChartProps) => {
  // Preparar datos para el gráfico
  const data = Object.entries(correlations).map(([metric, value]) => ({
    metric,
    correlation: value,
    pValue: pValues[metric] || 1,
  }));

  // Función para determinar el color de la barra
  const getBarColor = (value: number, pValue: number) => {
    // Si no es significativo (p > 0.05), usar gris
    if (pValue > 0.05) return '#9ca3af';
    
    // Color basado en magnitud y dirección
    if (value > 0) {
      return value > 0.5 ? '#10b981' : '#34d399'; // Verde para positivo
    } else {
      return value < -0.5 ? '#ef4444' : '#f87171'; // Rojo para negativo
    }
  };

  // Tooltip personalizado
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="label">{data.metric}</p>
          <p className="correlation">
            <strong>Correlación:</strong> {data.correlation.toFixed(4)}
          </p>
          <p className="p-value">
            <strong>p-value:</strong> {data.pValue.toFixed(4)}
          </p>
          <p className="significance">
            {data.pValue < 0.01
              ? '✅ Altamente significativo'
              : data.pValue < 0.05
              ? '✅ Significativo'
              : '⚠️ No significativo'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="correlation-chart">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="metric"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickFormatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)}
          />
          <YAxis
            domain={[-1, 1]}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ value: 'Correlación de Pearson', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={() => 'Correlación'}
          />
          <Bar dataKey="correlation" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColor(entry.correlation, entry.pValue)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color positive"></span>
          <span>Correlación positiva</span>
        </div>
        <div className="legend-item">
          <span className="legend-color negative"></span>
          <span>Correlación negativa</span>
        </div>
        <div className="legend-item">
          <span className="legend-color not-significant"></span>
          <span>No significativo (p &gt; 0.05)</span>
        </div>
      </div>
    </div>
  );
};

export default CorrelationChart;
