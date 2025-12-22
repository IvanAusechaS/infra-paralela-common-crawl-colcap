/**
 * API Client - News2Market Frontend
 * 
 * Cliente HTTP para comunicación con API Gateway
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_GATEWAY = import.meta.env.VITE_API_GATEWAY || '/api/v1';

// Crear instancia de axios
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_GATEWAY}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de respuestas para manejo de errores
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error('❌ API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('❌ Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ========================
// Tipos de datos
// ========================

export interface Article {
  id: number;
  url: string;
  title: string;
  content: string;
  crawled_at: string;
  status: string;
}

export interface ProcessedArticle {
  id: number;
  article_id: number;
  cleaned_content: string;
  word_count: number;
  economic_keywords: Record<string, number>;
  sentiment_score: number;
  entities: string[];
  processed_at: string;
}

export interface CorrelationRequest {
  start_date: string;
  end_date: string;
  metrics: string[];
  lag_days?: number;
}

export interface CorrelationResponse {
  job_id: string;
  correlations: Record<string, number>;
  p_values: Record<string, number>;
  insights: string[];
  sample_size: number;
}

export interface ColcapData {
  date: string;
  opening_price: number;
  closing_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  daily_change_percent: number;
}

// ========================
// Funciones de API
// ========================

export const api = {
  /**
   * Obtener artículos procesados
   */
  async getProcessedArticles(limit: number = 50): Promise<ProcessedArticle[]> {
    const response = await apiClient.get('/text-processor/articles', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Obtener estadísticas de procesamiento
   */
  async getProcessingStats(): Promise<any> {
    const response = await apiClient.get('/text-processor/stats');
    return response.data;
  },

  /**
   * Calcular correlación
   */
  async calculateCorrelation(request: CorrelationRequest): Promise<CorrelationResponse> {
    const response = await apiClient.post('/correlation/correlate', request);
    return response.data;
  },

  /**
   * Obtener datos históricos de COLCAP
   */
  async getColcapData(startDate: string, endDate: string): Promise<ColcapData[]> {
    const response = await apiClient.get(`/correlation/colcap/${startDate}/${endDate}`);
    return response.data;
  },

  /**
   * Listar resultados de correlación
   */
  async getCorrelationResults(limit: number = 20): Promise<CorrelationResponse[]> {
    const response = await apiClient.get('/correlation/results', {
      params: { limit },
    });
    return response.data.results || [];
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      await apiClient.get('/health');
      return true;
    } catch {
      return false;
    }
  },
};

export default apiClient;
