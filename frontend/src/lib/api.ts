import axios from 'axios';
import type {
    SearchResponse,
    StockData,
    ChartResponse,
    TechnicalResponse,
    ForecastData,
    InsightsResponse,
    SentimentResponse,
    MarketIndicesResponse,
    ComparisonData,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 120000, // 120 seconds for forecast endpoints
});

// Request interceptor for logging
apiClient.interceptors.request.use(
    (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response) {
            console.error('API Error:', error.response.status, error.response.data);
        } else if (error.request) {
            console.error('Network Error:', error.message);
        } else {
            console.error('Error:', error.message);
        }
        return Promise.reject(error);
    }
);

export const api = {
    // Search for stocks
    searchStocks: async (query: string): Promise<SearchResponse> => {
        const response = await apiClient.get<SearchResponse>('/api/search', {
            params: { query },
        });
        return response.data;
    },

    // Get stock data with fundamentals
    getStock: async (symbol: string): Promise<StockData> => {
        const response = await apiClient.get<StockData>(`/api/stock/${symbol}`);
        return response.data;
    },

    // Get chart data
    getChart: async (
        symbol: string,
        period: string = '2y',
        interval: string = '1d'
    ): Promise<ChartResponse> => {
        const response = await apiClient.get<ChartResponse>(
            `/api/stock/${symbol}/chart`,
            {
                params: { period, interval },
            }
        );
        return response.data;
    },

    // Get technical indicators
    getTechnicals: async (symbol: string): Promise<TechnicalResponse> => {
        const response = await apiClient.get<TechnicalResponse>(
            `/api/stock/${symbol}/technicals`
        );
        return response.data;
    },

    // Get forecast and recommendation
    getForecast: async (symbol: string): Promise<ForecastData> => {
        const response = await apiClient.get<ForecastData>(
            `/api/stock/${symbol}/forecast`
        );
        return response.data;
    },

    // Get AI insights
    getInsights: async (symbol: string): Promise<InsightsResponse> => {
        const response = await apiClient.get<InsightsResponse>(
            `/api/stock/${symbol}/insights`
        );
        return response.data;
    },

    // Get sentiment analysis
    getSentiment: async (symbol: string): Promise<SentimentResponse> => {
        const response = await apiClient.get<SentimentResponse>(
            `/api/stock/${symbol}/sentiment`
        );
        return response.data;
    },

    // Get market indices
    getMarketIndices: async (): Promise<MarketIndicesResponse> => {
        const response = await apiClient.get<MarketIndicesResponse>(
            '/api/market/indices'
        );
        return response.data;
    },

    // Compare stocks
    compareStocks: async (symbols: string[]): Promise<ComparisonData> => {
        const response = await apiClient.post<ComparisonData>('/api/compare', {
            symbols,
        });
        return response.data;
    },
};

export default api;
