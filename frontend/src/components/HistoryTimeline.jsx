import React from 'react';

export default function HistoryTimeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-sm" style={{ color: 'var(--jp-text-muted)' }}>
          No history events available
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-6">
      {events.map((event, index) => {
        const isLast = index === events.length - 1;

        return (
          <div key={event.year + '-' + index} className="flex items-start gap-6 mb-0">
            {/* Year */}
            <div
              className="text-2xl font-bold text-right"
              style={{
                fontFamily: "'Playfair Display', serif",
                color: 'var(--jp-gold)',
                minWidth: '80px',
                paddingTop: '2px',
              }}
            >
              {event.year}
            </div>

            {/* Timeline dot + line */}
            <div className="flex flex-col items-center" style={{ paddingTop: '8px' }}>
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: 'var(--jp-gold)' }}
              />
              {!isLast && (
                <div
                  className="flex-1"
                  style={{
                    width: '1px',
                    backgroundColor: 'var(--jp-gold)',
                    opacity: 0.3,
                    minHeight: '40px',
                  }}
                />
              )}
            </div>

            {/* Description */}
            <div
              className="text-sm leading-relaxed pb-8"
              style={{
                fontFamily: "'Inter', sans-serif",
                color: 'var(--jp-text-secondary)',
                paddingTop: '3px',
              }}
            >
              {event.event_description}
            </div>
          </div>
        );
      })}
    </div>
  );
}
