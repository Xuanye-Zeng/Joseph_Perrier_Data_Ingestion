import React, { useEffect } from 'react';

const formatPrice = (price) => {
  if (!price) return null;
  return `€${Number(price).toFixed(2)}`;
};

const capitalize = (text) => {
  if (!text) return text;
  const t = text.trim();
  return t.charAt(0).toUpperCase() + t.slice(1);
};

const getUniqueMedia = (media, sharedPatterns) => {
  if (!media) return [];
  const seen = new Set();
  return media.filter(m => {
    if (m.media_type !== 'image') return false;
    if (sharedPatterns.some(p => m.url.includes(p))) return false;
    const baseUrl = m.url.split('?')[0].replace(/-\d+x\d+\./, '.');
    if (seen.has(baseUrl)) return false;
    seen.add(baseUrl);
    return true;
  });
};

const SHARED_PATTERNS = ['patrimoine', 'savoir-faire', 'actu.webp', 'James-suckling',
  'Bernard-Burtschy', 'bettane', 'Le-Point', 'Vinum', 'drink-business', 'prehome'];

export default function ProductDetail({ product, onClose }) {
  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  if (!product) return null;

  const {
    name, collection, grape_blend, price_eur,
    description, tasting_notes, food_pairings, formats, media,
    source_url, image_url, awards, technical,
  } = product;

  const uniqueMedia = getUniqueMedia(media, SHARED_PATTERNS);

  const note = tasting_notes && tasting_notes.length > 0 ? tasting_notes[0] : null;
  // 4th column: food pairing text
  const pairingText = food_pairings && food_pairings.length > 0
    ? food_pairings.map(p => typeof p === 'string' ? p : p.description).join(' ')
    : null;
  const tastingEntries = note ? [
    { label: 'TO THE EYE', text: capitalize(note.color_description) },
    { label: 'ON THE NOSE', text: capitalize(note.nose_description) },
    { label: 'IN THE MOUTH', text: capitalize(note.palate_description) },
    { label: 'FOOD & WINE PAIRING', text: pairingText },
  ].filter(e => e.text) : [];

  const Divider = () => (
    <hr style={{ border: 'none', borderTop: '0.5px solid var(--jp-dark-border)', margin: '24px 0' }} />
  );

  return (
    <div
      className="fixed inset-0 z-50 flex justify-center overflow-y-auto"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)', paddingTop: '60px', paddingBottom: '60px', alignItems: 'flex-start' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="relative w-full"
        style={{
          backgroundColor: 'var(--jp-black)',
          border: '0.5px solid var(--jp-dark-border)',
          borderRadius: '12px',
          maxWidth: '720px',
          padding: '32px 36px',
          margin: '0 16px',
        }}
      >
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute bg-transparent border-none cursor-pointer"
          style={{ top: 16, right: 16, color: 'var(--jp-text-muted)', fontSize: '20px', lineHeight: 1, transition: 'color 0.2s' }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--jp-gold)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--jp-text-muted)'; }}
        >
          ✕
        </button>

        {/* Hero Image */}
        {image_url && (
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <img src={image_url} alt={name} style={{ maxHeight: '240px', objectFit: 'contain' }} />
          </div>
        )}

        {/* Header */}
        {collection && (
          <p className="text-[10px] uppercase font-semibold mb-2"
            style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
            {collection}
          </p>
        )}
        <h2 className="text-2xl font-bold mb-2"
          style={{ fontFamily: "'Playfair Display', serif", color: 'var(--jp-text-primary)' }}>
          {name}
        </h2>
        {price_eur && (
          <p className="text-xl mb-4"
            style={{ fontFamily: "'Playfair Display', serif", color: 'var(--jp-gold)' }}>
            {formatPrice(price_eur)}
          </p>
        )}
        {description && (
          <p className="text-sm leading-relaxed"
            style={{ color: 'var(--jp-text-secondary)', fontFamily: "'Inter', sans-serif" }}>
            {description}
          </p>
        )}

        {/* Grape Blend */}
        {grape_blend && (
          <>
            <Divider />
            <p className="text-[10px] uppercase font-semibold mb-2"
              style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
              Grape Blend
            </p>
            <p className="text-sm" style={{ color: 'var(--jp-text-secondary)', fontFamily: "'Inter', sans-serif" }}>
              {grape_blend}
            </p>
          </>
        )}

        {/* Technical Details */}
        {technical && (technical.aging_months || technical.dosage_gl != null || technical.reserve_wines_pct || technical.serving_temp_min || technical.aging_potential || technical.crus) && (
          <>
            <Divider />
            <p className="text-[10px] uppercase font-semibold mb-4"
              style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
              Technical Details
            </p>
            <div className="grid grid-cols-2 gap-x-8 gap-y-3">
              {technical.aging_months && (
                <div>
                  <p className="text-[10px] uppercase font-medium mb-0.5"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                    Aging
                  </p>
                  <p className="text-sm" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                    {technical.aging_months} months
                  </p>
                </div>
              )}
              {(technical.dosage_gl !== null && technical.dosage_gl !== undefined) && (
                <div>
                  <p className="text-[10px] uppercase font-medium mb-0.5"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                    Dosage
                  </p>
                  <p className="text-sm" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                    {technical.dosage_gl}g/L
                  </p>
                </div>
              )}
              {technical.reserve_wines_pct && (
                <div>
                  <p className="text-[10px] uppercase font-medium mb-0.5"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                    Reserve Wines
                  </p>
                  <p className="text-sm" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                    ~{technical.reserve_wines_pct}%
                  </p>
                </div>
              )}
              {technical.serving_temp_min && technical.serving_temp_max && (
                <div>
                  <p className="text-[10px] uppercase font-medium mb-0.5"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                    Serving Temperature
                  </p>
                  <p className="text-sm" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                    {technical.serving_temp_min}–{technical.serving_temp_max}°C
                  </p>
                </div>
              )}
              {technical.aging_potential && (
                <div>
                  <p className="text-[10px] uppercase font-medium mb-0.5"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                    Aging Potential
                  </p>
                  <p className="text-sm" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                    {technical.aging_potential}
                  </p>
                </div>
              )}
              {technical.crus && (
                <div className="col-span-2">
                  <p className="text-[10px] uppercase font-medium mb-0.5"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                    Crus Assemblés
                  </p>
                  <p className="text-sm" style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                    {technical.crus}
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {/* Awards & Ratings */}
        {awards && awards.length > 0 && (
          <>
            <Divider />
            <p className="text-[10px] uppercase font-semibold mb-4"
              style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
              Awards &amp; Ratings
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {awards.map((a, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3"
                  style={{ backgroundColor: 'var(--jp-cream)', borderRadius: '8px', border: '0.5px solid var(--jp-dark-border)' }}>
                  {a.logo_url && (
                    <div className="flex-shrink-0" style={{
                      width: '40px', height: '40px', borderRadius: '6px', overflow: 'hidden',
                      backgroundColor: 'var(--jp-cream)', display: 'flex', alignItems: 'center',
                      justifyContent: 'center', padding: '4px',
                    }}>
                      <img src={a.logo_url} alt={a.organization}
                        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
                    </div>
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-medium"
                      style={{ color: 'var(--jp-text-primary)', fontFamily: "'Inter', sans-serif" }}>
                      {a.organization}
                    </p>
                    {(a.score || a.medal || a.detail) && (
                      <p className="text-xs"
                        style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                        {a.score && <span style={{ color: 'var(--jp-gold)', fontWeight: 600 }}>{a.score} pts</span>}
                        {a.score && (a.medal || a.year) && ' — '}
                        {a.medal && <span>{a.medal}</span>}
                        {a.medal && a.year && ' '}
                        {a.year && <span>{a.year}</span>}
                        {!a.score && !a.medal && a.detail && <span>{a.detail}</span>}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Tasting Notes */}
        {tastingEntries.length > 0 && (
          <>
            <Divider />
            <p className="text-[10px] uppercase font-semibold mb-4"
              style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
              Tasting Notes
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tastingEntries.map((entry, idx) => (
                <div key={idx} className="p-4"
                  style={{ backgroundColor: 'var(--jp-cream)', border: '0.5px solid var(--jp-dark-border)', borderRadius: '8px' }}>
                  <p className="text-[11px] uppercase font-medium mb-2"
                    style={{ letterSpacing: '1.5px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
                    {entry.label}
                  </p>
                  <p className="text-sm leading-relaxed"
                    style={{ color: 'var(--jp-text-secondary)', fontFamily: "'Inter', sans-serif" }}>
                    {entry.text}
                  </p>
                </div>
              ))}
            </div>
            {note && note.serving_suggestion && (
              <p className="text-xs mt-3" style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif" }}>
                <span style={{ color: 'var(--jp-gold)' }}>Serving: </span>{note.serving_suggestion}
              </p>
            )}
          </>
        )}

        {/* Food Pairings */}
        {/* Formats */}
        {formats && formats.length > 0 && (
          <>
            <Divider />
            <p className="text-[10px] uppercase font-semibold mb-3"
              style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
              Available Formats
            </p>
            <div className="flex flex-wrap gap-2">
              {formats.map((fmt, idx) => (
                <span key={idx} className="text-xs px-3.5 py-1.5 rounded-full"
                  style={{ border: '0.5px solid var(--jp-dark-border)', color: 'var(--jp-text-secondary)', fontFamily: "'Inter', sans-serif" }}>
                  {(() => {
                    const vol = fmt.volume_cl;
                    const MAPPING = {
                      37: 'Half Bottle — 375ml',
                      75: 'Bottle — 750ml',
                      150: 'Magnum — 1.5L',
                      300: 'Jéroboam — 3L',
                      600: 'Mathusalem — 6L',
                    };
                    if (vol && MAPPING[vol]) return MAPPING[vol];
                    if (vol >= 100) return `${fmt.format_name} — ${(vol / 100).toFixed(1)}L`;
                    if (vol) return `${fmt.format_name} — ${vol * 10}ml`;
                    return fmt.format_name || fmt.name;
                  })()}
                </span>
              ))}
            </div>
          </>
        )}

        {/* Gallery (only if 2+ truly unique images after dedup) */}
        {uniqueMedia.length >= 2 && (
          <>
            <Divider />
            <p className="text-[10px] uppercase font-semibold mb-3"
              style={{ letterSpacing: '2px', color: 'var(--jp-gold)', fontFamily: "'Inter', sans-serif" }}>
              Gallery
            </p>
            <div className="flex gap-3 pb-2" style={{ overflowX: 'auto' }}>
              {uniqueMedia.map((m, idx) => (
                <div key={idx} className="flex-shrink-0"
                  style={{ width: '120px', height: '100px', borderRadius: '8px', overflow: 'hidden', backgroundColor: 'var(--jp-cream)' }}>
                  <img src={m.url} alt={`${name} ${idx + 1}`}
                    className="w-full h-full"
                    style={{ objectFit: 'contain', display: 'block', transition: 'filter 0.2s' }}
                    onMouseEnter={(e) => { e.currentTarget.style.filter = 'brightness(1.05)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.filter = 'none'; }}
                  />
                </div>
              ))}
            </div>
          </>
        )}

        {/* Source URL */}
        {source_url && (
          <>
            <Divider />
            <a href={source_url + (source_url.includes('?') ? '&' : '?') + 'wg-choose-original=false'} target="_blank" rel="noopener noreferrer"
              className="inline-block text-xs"
              style={{ color: 'var(--jp-text-muted)', fontFamily: "'Inter', sans-serif", textDecoration: 'none', borderBottom: '0.5px solid var(--jp-dark-border)', transition: 'color 0.2s' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--jp-gold)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--jp-text-muted)'; }}>
              View on josephperrier.com →
            </a>
          </>
        )}
      </div>
    </div>
  );
}
