import React, { useState } from 'react';

const CATEGORY_COLORS = {
  awards: 'var(--jp-gold)',
  events: 'var(--jp-steel)',
  news: 'var(--jp-green)',
  editorial: 'var(--jp-text-muted)',
};

function getCategoryColor(category) {
  if (!category) return 'var(--jp-text-muted)';
  const key = category.toLowerCase();
  return CATEGORY_COLORS[key] || 'var(--jp-text-secondary)';
}

const EXCLUDED_TITLES = ['customizedevents', 'where to find us', 'le pavillon 1825', 'terms and conditions'];

export default function ArticlesView({ articles }) {
  const validArticles = (articles || []).filter(a =>
    a.title &&
    a.title.length > 15 &&
    !EXCLUDED_TITLES.includes(a.title.toLowerCase().trim())
  );

  const [visibleCount, setVisibleCount] = useState(12);
  const visibleArticles = validArticles.slice(0, visibleCount);

  if (validArticles.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-sm" style={{ color: 'var(--jp-text-muted)' }}>
          No articles available
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-6xl mx-auto py-6">
      {visibleArticles.map((article, index) => (
        <div
          key={article.id || article.title + '-' + index}
          className="rounded-lg overflow-hidden"
          style={{
            backgroundColor: 'var(--jp-dark)',
            border: '0.5px solid var(--jp-dark-border)',
          }}
        >
          {/* Image */}
          {article.image_url && (
            <img
              src={article.image_url}
              alt={article.title}
              style={{ width: '100%', height: '160px', objectFit: 'cover', display: 'block' }}
            />
          )}

          {/* Content */}
          <div className="p-4">
            {/* Category Badge */}
            {article.category && (
              <span
                className="text-[10px] uppercase tracking-wider font-semibold"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: getCategoryColor(article.category),
                  letterSpacing: '0.1em',
                }}
              >
                {article.category}
              </span>
            )}

            {/* Title */}
            <h3
              className="text-base font-medium mt-2"
              style={{
                fontFamily: "'Playfair Display', serif",
                color: 'var(--jp-text-primary)',
              }}
            >
              {article.title}
            </h3>

            {/* Summary */}
            {article.summary && (
              <p
                className="text-xs mt-2 line-clamp-3"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: 'var(--jp-text-muted)',
                }}
              >
                {article.summary}
              </p>
            )}

            {/* Author + Date */}
            {(article.author || article.published_date) && (
              <p
                className="text-[10px] mt-2"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: 'var(--jp-text-muted)',
                }}
              >
                {article.author}
                {article.author && article.published_date && ' \u00B7 '}
                {article.published_date}
              </p>
            )}

            {/* Source Link */}
            {article.source_url && (
              <a
                href={article.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs mt-3 inline-block"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: 'var(--jp-gold)',
                  textDecoration: 'none',
                }}
              >
                Read more &rarr;
              </a>
            )}
          </div>
        </div>
      ))}

      {visibleCount < validArticles.length && (
        <div className="col-span-full flex justify-center mt-6">
          <button
            onClick={() => setVisibleCount(prev => prev + 9)}
            className="px-6 py-2 text-sm rounded-full transition-colors duration-200"
            style={{
              fontFamily: "'Inter', sans-serif",
              border: '1px solid var(--jp-dark-border)',
              backgroundColor: 'var(--jp-dark)',
              color: 'var(--jp-text-muted)',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--jp-gold)'; e.currentTarget.style.color = 'var(--jp-gold)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--jp-dark-border)'; e.currentTarget.style.color = 'var(--jp-text-muted)'; }}
          >
            Load more ({validArticles.length - visibleCount} remaining)
          </button>
        </div>
      )}
    </div>
  );
}
