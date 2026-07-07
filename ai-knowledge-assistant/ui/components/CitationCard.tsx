'use client'
import { useState } from 'react'
import { Citation } from '@/lib/types'

// Returns color based on confidence level
function confidenceColor(level: string) {
  if (level === 'High')   return 'var(--high)'
  if (level === 'Medium') return 'var(--medium)'
  return 'var(--low)'
}

export default function CitationCard({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false)
  const color = confidenceColor(citation.confidence)

  return (
    <div
      style={{
        background:   'var(--bg-input)',
        border:       `1px solid var(--border)`,
        borderLeft:   `3px solid ${color}`,
        borderRadius: 6,
        marginBottom: 8,
        overflow:     'hidden',
        transition:   'border-color 0.2s',
      }}
    >
      {/* Header row — click to expand */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          width:      '100%',
          display:    'flex',
          alignItems: 'center',
          gap:        10,
          padding:    '10px 14px',
          background: 'none',
          border:     'none',
          cursor:     'pointer',
          textAlign:  'left',
        }}
      >
        {/* Rank badge */}
        <span style={{
          fontSize:   11,
          fontFamily: 'JetBrains Mono, monospace',
          color:      color,
          background: `${color}18`,
          border:     `1px solid ${color}40`,
          borderRadius: 4,
          padding:    '2px 6px',
          minWidth:   28,
          textAlign:  'center',
          lineHeight: 1.5,
        }}>
          #{citation.rank}
        </span>

        {/* Document title */}
        <span style={{
          flex:          1,
          fontSize:      13,
          color:         'var(--text)',
          fontFamily:    'JetBrains Mono, monospace',
          fontWeight:    500,
          overflow:      'hidden',
          textOverflow:  'ellipsis',
          whiteSpace:    'nowrap',
          lineHeight:    1.5,
        }}>
          {citation.title}
        </span>

        {/* Confidence score */}
        <span style={{
          fontSize:   11,
          color:      color,
          fontFamily: 'JetBrains Mono, monospace',
          marginRight: 6,
          lineHeight: 1.5,
        }}>
          {citation.confidence} · {citation.score}
        </span>

        {/* Expand chevron */}
        <span style={{
          color:      'var(--text-muted)',
          fontSize:   11,
          transform:  open ? 'rotate(180deg)' : 'rotate(0)',
          transition: 'transform 0.2s',
        }}>▼</span>
      </button>

      {/* Expandable snippet section */}
      {open && (
        <div style={{
          padding:   '0 14px 12px 14px',
          borderTop: '1px solid var(--border)',
        }}>
          {/* Source file name */}
          <div style={{
            fontSize:   11,
            color:      'var(--text-muted)',
            marginTop:  10,
            marginBottom: 6,
            fontFamily: 'JetBrains Mono, monospace',
            lineHeight: 1.5,
          }}>
            📄 {citation.source}
          </div>

          {/* Snippet text */}
          <div style={{
            fontSize:   13,
            color:      'var(--text)',
            lineHeight: 1.5,
            fontFamily: 'JetBrains Mono, monospace',
            fontStyle:  'italic',
            opacity:    0.85,
          }}>
            "{citation.snippet}"
          </div>
        </div>
      )}
    </div>
  )
}
