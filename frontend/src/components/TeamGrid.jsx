import React from 'react';

function getInitials(name) {
  if (!name) return '?';
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export default function TeamGrid({ members }) {
  if (!members || members.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-sm" style={{ color: 'var(--jp-text-muted)' }}>
          No team members available
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto py-6">
      {members.map((member, index) => (
        <div
          key={member.name + '-' + index}
          className="flex gap-5 rounded-lg p-6"
          style={{
            backgroundColor: 'var(--jp-dark)',
            border: '0.5px solid var(--jp-dark-border)',
          }}
        >
          {/* Avatar */}
          <div className="flex-shrink-0">
            {member.image_url ? (
              <img
                src={member.image_url}
                alt={member.name}
                className="w-20 h-20 rounded-full object-cover"
              />
            ) : (
              <div
                className="w-20 h-20 rounded-full flex items-center justify-center text-lg font-bold"
                style={{
                  backgroundColor: 'var(--jp-gold)',
                  color: 'var(--jp-black)',
                  fontFamily: "'Playfair Display', serif",
                }}
              >
                {getInitials(member.name)}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <h3
              className="text-lg font-medium"
              style={{
                fontFamily: "'Playfair Display', serif",
                color: 'var(--jp-text-primary)',
              }}
            >
              {member.name}
            </h3>

            {member.role && (
              <p
                className="text-sm"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: 'var(--jp-gold)',
                }}
              >
                {member.role}
              </p>
            )}

            {member.generation && (
              <p
                className="text-xs mt-0.5"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: 'var(--jp-text-muted)',
                }}
              >
                {member.generation}
              </p>
            )}

            {member.bio && (
              <p
                className="text-sm mt-2 leading-relaxed"
                style={{
                  fontFamily: "'Inter', sans-serif",
                  color: 'var(--jp-text-secondary)',
                }}
              >
                {member.bio}
              </p>
            )}

            <a
              href="https://www.josephperrier.com/en/maison/famille/?wg-choose-original=false"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs mt-2"
              style={{
                color: 'var(--jp-text-muted)',
                fontFamily: "'Inter', sans-serif",
                textDecoration: 'none',
                transition: 'color 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--jp-gold)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--jp-text-muted)'; }}
            >
              View full profile →
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
