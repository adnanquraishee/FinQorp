import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { MarketOverview } from './pages/MarketOverview';
import { StockAnalysis } from './pages/StockAnalysis';
import { Technical } from './pages/Technical';
import { Forecast } from './pages/Forecast';
import { Compare } from './pages/Compare';
import { Landing } from './pages/Landing';
import './index.css';



function AppContent() {
  const [currentStock, setCurrentStock] = useState<string | null>(null);
  const [stockMetrics, setStockMetrics] = useState<any>({});

  useEffect(() => {
    const handleStockLoaded = (event: any) => {
      setCurrentStock(event.detail.symbol);
      setStockMetrics(event.detail.metrics);
    };
    window.addEventListener('stock-loaded', handleStockLoaded);
    return () => window.removeEventListener('stock-loaded', handleStockLoaded);
  }, []);

  return (
    <div className="flex min-h-screen bg-[var(--obsidian)] text-white">
      <Sidebar currentStock={currentStock} stockMetrics={stockMetrics} />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<MarketOverview />} />
          <Route path="/analysis" element={<StockAnalysis />} />
          <Route path="/technical" element={<Technical />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/compare" element={<Compare />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 3D immersive landing page */}
        <Route path="/" element={<Landing />} />

        {/* Existing dashboard under /app/* */}
        <Route path="/app/*" element={<AppContent />} />
      </Routes>

    </BrowserRouter>
  );
}

export default App;
