import React from 'react';

function InfoCard({ label, children, colSpan }) {
  return (
    <div
      className={`rounded-lg p-5 ${colSpan ? 'md:col-span-2' : ''}`}
      style={{
        backgroundColor: 'var(--jp-dark)',
        border: '0.5px solid var(--jp-dark-border)',
      }}
    >
      <p
        className="text-[10px] uppercase tracking-wider mb-2"
        style={{ fontFamily: "'Inter', sans-serif", color: 'var(--jp-gold)', letterSpacing: '0.1em' }}
      >
        {label}
      </p>
      <div
        className="text-sm leading-relaxed"
        style={{ fontFamily: "'Inter', sans-serif", color: 'var(--jp-text-primary)' }}
      >
        {children}
      </div>
    </div>
  );
}

function StatBlock({ value, label }) {
  return (
    <div className="text-center">
      <p className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif", color: 'var(--jp-gold)' }}>
        {value}
      </p>
      <p className="text-xs uppercase mt-1" style={{ fontFamily: "'Inter', sans-serif", letterSpacing: '0.1em', color: 'var(--jp-text-muted)' }}>
        {label}
      </p>
    </div>
  );
}

export default function WineryView({ winery, media }) {
  if (!winery) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-sm" style={{ color: 'var(--jp-text-muted)' }}>Loading winery information...</p>
      </div>
    );
  }

  const { name, location, founded_year, description, vineyard_hectares, cellar_description, awards_honors } = winery;

  const wineryImages = (media || []).filter(
    (m) => m.winery_id && !m.product_id && m.media_type === 'image'
  ).slice(0, 8);

  return (
    <div className="max-w-4xl mx-auto py-6">
      {/* Hero Header */}
      <div className="text-center mb-8">
        <p className="text-[10px] uppercase font-semibold mb-2"
          style={{ letterSpacing: '3px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
          Maison de Champagne
        </p>
        <h2 className="text-4xl font-bold mb-2"
          style={{ fontFamily: "'Playfair Display', serif", color: 'var(--jp-text-primary)' }}>
          {name}
        </h2>
        <p className="text-sm" style={{ fontFamily: "'Inter', sans-serif", color: 'var(--jp-text-muted)' }}>
          {location} · Est. {founded_year}
        </p>
      </div>

      {/* Key Facts Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8 py-6"
        style={{ borderTop: '0.5px solid var(--jp-dark-border)', borderBottom: '0.5px solid var(--jp-dark-border)' }}>
        <StatBlock value="1825" label="Founded" />
        <StatBlock value="200" label="Years of Heritage" />
        <StatBlock value={`${vineyard_hectares || 24}`} label="Hectares" />
        <StatBlock value="5km" label="of Cellars" />
      </div>

      {/* Description */}
      {description && (
        <p className="text-sm leading-relaxed mb-8 text-center max-w-2xl mx-auto"
          style={{ fontFamily: "'Inter', sans-serif", color: 'var(--jp-text-secondary)' }}>
          {description}
        </p>
      )}

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {cellar_description && (
          <InfoCard label="The Cellars" colSpan>
            {cellar_description}
          </InfoCard>
        )}

        <InfoCard label="The Vineyard">
          {vineyard_hectares} hectares of estate vineyards across premier and grand cru terroirs
          including Cumières, Hautvillers, Damery, and Verneuil in the Vallée de la Marne.
        </InfoCard>

        <InfoCard label="The Craft">
          Six generations of family winemaking. Each cuvée is aged in the historic Gallo-Roman
          cellars at a constant 10°C, allowing the champagne to develop its full complexity.
        </InfoCard>
      </div>

      {/* Awards */}
      {awards_honors && (
        <div className="mb-8">
          <p className="text-[10px] uppercase font-semibold mb-3"
            style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
            Awards &amp; Recognition
          </p>
          <div className="rounded-lg p-5"
            style={{ backgroundColor: 'var(--jp-dark)', border: '0.5px solid var(--jp-dark-border)' }}>
            <p className="text-sm leading-relaxed"
              style={{ fontFamily: "'Inter', sans-serif", color: 'var(--jp-text-primary)' }}>
              {awards_honors}
            </p>
          </div>
        </div>
      )}

      {/* Visits Info */}
      <div className="mb-8">
        <p className="text-[10px] uppercase font-semibold mb-3"
          style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
          Visit the Estate
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--jp-dark)', border: '0.5px solid var(--jp-dark-border)' }}>
            <p className="text-sm font-medium mb-1" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
              Visite 1825
            </p>
            <p className="text-xs" style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
              Classic cellar tour with Cuvée Royale Brut tasting
            </p>
          </div>
          <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--jp-dark)', border: '0.5px solid var(--jp-dark-border)' }}>
            <p className="text-sm font-medium mb-1" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
              Visite Royale
            </p>
            <p className="text-xs" style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
              Two champagne tastings with your choice of cuvée
            </p>
          </div>
          <div className="rounded-lg p-4" style={{ backgroundColor: 'var(--jp-dark)', border: '0.5px solid var(--jp-dark-border)' }}>
            <p className="text-sm font-medium mb-1" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
              Expérience Joséphine
            </p>
            <p className="text-xs" style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
              Rare tasting with curated food pairings
            </p>
          </div>
        </div>
        <div className="mt-3 text-right">
          <a href="https://www.josephperrier.com/en/visites/?wg-choose-original=false"
            target="_blank" rel="noopener noreferrer"
            className="text-xs"
            style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif", textDecoration: 'none', transition: 'color 0.2s' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--jp-gold)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--jp-text-muted)'; }}>
            Book a visit on josephperrier.com →
          </a>
        </div>
      </div>

      {/* Media Gallery */}
      {wineryImages.length > 0 && (
        <div>
          <p className="text-[10px] uppercase font-semibold mb-3"
            style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
            Gallery
          </p>
          <div className="flex gap-3 overflow-x-auto pb-3">
            {wineryImages.map((item, i) => (
              <img
                key={item.id || i}
                src={item.url}
                alt={item.alt_text || `Winery image ${i + 1}`}
                className="h-48 rounded-lg object-cover flex-shrink-0"
              />
            ))}
          </div>
        </div>
      )}

      {/* Website Link */}
      <div className="mt-8 text-center">
        <a href="https://www.josephperrier.com/en/?wg-choose-original=false"
          target="_blank" rel="noopener noreferrer"
          className="text-xs"
          style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif", textDecoration: 'none', borderBottom: '0.5px solid var(--jp-dark-border)', transition: 'color 0.2s' }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--jp-gold)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--jp-text-muted)'; }}>
          Visit josephperrier.com →
        </a>
      </div>
    </div>
  );
}
