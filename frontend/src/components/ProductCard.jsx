import React from 'react';

const ChampagneBottleSVG = () => (
  <svg
    width="48"
    height="120"
    viewBox="0 0 48 120"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ opacity: 0.35 }}
  >
    <path
      d="M19 2C19 2 18 8 18 14C18 20 16 24 14 30C12 36 10 42 10 52V108C10 112 14 116 20 116H28C34 116 38 112 38 108V52C38 42 36 36 34 30C32 24 30 20 30 14C30 8 29 2 29 2H19Z"
      stroke="var(--jp-gold)"
      strokeWidth="1.5"
      fill="none"
    />
    <rect x="16" y="58" width="16" height="24" rx="1" stroke="var(--jp-gold)" strokeWidth="0.75" fill="none" />
    <line x1="19" y1="0" x2="29" y2="0" stroke="var(--jp-gold)" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

function Tag({ children }) {
  return (
    <span
      className="text-[10px] px-2 py-0.5 rounded-full"
      style={{
        border: '0.5px solid var(--jp-dark-border)',
        color: 'var(--jp-text-secondary)',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {children}
    </span>
  );
}

export default function ProductCard({ product, onClick }) {
  const {
    name,
    collection,
    type,
    grape_blend,
    price_eur,
    vintage,
    is_limited_edition,
    media,
  } = product;

  const imageUrl = product.image_url || (media && media.length > 0 ? media[0].url || media[0] : null);

  return (
    <div
      className="relative overflow-hidden cursor-pointer"
      onClick={onClick}
      style={{
        backgroundColor: 'var(--jp-dark)',
        border: '0.5px solid var(--jp-dark-border)',
        borderRadius: '12px',
        transition: 'border-color 0.3s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--jp-gold)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--jp-dark-border)';
      }}
    >
      {/* Limited Edition Badge */}
      {(!!is_limited_edition || is_limited_edition === 1) && (
        <span
          className="absolute top-3 right-3 z-10 text-[10px] uppercase px-2 py-1 font-semibold"
          style={{
            backgroundColor: 'var(--jp-gold)',
            color: 'var(--jp-black)',
            borderRadius: '4px',
            fontFamily: "'Inter', sans-serif",
            letterSpacing: '1px',
          }}
        >
          LIMITED
        </span>
      )}

      {/* Image Area */}
      <div
        className="flex items-center justify-center"
        style={{
          position: 'relative',
          height: '200px',
          backgroundColor: 'var(--jp-black)',
        }}
      >
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={name}
            className="w-full h-full"
            style={{ objectFit: 'contain' }}
          />
        ) : (
          <ChampagneBottleSVG />
        )}
      </div>

      {/* Content Area */}
      <div className="p-5">
        {/* Collection Label */}
        {collection && (
          <p
            className="text-[10px] uppercase font-semibold mb-1"
            style={{
              letterSpacing: '2px',
              color: 'var(--jp-gold)',
              fontFamily: "'Inter', sans-serif",
            }}
          >
            {collection}
          </p>
        )}

        {/* Product Name */}
        <h3
          className="text-lg font-medium mb-2"
          style={{
            fontFamily: "'Playfair Display', serif",
            color: 'var(--jp-text-primary)',
          }}
        >
          {name}
        </h3>

        {/* Grape Blend */}
        {grape_blend && (
          <p
            className="text-xs mb-3 truncate"
            style={{
              color: 'var(--jp-text-muted)',
              fontFamily: "'Inter', sans-serif",
            }}
          >
            {grape_blend}
          </p>
        )}

        {/* Bottom Row */}
        <div className="flex justify-between items-center">
          {/* Price */}
          <span
            className="text-lg"
            style={{
              fontFamily: "'Playfair Display', serif",
              color: 'var(--jp-gold)',
            }}
          >
            {price_eur ? `€${Number(price_eur).toFixed(2)}` : 'Price on request'}
          </span>

          {/* Tags */}
          <div className="flex items-center gap-1.5">
            {type && <Tag>{type}</Tag>}
            {vintage && <Tag>{vintage}</Tag>}
          </div>
        </div>
      </div>
    </div>
  );
}
