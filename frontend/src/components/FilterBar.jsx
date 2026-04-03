import React from 'react';

export default function FilterBar({ filters, onFilterChange, collections = [] }) {
  const update = (key, value) => onFilterChange({ ...filters, [key]: value });

  return (
    <div className="flex flex-wrap items-center gap-3 px-8 py-4">
      {/* Search */}
      <input
        type="text"
        placeholder="Search champagnes..."
        value={filters.search}
        onChange={(e) => update('search', e.target.value)}
        className="px-4 py-2 text-sm rounded-lg outline-none transition-colors duration-200"
        style={{
          fontFamily: "'Inter', sans-serif",
          backgroundColor: 'var(--jp-dark)',
          border: '1px solid var(--jp-dark-border)',
          color: 'var(--jp-text-primary)',
          width: '200px',
        }}
        onFocus={(e) => { e.target.style.borderColor = 'var(--jp-gold)'; }}
        onBlur={(e) => { e.target.style.borderColor = 'var(--jp-dark-border)'; }}
      />

      {/* Collection Pills */}
      {(() => {
        const COLLECTION_ORDER = ['Cuvée Royale', 'Parcellaire', 'Joséphine', 'Cuvée 200'];
        const sortedCollections = COLLECTION_ORDER.filter(c => collections.includes(c));
        return ['', ...sortedCollections];
      })().map((col) => {
        const isActive = filters.collection === col;
        const label = col || 'All';
        return (
          <button
            key={col}
            onClick={() => update('collection', col)}
            className="px-3 py-1.5 text-xs uppercase rounded-full transition-colors duration-200"
            style={{
              fontFamily: "'Inter', sans-serif",
              letterSpacing: '0.05em',
              cursor: 'pointer',
              border: isActive ? '1px solid transparent' : '1px solid var(--jp-dark-border)',
              backgroundColor: isActive ? 'var(--jp-gold)' : 'var(--jp-dark)',
              color: isActive ? 'var(--jp-black)' : 'var(--jp-text-muted)',
              fontWeight: isActive ? 600 : 400,
            }}
          >
            {label}
          </button>
        );
      })}

      {/* Spacer to push price slider right */}
      <div className="flex-1" />

      {/* Price Slider */}
      <div className="flex items-center gap-2">
        <label
          className="text-xs uppercase"
          style={{
            fontFamily: "'Inter', sans-serif",
            letterSpacing: '0.05em',
            color: 'var(--jp-text-muted)',
            whiteSpace: 'nowrap',
          }}
        >
          Max Price
        </label>
        <input
          type="range"
          min="0"
          max="500"
          step="10"
          value={filters.max_price || 500}
          onChange={(e) => {
            const val = parseInt(e.target.value);
            update('max_price', val >= 500 ? '' : String(val));
          }}
          className="w-28 accent-amber-500"
        />
        <span
          className="text-sm tabular-nums"
          style={{
            fontFamily: "'Inter', sans-serif",
            color: 'var(--jp-gold)',
            minWidth: '50px',
          }}
        >
          {filters.max_price ? `€${filters.max_price}` : 'Any'}
        </span>
      </div>
    </div>
  );
}
