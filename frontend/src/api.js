const API_BASE = '/api';

async function fetchJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getStats: () => fetchJSON('/stats'),
  getWinery: () => fetchJSON('/winery'),
  getProducts: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([_, v]) => v != null && v !== ''))
    ).toString();
    return fetchJSON(`/products${qs ? '?' + qs : ''}`);
  },
  getProduct: (id) => fetchJSON(`/products/${id}`),
  getHistory: () => fetchJSON('/history'),
  getTeam: () => fetchJSON('/team'),
  getMedia: (productId) => fetchJSON(`/media${productId ? '?product_id=' + productId : ''}`),
  getArticles: () => fetchJSON('/articles'),
};
