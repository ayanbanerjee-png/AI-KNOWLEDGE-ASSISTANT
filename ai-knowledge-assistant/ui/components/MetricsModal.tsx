'use client'
import { useState, useEffect } from 'react'

interface Stats {
  total_queries:        number
  avg_latency_ms:       number
  min_latency_ms:       number
  max_latency_ms:       number
  avg_recall:           number
  avg_citation_coverage: number
  avg_grounding:        number
}

interface RecentLog {
  timestamp:        string
  question:         string
  latency_ms:       number
  recall_at_k:      number
  grounding_score:  number
  sources:          string
}

interface Props {
  isOpen:  boolean
  onClose: () => void
}

export default function MetricsModal({ isOpen, onClose }: Props) {
  const [stats, setStats]   = useState<Stats | null>(null)
  const [logs, setLogs]     = useState<RecentLog[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')
  const [tab, setTab]       = useState<'overview' | 'recent'>('overview')

  useEffect(() => {
    if (!isOpen) return
    fetchMetrics()
  }, [isOpen])

  const fetchMetrics = async () => {
    setLoading(true)
    setError('')
    try {
      const res  = await fetch('/api/metrics')
      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Failed to load metrics'); return }
      setStats(data.stats)
      setLogs(data.recent_logs || [])
    } catch {
      setError('Cannot connect to backend — is API running?')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 200 }} />

      {/* Modal */}
      <div style={{
        position:      'fixed',
        top:           '50%',
        left:          '50%',
        transform:     'translate(-50%, -50%)',
        width:         620,
        maxHeight:     '80vh',
        background:    'var(--bg-card)',
        border:        '1px solid var(--border)',
        borderRadius:  12,
        zIndex:        201,
        display:       'flex',
        flexDirection: 'column',
        boxShadow:     '0 8px 40px rgba(0,0,0,0.5)',
        overflow:      'hidden',
      }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          <div>
            <div style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 15, color: 'var(--text)' }}>📊 Evaluation Metrics</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', marginTop: 2 }}>
              {stats ? `${stats.total_queries} queries logged` : 'Loading...'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={fetchMetrics} style={btnStyle}>↺ refresh</button>
            <button onClick={onClose} style={{ ...btnStyle, color: 'var(--low)' }}>✕</button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          {(['overview', 'recent'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              flex: 1, padding: '10px 0', fontSize: 12, fontFamily: 'JetBrains Mono, monospace',
              background: 'none', border: 'none', cursor: 'pointer',
              color:      tab === t ? 'var(--accent)' : 'var(--text-muted)',
              borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
              transition: 'all 0.15s',
            }}>
              {t === 'overview' ? '📈 Overview' : '🕒 Recent Queries'}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          {loading && <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, padding: 40 }}>Loading metrics...</div>}
          {error  && <div style={{ color: 'var(--low)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>⚠ {error}</div>}

          {!loading && !error && stats && tab === 'overview' && (
            <div>
              {/* Score cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 20 }}>
                <MetricCard label="Total Queries"   value={String(stats.total_queries)}                              unit=""    color="var(--accent)" />
                <MetricCard label="Avg Latency"     value={stats.avg_latency_ms ? (stats.avg_latency_ms / 1000).toFixed(1) : 'N/A'} unit="s"  color="var(--medium)" />
                <MetricCard label="Avg Recall@K"    value={stats.avg_recall ? (stats.avg_recall * 100).toFixed(1) : 'N/A'}  unit="%"   color="var(--high)" />
                <MetricCard label="Avg Grounding"   value={stats.avg_grounding ? (stats.avg_grounding * 100).toFixed(1) : 'N/A'} unit="%" color="var(--high)" />
                <MetricCard label="Citation Cov."   value={stats.avg_citation_coverage ? (stats.avg_citation_coverage * 100).toFixed(1) : 'N/A'} unit="%" color="var(--accent-2)" />
                <MetricCard label="Min / Max Latency" value={stats.min_latency_ms ? `${stats.min_latency_ms} / ${stats.max_latency_ms}` : 'N/A'} unit="ms" color="var(--text-muted)" />
              </div>

              {/* Score bars */}
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Performance</div>
              <ScoreBar label="Recall@K"    value={stats.avg_recall || 0}            color="var(--high)" />
              <ScoreBar label="Grounding"   value={stats.avg_grounding || 0}         color="var(--accent)" />
              <ScoreBar label="Citation Cov" value={stats.avg_citation_coverage || 0} color="var(--accent-2)" />
            </div>
          )}

          {!loading && !error && tab === 'recent' && (
            <div>
              {logs.length === 0 && <div style={{ color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>No queries logged yet.</div>}
              {logs.map((log, i) => (
                <div key={i} style={{ marginBottom: 12, padding: '10px 14px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text)', fontFamily: 'JetBrains Mono, monospace', marginBottom: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    → {log.question}
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 10, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
                    <span>⏱ {log.latency_ms}ms</span>
                    <span>📊 Recall: {log.recall_at_k}</span>
                    <span>🎯 Grounding: {log.grounding_score}</span>
                    <span style={{ marginLeft: 'auto' }}>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

function MetricCard({ label, value, unit, color }: { label: string; value: string; unit: string; color: string }) {
  return (
    <div style={{ padding: '14px 16px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 8, borderLeft: `3px solid ${color}` }}>
      <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 22, fontFamily: 'Syne, sans-serif', fontWeight: 700, color }}>
        {value}<span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 4 }}>{unit}</span>
      </div>
    </div>
  )
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100)
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)', marginBottom: 4 }}>
        <span>{label}</span><span style={{ color }}>{pct}%</span>
      </div>
      <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 6,
  padding: '5px 10px', fontSize: 11, color: 'var(--text-muted)', cursor: 'pointer',
  fontFamily: 'JetBrains Mono, monospace',
}
