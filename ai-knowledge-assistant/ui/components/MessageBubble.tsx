'use client'
import { useState } from 'react'
import { Message } from '@/lib/types'
import CitationCard from './CitationCard'

export default function MessageBubble({
  message,
  onEdit,
}: {
  message: Message
  onEdit?: (msg: Message) => void  // optional edit callback from page.tsx
}) {
  const [showCitations, setShowCitations] = useState(false)
  const [hovered, setHovered]             = useState(false)
  const isUser = message.role === 'user'

  return (
    <div
      id={`msg-${message.id}`}
      className="fade-up"
      style={{
        display:       'flex',
        flexDirection: 'column',
        alignItems:    isUser ? 'flex-end' : 'flex-start',
        marginBottom:  28,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Role label — shows model name, response time and edit button */}
      <div style={{
        fontSize:      11,
        color:         'var(--text-muted)',
        marginBottom:  8,
        fontFamily:    'JetBrains Mono, monospace',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        lineHeight:    1.5,
        display:       'flex',
        alignItems:    'center',
        gap:           8,
      }}>
        {isUser ? 'you' : `assistant · ${message.model || 'mistral'}`}
        {message.latency_ms ? ` · ${message.latency_ms}ms` : ''}

        {/* Edit button — only shows on user messages when hovered */}
        {isUser && hovered && onEdit && (
          <button
            onClick={() => onEdit(message)}
            title="Edit this message"
            style={{
              background:   'none',
              border:       '1px solid var(--border)',
              borderRadius: 4,
              padding:      '1px 6px',
              fontSize:     10,
              color:        'var(--text-muted)',
              cursor:       'pointer',
              fontFamily:   'JetBrains Mono, monospace',
              lineHeight:   1.5,
              transition:   'all 0.15s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = 'var(--accent)'
              e.currentTarget.style.color = 'var(--text)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.color = 'var(--text-muted)'
            }}
          >
            ✏️ edit
          </button>
        )}
      </div>

      {/* Message bubble */}
      <div style={{
        maxWidth:     '78%',
        padding:      '14px 18px',
        borderRadius: isUser ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
        background:   isUser ? 'var(--accent)' : 'var(--bg-card)',
        border:       isUser ? 'none' : '1px solid var(--border)',
        fontSize:     15,
        lineHeight:   1.5,
        color:        isUser ? '#fff' : 'var(--text)',
        fontFamily:   'JetBrains Mono, monospace',
        whiteSpace:   'pre-wrap',
        wordBreak:    'break-word',
      }}>
        {message.content}
      </div>

      {/* Citations toggle button — only for assistant messages */}
      {!isUser && message.citations && message.citations.length > 0 && (
        <div style={{ maxWidth: '78%', width: '100%', marginTop: 10 }}>
          <button
            onClick={() => setShowCitations(!showCitations)}
            style={{
              background:   'none',
              border:       '1px solid var(--border)',
              borderRadius: 6,
              padding:      '5px 12px',
              fontSize:     12,
              color:        'var(--accent-2)',
              cursor:       'pointer',
              fontFamily:   'JetBrains Mono, monospace',
              marginBottom: showCitations ? 10 : 0,
              transition:   'border-color 0.2s',
              lineHeight:   1.5,
            }}
          >
            {showCitations ? '▲ hide' : '▼ show'}{' '}
            {message.citations.length} source{message.citations.length > 1 ? 's' : ''}
          </button>

          {/* Expandable citation list */}
          {showCitations && (
            <div className="fade-up">
              {message.citations.map(c => (
                <CitationCard key={c.rank} citation={c} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}