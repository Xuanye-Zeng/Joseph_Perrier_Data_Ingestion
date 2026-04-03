import React from 'react';
import ProductCard from './ProductCard';

export default function ProductGrid({ products, onProductClick }) {
  if (!products || products.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <p
          className="text-sm"
          style={{
            fontFamily: "'Inter', sans-serif",
            color: 'var(--jp-text-muted)',
          }}
        >
          No products found
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onClick={() => onProductClick(product)}
        />
      ))}
    </div>
  );
}
