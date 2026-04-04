import React from 'react';

export default function StatsBar({ stats }) {
  if (!stats || Object.keys(stats).length === 0) return null;

  const videoCount = stats.media_types?.video || 0;
  const imageCount = (stats.media || 0) - videoCount;
  const items = [
    { value: stats.product, label: 'champagnes' },
    { value: imageCount, label: 'images' },
    { value: videoCount, label: 'videos' },
    { value: stats.winery_history, label: 'history events' },
    { value: stats.article, label: 'articles' },
  ].filter(item => item.value != null && item.value > 0);

  return (
    <p
      className="text-center mb-6"
      style={{
        fontFamily: "'Inter', sans-serif",
        fontSize: '12px',
        color: 'var(--jp-text-muted)',
        letterSpacing: '1px',
      }}
    >
      {items.map((item, i) => (
        <span key={i}>
          {i > 0 && <span style={{ margin: '0 8px', opacity: 0.5 }}>·</span>}
          <span style={{ color: 'var(--jp-gold)' }}>{item.value}</span> {item.label}
        </span>
      ))}
    </p>
  );
}
