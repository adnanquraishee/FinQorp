from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import traceback
import logging

# Import existing modules
from modules import (
    data_fetch, 
    sentiment, 
    forecast, 
    fundamentals, 
    insights, 
    compare, 
    recommendation, 
    ticker_resolver, 
    technicals,
    accuracy
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FinQorp API", version="1.0.0")

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
        "https://*.vercel.app",   # Vercel deployments
        "https://*.netlify.app"   # Netlify deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class TickerOption(BaseModel):
    ticker: str
    name: str
    exchange: str

class CompareRequest(BaseModel):
    symbols: List[str]

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "FinQorp API is running",
        "version": "1.0.0"
    }

@app.get("/api/search")
async def search_stocks(query: str = Query(..., min_length=1)):
    """
    Search for stocks by company name or ticker symbol
    Returns list of matching ticker options
    """
    try:
        options = ticker_resolver.find_ticker_options(query)
        if not options:
            return {"results": []}
        
        return {
            "results": [
                {
                    "ticker": opt["ticker"],
                    "name": opt["name"],
                    "exchange": opt["exchange"]
                }
                for opt in options
            ]
        }
    except Exception as e:
        logger.error(f"Search error for '{query}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}")
async def get_stock_data(symbol: str):
    """
    Get comprehensive stock data including fundamentals, metrics, and profile
    """
    try:
        metrics, figs, profile_info = fundamentals.get_fundamentals(symbol)
        
        if "Error" in metrics:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
        
        # Convert matplotlib figures to base64 (for charts)
        import io
        import base64
        
        chart_data = {}
        for key, fig in figs.items():
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            chart_data[key] = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
        
        return {
            "symbol": symbol,
            "metrics": metrics,
            "profile": profile_info,
            "charts": chart_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock data error for '{symbol}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/chart")
async def get_stock_chart(
    symbol: str, 
    period: str = Query("2y", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: str = Query("1d", regex="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$")
):
    """
    Get historical price data for charting
    """
    try:
        df = data_fetch.get_stock_data(symbol, period=period, interval=interval)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No chart data found for {symbol}")
        
        # Calculate moving averages
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean()
        
        # Convert to dict for JSON response
        data = df.reset_index().to_dict('records')
        
        # Convert Timestamp to string and NaN to None for JSON compatibility
        import math
        for record in data:
            if 'Date' in record:
                date_val = record['Date']
                if hasattr(date_val, 'isoformat'):
                    record['Date'] = date_val.isoformat()
                elif not isinstance(date_val, str):
                    record['Date'] = str(date_val)
            
            # Replace NaN with None for JSON serialization
            for key, value in list(record.items()):
                if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    record[key] = None
        
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart data error for '{symbol}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/technicals")
async def get_technicals(symbol: str):
    """
    Get technical indicators (RSI, MACD, Bollinger Bands)
    """
    try:
        df = data_fetch.get_stock_data(symbol, period="1y", interval="1d")
        
        if df.empty or 'Close' not in df.columns:
            raise HTTPException(status_code=404, detail=f"No data for technical analysis: {symbol}")
        
        # Calculate indicators
        technicals.calculate_bbands(df)
        technicals.calculate_rsi(df)
        technicals.calculate_macd(df)
        df = df.dropna()
        
        # Convert to dict
        data = df.reset_index().to_dict('records')
        
        # Convert Timestamp to string and NaN to None for JSON compatibility
        import math
        for record in data:
            if 'Date' in record:
                date_val = record['Date']
                if hasattr(date_val, 'isoformat'):
                    record['Date'] = date_val.isoformat()
                elif not isinstance(date_val, str):
                    record['Date'] = str(date_val)
            
            # Replace NaN with None for JSON serialization
            for key, value in list(record.items()):
                if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                    record[key] = None
        
        return {
            "symbol": symbol,
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Technical analysis error for '{symbol}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/forecast")
async def get_forecast(symbol: str):
    """
    Get price forecast, recommendation, sentiment, and accuracy metrics
    """
    try:
        # 1. Sentiment analysis
        _, sentiment_fig, sentiment_score = sentiment.analyze_sentiment(symbol)
        
        # 2. Generate 30-day forecast for recommendation
        hist_df_30d, simulations_30d, _ = forecast.generate_forecast(symbol, period=30, num_simulations=100)
        
        # 3. Generate recommendation
        rec_text, rec_fig = recommendation.get_recommendation(symbol, hist_df_30d, simulations_30d, sentiment_score)
        
        # 4. Generate 90-day forecast for visualization
        hist_df_90d, simulations_90d, future_dates_90d = forecast.generate_forecast(symbol, period=90, num_simulations=100)
        forecast_fig = forecast.plot_forecast(hist_df_90d, simulations_90d, future_dates_90d, sentiment_score)
        
        # 5. Run accuracy backtest
        accuracy_results = accuracy.run_backtest(symbol, forecast_days=30, num_simulations=100)
        
        # Convert figures to base64
        import io
        import base64
        
        def fig_to_base64(fig):
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#0a0e17')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            return img_base64
        
        sentiment_chart = fig_to_base64(sentiment_fig) if sentiment_fig else None
        forecast_chart = fig_to_base64(forecast_fig) if forecast_fig else None
        
        # Handle recommendation figure (Plotly)
        rec_chart = None
        if rec_fig:
            rec_chart = rec_fig.to_json()
        
        return {
            "symbol": symbol,
            "recommendation": rec_text,
            "sentiment_score": sentiment_score,
            "charts": {
                "sentiment": sentiment_chart,
                "forecast": forecast_chart,
                "recommendation": rec_chart
            },
            "accuracy": accuracy_results
        }
    except Exception as e:
        logger.error(f"Forecast error for '{symbol}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/sentiment")
async def get_sentiment(symbol: str):
    """
    Get sentiment analysis for a stock
    """
    try:
        _, sentiment_fig, sentiment_score = sentiment.analyze_sentiment(symbol)
        
        # Convert figure to base64
        import io
        import base64
        
        buf = io.BytesIO()
        sentiment_fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#0a0e17')
        buf.seek(0)
        chart = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        
        return {
            "symbol": symbol,
            "score": sentiment_score,
            "chart": chart
        }
    except Exception as e:
        logger.error(f"Sentiment error for '{symbol}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/insights")
async def get_insights(symbol: str):
    """
    Get AI-generated insights for a stock
    """
    try:
        summary = insights.generate_ai_summary(symbol)
        return {
            "symbol": symbol,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Insights error for '{symbol}': {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/indices")
async def get_market_indices():
    """
    Get market overview with major indices
    """
    try:
        indices = ['^NSEI', '^BSESN', '^GSPC', '^IXIC', 'GC=F', 'CL=F', 'INR=X', 'EURUSD=X']
        index_data = data_fetch.get_market_data(indices)
        
        index_names = {
            '^NSEI': 'NIFTY 50',
            '^BSESN': 'SENSEX',
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            'GC=F': 'Gold',
            'CL=F': 'Crude Oil',
            'INR=X': 'USD/INR',
            'EURUSD=X': 'EUR/USD'
        }
        
        result = []
        for ticker, name in index_names.items():
            data = index_data.get(ticker)
            if data:
                result.append({
                    "symbol": ticker,
                    "name": name,
                    "price": data['price'],
                    "change": data['change']
                })
            else:
                result.append({
                    "symbol": ticker,
                    "name": name,
                    "price": None,
                    "change": None
                })
        
        return {"indices": result}
    except Exception as e:
        logger.error(f"Market indices error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare")
async def compare_stocks(request: CompareRequest):
    """
    Compare multiple stocks
    """
    try:
        if len(request.symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required for comparison")
        
        if len(request.symbols) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 symbols allowed")
        
        summary, df, fig = compare.compare_companies(request.symbols)
        
        # Convert dataframe to dict
        comparison_data = df.to_dict('records')
        
        # Convert figure to base64
        import io
        import base64
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#0a0e17')
        buf.seek(0)
        chart = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        
        return {
            "symbols": request.symbols,
            "summary": summary,
            "data": comparison_data,
            "chart": chart
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
