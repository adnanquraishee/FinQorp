export interface TickerOption {
    ticker: string;
    name: string;
    exchange: string;
}

export interface StockMetrics {
    [key: string]: string;
}

export interface CompanyProfile {
    longName?: string;
    sector?: string;
    industry?: string;
    website?: string;
    employees?: string | number;
    summary?: string;
}

export interface StockData {
    symbol: string;
    metrics: StockMetrics;
    profile: CompanyProfile;
    charts: Record<string, string>;
}

export interface ChartDataPoint {
    Date: string;
    Open: number;
    High: number;
    Low: number;
    Close: number;
    Volume: number;
    MA50?: number;
    MA200?: number;
}

export interface TechnicalDataPoint extends ChartDataPoint {
    RSI_14?: number;
    MACD_12_26_9?: number;
    MACDs_12_26_9?: number;
    MACDh_12_26_9?: number;
    BBL_20_2_0?: number;
    BBM_20_2_0?: number;
    BBU_20_2_0?: number;
}

export interface AccuracyMetrics {
    rmse: number;
    mae: number;
    mape: number;
    directional_accuracy: number;
}

export interface AccuracyResults {
    metrics: AccuracyMetrics;
    accuracy_score: number;
    forecast_prices: number[];
    actual_prices: number[];
    dates: string[];
    error?: string;
}

export interface ForecastData {
    symbol: string;
    recommendation: string;
    sentiment_score: number;
    charts: {
        sentiment: string | null;
        forecast: string | null;
        recommendation: string | null;
    };
    accuracy: AccuracyResults;
}

export interface MarketIndex {
    symbol: string;
    name: string;
    price: number | null;
    change: number | null;
}

export interface ComparisonData {
    symbols: string[];
    summary: string;
    data: Array<Record<string, any>>;
    chart: string;
}

export interface SearchResponse {
    results: TickerOption[];
}

export interface ChartResponse {
    symbol: string;
    period: string;
    interval: string;
    data: ChartDataPoint[];
}

export interface TechnicalResponse {
    symbol: string;
    data: TechnicalDataPoint[];
}

export interface InsightsResponse {
    symbol: string;
    summary: string;
}

export interface SentimentResponse {
    symbol: string;
    score: number;
    chart: string;
}

export interface MarketIndicesResponse {
    indices: MarketIndex[];
}
