import React from 'react';

const TABS = ['products', 'winery', 'history', 'family', 'articles'];

export default function Header({ activeTab, onTabChange }) {
  return (
    <header
      className="sticky top-0 z-50 flex justify-between items-center px-8 py-4"
      style={{
        backgroundColor: 'var(--jp-black)',
        borderBottom: '0.5px solid var(--jp-dark-border)',
      }}
    >
      {/* Left — Branding */}
      <div className="flex flex-col">
        <h1
          className="text-2xl font-bold leading-tight"
          style={{
            fontFamily: "'Playfair Display', serif",
            color: 'var(--jp-gold)',
          }}
        >
          JOSEPH PERRIER
        </h1>
        <span
          className="text-xs uppercase"
          style={{
            fontFamily: "'Inter', sans-serif",
            letterSpacing: '2px',
            color: 'var(--jp-text-muted)',
          }}
        >
          Data Explorer
        </span>
      </div>

      {/* Right — Tab Navigation */}
      <nav className="flex items-center gap-1">
        {TABS.map((tab) => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => onTabChange(tab)}
              className="px-4 py-2 text-sm uppercase transition-colors duration-200"
              style={{
                fontFamily: "'Inter', sans-serif",
                letterSpacing: '1px',
                background: 'transparent',
                border: 'none',
                borderBottom: isActive
                  ? '2px solid var(--jp-gold)'
                  : '2px solid transparent',
                color: isActive
                  ? 'var(--jp-gold)'
                  : 'var(--jp-text-muted)',
                cursor: 'pointer',
              }}
            >
              {tab}
            </button>
          );
        })}
      </nav>
    </header>
  );
}
