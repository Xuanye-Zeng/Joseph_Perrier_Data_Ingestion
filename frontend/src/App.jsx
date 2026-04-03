import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import Header from './components/Header';
import StatsBar from './components/StatsBar';
import FilterBar from './components/FilterBar';
import ProductGrid from './components/ProductGrid';
import WineryView from './components/WineryView';
import HistoryTimeline from './components/HistoryTimeline';
import TeamGrid from './components/TeamGrid';
import ArticlesView from './components/ArticlesView';

// Lazy-import ProductDetail if it exists; gracefully handle absence
let ProductDetail = null;
try {
  ProductDetail = React.lazy(() => import('./components/ProductDetail'));
} catch {
  // ProductDetail component not yet created
}

const DEFAULT_FILTERS = {
  search: '',
  collection: '',
  type: '',
  max_price: '',
};

export default function App() {
  const [activeTab, setActiveTab] = useState('products');
  const [stats, setStats] = useState({});
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productDetail, setProductDetail] = useState(null);
  const [winery, setWinery] = useState(null);
  const [history, setHistory] = useState(null);
  const [team, setTeam] = useState(null);
  const [articles, setArticles] = useState(null);
  const [wineryMedia, setWineryMedia] = useState(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  // Fetch stats on mount
  useEffect(() => {
    api.getStats().then(setStats).catch(console.error);
  }, []);

  // Fetch products on mount and when filters change
  useEffect(() => {
    const params = {};
    if (filters.search) params.search = filters.search;
    if (filters.collection) params.collection = filters.collection;
    if (filters.type) params.type = filters.type;
    if (filters.max_price) params.max_price = filters.max_price;

    api.getProducts(params).then(setProducts).catch(console.error);
  }, [filters]);

  // Fetch tab-specific data when tab changes
  useEffect(() => {
    if (activeTab === 'winery' && !winery) {
      api.getWinery().then(data => { if (data && data.name) setWinery(data); }).catch(console.error);
      api.getMedia().then(data => { if (Array.isArray(data)) setWineryMedia(data); }).catch(console.error);
    }
    if (activeTab === 'history' && history === null) {
      api.getHistory().then(setHistory).catch(console.error);
    }
    if (activeTab === 'family' && team === null) {
      api.getTeam().then(setTeam).catch(console.error);
    }
    if (activeTab === 'articles' && articles === null) {
      api.getArticles().then(setArticles).catch(console.error);
    }
  }, [activeTab, winery, history, team, articles]);

  const handleProductClick = useCallback(async (product) => {
    setSelectedProduct(product);
    try {
      const detail = await api.getProduct(product.id);
      setProductDetail(detail);
      setSelectedProduct(detail);
    } catch (err) {
      console.error('Failed to fetch product detail:', err);
    }
  }, []);

  // Extract collections from stats (stable, not affected by filters)
  const collections = stats.collections ? Object.keys(stats.collections) : [];

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--jp-black)' }}>
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="max-w-7xl mx-auto px-6 py-6">
        <StatsBar stats={stats} />

        {activeTab === 'products' && (
          <>
            <FilterBar
              filters={filters}
              onFilterChange={setFilters}
              collections={collections}
            />
            <ProductGrid
              products={products}
              onProductClick={handleProductClick}
            />
          </>
        )}

        {activeTab === 'winery' && (
          <WineryView winery={winery} media={wineryMedia} />
        )}

        {activeTab === 'history' && (
          <HistoryTimeline events={history} />
        )}

        {activeTab === 'family' && (
          <TeamGrid members={team} />
        )}

        {activeTab === 'articles' && (
          <ArticlesView articles={articles} />
        )}
      </main>

      {/* Product Detail Modal */}
      {selectedProduct && ProductDetail && (
        <React.Suspense fallback={null}>
          <ProductDetail
            product={selectedProduct}
            onClose={() => {
              setSelectedProduct(null);
              setProductDetail(null);
            }}
          />
        </React.Suspense>
      )}
    </div>
  );
}
