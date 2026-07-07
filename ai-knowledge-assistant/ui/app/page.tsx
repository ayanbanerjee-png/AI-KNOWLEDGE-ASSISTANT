'use client'
import { useState, useRef, useEffect } from 'react'
import { Message, Citation } from '@/lib/types'
import MessageBubble from '@/components/MessageBubble'
import MetricsModal from '@/components/MetricsModal'
function redactPII(text: string): string {
  return text
    // Email addresses
    .replace(/\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b/g, '[EMAIL REDACTED]')
    // US phone numbers
    .replace(/\b(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b/g, '[PHONE REDACTED]')
    // Indian phone numbers
    .replace(/\b(?:\+91[\s-]?)?[6-9]\d{9}\b/g, '[PHONE REDACTED]')
    // UK phone numbers
    .replace(/\b(\+44\s?|0)(\d\s?){9,10}\b/g, '[PHONE REDACTED]')
    // Credit card numbers
    .replace(/\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b/g, '[CARD REDACTED]')
    // Social Security Numbers
    .replace(/\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g, '[SSN REDACTED]')
    // Passport / National ID
    .replace(/\b[A-Z]{1,2}\d{6,9}\b/g, '[ID REDACTED]')
    // IP addresses
    .replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[IP REDACTED]')
}

// ── Suggestion prompts shown on empty state ──────────────────────────────────
const SUGGESTIONS = [
  'Who is the manager of Data Engineering?',
  'How do I report a security vulnerability?',
  'What is the incident response process?',
  'What are the code review rules?',
  'What is the AI Knowledge Assistant project about?',
]

// ── Export format options shown in sidebar ───────────────────────────────────
const EXPORT_FORMATS = [
  { label: 'PDF',  ext: 'pdf',  icon: '📄' },
  { label: 'Word', ext: 'docx', icon: '📝' },
  { label: 'CSV',  ext: 'csv',  icon: '📊' },
  { label: 'MD',   ext: 'md',   icon: '🗒️' },
]

type StoredMessage = Omit<Message, 'timestamp'> & {
  timestamp: Date | string
}

type ChatHistoryEntry = {
  id: string
  title: string
  messages: StoredMessage[]
}

export default function Home() {
  const [messages, setMessages]         = useState<Message[]>([])
  const [input, setInput]               = useState('')
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState('')
  const [uploading, setUploading]       = useState(false)
  const [indexing, setIndexing]         = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [indexStatus, setIndexStatus]   = useState('')
  const [sidebarOpen, setSidebarOpen]   = useState(true)
  const [chatHistory, setChatHistory]   = useState<ChatHistoryEntry[]>([])
  const [drawerOpen, setDrawerOpen]     = useState(false)
  const [metricsOpen, setMetricsOpen]   = useState(false)

  const bottomRef     = useRef<HTMLDivElement>(null)
  const inputRef      = useRef<HTMLTextAreaElement>(null)
  const fileRef       = useRef<HTMLInputElement>(null)
  const currentChatTitle = useRef<string | null>(null) 
  const currentChatId = useRef<string | null>(null)
  const pendingReset   = useRef(false) 
  const lastSavedHash  = useRef<string | null>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── Load chat history from localStorage on mount ──────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem('chat_history')
    if (!saved) return

    try {
      const parsed = JSON.parse(saved) as ChatHistoryEntry[]
      
      // Regenerate titles to include date + time for all chats
      const upgraded = parsed.map(entry => {
        const firstUserMsg = entry.messages.find(m => m.role === 'user')
        if (!firstUserMsg) return entry
        
        const dt = new Date(firstUserMsg.timestamp)
        const dateTime = dt.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        const newTitle = `${firstUserMsg.content.slice(0, 40)}  ${dateTime}`
        
        return { ...entry, title: newTitle }
      })
      
      // Save upgraded history back to localStorage
      localStorage.setItem('chat_history', JSON.stringify(upgraded))
      setChatHistory(upgraded)
    } catch {
      setChatHistory([])
    }
  }, [])

  // ── Send a question to the RAG API ────────────────────────────────────────
  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return
    setError('')

    const userMsg: Message = {
      id:        crypto.randomUUID(),
      role:      'user',
      content:   redactPII(question.trim()),
      timestamp: new Date(),
    }
    const messagesWithUser = [...messages, userMsg]

    // ensure this message is tied to a session id so responses can be
    // associated with the correct conversation even if the user switches
    // chats while the backend is responding.
    const sessionId = currentChatId.current ?? crypto.randomUUID()
    if (!currentChatId.current) currentChatId.current = sessionId

    const dt = new Date()
    const dateTime = dt.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    const requestSessionTitle = currentChatTitle.current ?? `${redactPII(question.trim()).slice(0, 40)}  ${dateTime}`
    if (!currentChatTitle.current) {
      currentChatTitle.current = requestSessionTitle
    }

    // append the user message to the UI immediately
    pendingReset.current = false
    setMessages(messagesWithUser)
    setInput('')
    setLoading(true)

    try {
      const res  = await fetch('/api/ask', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ question: question.trim() }),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Something went wrong.')
        setLoading(false)
        return
      }

      const assistantMsg: Message = {
        id:         crypto.randomUUID(),
        role:       'assistant',
        content:    data.answer,
        citations:  data.citations as Citation[],
        model:      data.model,
        latency_ms: data.latency_ms,
        timestamp:  new Date(),
      }
      // If the session id we used when sending this request is no longer
      // the active session, the user switched chats while the request
      // was in-flight. In that case, save the assistant reply to the
      // corresponding history entry instead of mutating the current UI.
      const requestSession = sessionId
      if (requestSession !== currentChatId.current) {
        setChatHistory(prev => {
          const idx = prev.findIndex(c => c.id === requestSession)
          if (idx >= 0) {
            const updated = prev.slice()
            updated[idx] = {
              ...updated[idx],
              messages: [...updated[idx].messages, assistantMsg],
            }
            localStorage.setItem('chat_history', JSON.stringify(updated))
            return updated
          }

          // create a new history entry for the session that completed
          const entry = {
            id: requestSession,
            title: requestSessionTitle,
            messages: [userMsg, assistantMsg],
          }
          const updated = [entry, ...prev].slice(0, 20)
          localStorage.setItem('chat_history', JSON.stringify(updated))
          return updated
        })
        // don't modify the active messages UI
      } else {
        const updatedMessages = pendingReset.current ? [assistantMsg] : [...messagesWithUser, assistantMsg]
        if (pendingReset.current) pendingReset.current = false
        setMessages(updatedMessages)
        saveToHistory(updatedMessages)
      }
    } catch {
      setError('Network error — is the API server running?')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  // ── Upload documents to the knowledge base ────────────────────────────────
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files
    if (!file || file.length === 0) return

    setUploading(true)
    setUploadStatus('Uploading...')

    const formData = new FormData()
    Array.from(file).forEach(f => formData.append('file', f))

    try {
      const res  = await fetch('/api/upload', { method: 'POST', body: formData })
      const data = await res.json()

      if (res.ok) {
        if (data.renamed) {
          setUploadStatus(`⚠️ ${data.message}`)
        } else {
          setUploadStatus(`✅ ${data.message}`)
        }
      } else {
        setUploadStatus(`❌ ${data.error || 'Upload failed'}`)
      }
    } catch {
      setUploadStatus('❌ Upload failed — is API running?')
    } finally {
      setUploading(false)
      setTimeout(() => setUploadStatus(''), 6000)
    }
  }

  // ── Trigger re-indexing of all documents ─────────────────────────────────
  const handleReindex = async () => {
    setIndexing(true)
    setIndexStatus('Indexing...')

    try {
      const res  = await fetch('/api/reindex', {
        method: 'POST',
        headers: { 'Content-type': 'application/json' },
      })
      const data = await res.json()
      setIndexStatus(res.ok ? `✅ ${data.message || 'Done!'}` : `❌ ${data.error}`)
    } catch {
      setIndexStatus('❌ Reindex failed — is API running?')
    } finally {
      setIndexing(false)
      setTimeout(() => setIndexStatus(''), 6000)
    }
  }

  // ── Export last assistant answer in chosen format ─────────────────────────
  const handleExport = async (format: string) => {
    const lastAnswer = [...messages].reverse().find(m => m.role === 'assistant')
    if (!lastAnswer) {
      alert('No answer to export yet.')
      return
    }

    try {
      const res = await fetch('/api/export', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          format,
          answer:     lastAnswer.content,
          citations:  lastAnswer.citations || [],
          model:      lastAnswer.model,
          latency_ms: lastAnswer.latency_ms,
        }),
      })

      if (!res.ok) {
        const d = await res.json()
        alert(`Export failed: ${d.error}`)
        return
      }

      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `answer.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Export failed — is API running?')
    }
  }

  // ── Enter to send, Shift+Enter for newline ────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const getMessagesHash = (msgs: Message[]) => msgs.map(m => `${m.role}:${m.content}`).join('|')

  // ── Save current chat to history ──────────────────────────────────────────
  const saveToHistory = (overrideMessages?: Message[]) => {
    const currentMessages = overrideMessages ?? messages
    if (currentMessages.length === 0) return

    const wasNewSession = currentChatId.current === null

    const hash = getMessagesHash(currentMessages)
    if (currentChatId.current && lastSavedHash.current === hash) {
      return
    }

    setChatHistory(prev => {
      const id = currentChatId.current ?? crypto.randomUUID()

      const title = currentChatTitle.current ?? (() => {
        const firstUserMsg = currentMessages.find(m => m.role === 'user')
        if (!firstUserMsg) return 'Untitled'
        const dt = new Date(firstUserMsg.timestamp)
        const dateTime = dt.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        return `${firstUserMsg.content.slice(0, 40)}  ${dateTime}`
      })()

      if (!currentChatTitle.current && title !== 'Untitled') {
        currentChatTitle.current = title
      }

      const entry = { id, title, messages: currentMessages }

      // If there's already an entry with this id, update it.
      const existingIdIndex = prev.findIndex(c => c.id === id)
      if (existingIdIndex >= 0) {
        const existing = prev[existingIdIndex]
        const mergedMessages = existing.messages.length >= currentMessages.length ? existing.messages : currentMessages
        const updated = prev.map(c => c.id === id ? { ...entry, messages: mergedMessages } : c)
        localStorage.setItem('chat_history', JSON.stringify(updated))
        currentChatId.current = id
        lastSavedHash.current = hash
        return updated
      }

      // For brand-new sessions, check for an exact duplicate (same title and identical messages sequence).
      if (wasNewSession) {
        const duplicateIndex = prev.findIndex(c => {
          if (c.title !== title) return false
          if (c.messages.length !== currentMessages.length) return false
          for (let i = 0; i < currentMessages.length; i++) {
            const m1 = currentMessages[i]
            const m2 = c.messages[i]
            if (!m2) return false
            if (m1.id !== m2.id && (m1.content !== m2.content || m1.role !== m2.role)) return false
          }
          return true
        })

        if (duplicateIndex >= 0) {
          currentChatId.current = prev[duplicateIndex].id
          lastSavedHash.current = hash
          return prev
        }
      }

      currentChatId.current = id
      const updated = [entry, ...prev].slice(0, 20)
      localStorage.setItem('chat_history', JSON.stringify(updated))
      lastSavedHash.current = hash
      return updated
    })
  }

  // ── Start a new chat ──────────────────────────────────────────────────────
  const startNewChat = () => {
    saveToHistory()
    setMessages([])
    setInput('')
    setError('')
    currentChatId.current = null
    currentChatTitle.current = null
    pendingReset.current = true
    lastSavedHash.current = null
  }

  // ── Load a past chat ──────────────────────────────────────────────────────
  const loadChat = (entry: ChatHistoryEntry) => {
    // Only save the current chat if it's a real unsaved session
    if (messages.length > 0 && currentChatId.current !== null && lastSavedHash.current !== getMessagesHash(messages)) {
      saveToHistory()
    }

    // Load the selected chat's messages
    const loadedMessages = entry.messages.map(m => ({
      ...m,
      timestamp: new Date(m.timestamp),
    }))
    
    setMessages(loadedMessages)
    currentChatId.current = entry.id
    currentChatTitle.current = entry.title
    // mark loaded chat as saved
    lastSavedHash.current = entry.messages.map(m => `${m.role}:${m.content}`).join('|')
  }

  // ── Edit a previous message ───────────────────────────────────────────────
  const handleEdit = (msg: Message) => {
    setInput(msg.content)
    setMessages(prev =>
      prev.slice(0, prev.findIndex(m => m.id === msg.id))
    )
    inputRef.current?.focus()
  }

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div style={{
      display:    'flex',
      height:     '100vh',
      background: 'var(--bg)',
      overflow:   'hidden',
    }}>

      {/* ══════════════════════════════════════════
          SIDEBAR
      ══════════════════════════════════════════ */}
      <aside style={{
        width:         sidebarOpen ? 260 : 0,
        minWidth:      sidebarOpen ? 260 : 0,
        background:    'var(--bg-card)',
        borderRight:   '1px solid var(--border)',
        display:       'flex',
        flexDirection: 'column',
        overflow:      'hidden',
        transition:    'width 0.25s ease, min-width 0.25s ease',
        flexShrink:    0,
      }}>
        <div style={{ padding: '20px 16px', overflowY: 'auto', flex: 1 }}>

          {/* Sidebar title */}
          <div style={{
            fontSize:      13,
            fontWeight:    700,
            color:         'var(--text)',
            fontFamily:    'Syne, sans-serif',
            marginBottom:  20,
            letterSpacing: '-0.02em',
          }}>
            Knowledge Base
          </div>

          {/* ── Upload section ───────────────────── */}
          <SidebarSection label="Upload Documents">
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".pdf,.docx,.md,.txt,.csv"
              style={{ display: 'none' }}
              onChange={handleUpload}
            />
            <SidebarButton
              icon="📁"
              label={uploading ? 'Uploading...' : 'Choose Files'}
              disabled={uploading}
              onClick={() => fileRef.current?.click()}
            />
            <div style={{
              fontSize:   11,
              color:      'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
              marginTop:  6,
              lineHeight: 1.5,
            }}>
              PDF · DOCX · MD · TXT · CSV
            </div>
            {uploadStatus && <StatusPill text={uploadStatus} />}
          </SidebarSection>

          <Divider />

          {/* ── Index section ────────────────────── */}
          <SidebarSection label="Index">
            <SidebarButton
              icon="⚡"
              label={indexing ? 'Indexing...' : 'Run Indexing'}
              disabled={indexing}
              onClick={() => {
                setIndexStatus('Indexing...')
                setIndexing(true)
                fetch('/api/index', { method: 'POST' })
                  .then(r => r.json())
                  .then(d => setIndexStatus(`✅ ${d.message || 'Indexed!'}`))
                  .catch(() => setIndexStatus('❌ Failed'))
                  .finally(() => {
                    setIndexing(false)
                    setTimeout(() => setIndexStatus(''), 3000)
                  })
              }}
            />
            <div style={{
              fontSize:   11,
              color:      'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
              marginTop:  6,
              lineHeight: 1.5,
            }}>
              Embeds new documents into FAISS
            </div>
            {indexStatus && <StatusPill text={indexStatus} />}
          </SidebarSection>

          <Divider />

          {/* ── Reindex section ──────────────────── */}
          <SidebarSection label="Reindex">
            <SidebarButton
              icon="🔄"
              label={indexing ? 'Reindexing...' : 'Full Reindex'}
              disabled={indexing}
              onClick={handleReindex}
            />
            <div style={{
              fontSize:   11,
              color:      'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
              marginTop:  6,
              lineHeight: 1.5,
            }}>
              Clears and rebuilds entire index
            </div>
          </SidebarSection>

          <Divider />

          
          <SidebarButton
            icon="📊"
            label="View Metrics"
            onClick={() => setMetricsOpen(true)}
          />

          <Divider />

          {/* ── Export section ───────────────────── */}
          <SidebarSection label="Export Last Answer">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {EXPORT_FORMATS.map(f => (
                <SidebarButton
                  key={f.ext}
                  icon={f.icon}
                  label={`Export as ${f.label}`}
                  onClick={() => handleExport(f.ext)}
                />
              ))}
            </div>
            <div style={{
              fontSize:   11,
              color:      'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
              marginTop:  8,
              lineHeight: 1.5,
            }}>
              Downloads the last assistant answer
            </div>
          </SidebarSection>

          <Divider />

          {/* ── New chat button ──────────────────────────── */}
          <SidebarButton
            icon="✏️"
            label="New Chat"
             disabled={loading}
            onClick={startNewChat}
          />

          <Divider />

          {/* ── Chat history ─────────────────────────────── */}
          <SidebarSection label="Chat History">
            {chatHistory.length === 0 && (
              <div style={{
                fontSize:   11,
                color:      'var(--text-muted)',
                fontFamily: 'JetBrains Mono, monospace',
                lineHeight: 1.5,
              }}>
                No history yet
              </div>
            )}

            {chatHistory.map(entry => (
              <div
                key={entry.id}
                style={{
                  display:      'flex',
                  alignItems:   'center',
                  marginBottom: 4,
                  border:       '1px solid var(--border)',
                  borderRadius: 6,
                  overflow:     'hidden',
                  background:   'var(--bg-input)',
                }}
              >
                {/* Load chat */}
                <button
                  onClick={() => loadChat(entry)}
                  title={entry.title}
                  style={{
                    flex:         1,
                    textAlign:    'left',
                    background:   'none',
                    border:       'none',
                    padding:      '8px 10px',
                    fontSize:     12,
                    color:        'var(--text-muted)',
                    cursor:       'pointer',
                    fontFamily:   'JetBrains Mono, monospace',
                    lineHeight:   1.5,
                    overflow:     'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace:   'nowrap',
                  }}
                >
                  → {entry.title}
                </button>

                {/* Delete chat */}
                <button
                  onClick={() => {
                    const updated = chatHistory.filter(c => c.id !== entry.id)
                    setChatHistory(updated)
                    localStorage.setItem('chat_history', JSON.stringify(updated))

                    if (currentChatId.current === entry.id) {
                      setMessages([])
                      setInput('')
                      setError('')
                      currentChatId.current = null
                      currentChatTitle.current = null
                    }
                  }}
                  title="Delete chat"
                  style={{
                    background: 'none',
                    border:     'none',
                    cursor:     'pointer',
                    color:      'var(--text-muted)',
                    fontSize:   13,
                    padding:    '6px 8px',
                    flexShrink: 0,
                    lineHeight: 1,
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.color = 'var(--low)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.color = 'var(--text-muted)'
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </SidebarSection>

        </div>
      </aside>

      {/* ══════════════════════════════════════════
          MAIN CHAT AREA
      ══════════════════════════════════════════ */}
      <div style={{
        display:       'flex',
        flexDirection: 'column',
        flex:          1,
        overflow:      'hidden',
      }}>

        {/* ── Header ──────────────────────────────── */}
        <div style={{
          display:      'flex',
          alignItems:   'center',
          gap:          12,
          padding:      '16px 24px',
          borderBottom: '1px solid var(--border)',
          background:   'var(--bg-card)',
          flexShrink:   0,
        }}>
          {/* Sidebar toggle button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              background:   'var(--bg-input)',
              border:       '1px solid var(--border)',
              borderRadius: 6,
              padding:      '5px 9px',
              cursor:       'pointer',
              color:        'var(--text-muted)',
              fontSize:     14,
              lineHeight:   1,
              transition:   'all 0.15s',
            }}
            title="Toggle sidebar"
          >
            ☰
          </button>

          {/* Logo */}
          <div style={{
            width:          34,
            height:         34,
            borderRadius:   8,
            background:     'var(--accent)',
            display:        'flex',
            alignItems:     'center',
            justifyContent: 'center',
            fontSize:       18,
            flexShrink:     0,
          }}>⚡</div>

          <div>
            <div style={{
              fontFamily:    'Syne, sans-serif',
              fontWeight:    700,
              fontSize:      17,
              color:         'var(--text)',
              letterSpacing: '-0.02em',
            }}>
              AI Knowledge Assistant
            </div>
            <div style={{
              fontSize:   11,
              color:      'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
              marginTop:  2,
            }}>
              RAG · FAISS · Mistral
            </div>
          </div>

          {/* Conversation drawer trigger — only when messages exist */}
            <button
              onClick={() => setDrawerOpen(true)}
              style={{
                marginLeft:   'auto',
                background:   'var(--bg-input)',
                border:       '1px solid var(--border)',
                borderRadius: 6,
                padding:      '6px 12px',
                fontSize:     12,
                color:        'var(--text-muted)',
                cursor:       'pointer',
                fontFamily:   'JetBrains Mono, monospace',
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
              📋 conversation
            </button>
        </div>

        {/* ── Messages area ───────────────────────── */}
        <div style={{
          flex:      1,
          overflowY: 'auto',
          padding:   '28px 28px',
        }}>

          {/* Empty state with suggestions */}
          {messages.length === 0 && !loading && (
            <div style={{
              display:        'flex',
              flexDirection:  'column',
              alignItems:     'center',
              justifyContent: 'center',
              height:         '100%',
              gap:            36,
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  fontFamily:    'Syne, sans-serif',
                  fontWeight:    800,
                  fontSize:      32,
                  color:         'var(--text)',
                  letterSpacing: '-0.03em',
                  marginBottom:  10,
                  lineHeight:    1.5,
                }}>
                  Ask anything
                </div>
                <div style={{
                  fontSize:   13,
                  color:      'var(--text-muted)',
                  fontFamily: 'JetBrains Mono, monospace',
                  lineHeight: 1.5,
                }}>
                  Searching across{' '}
                  <span style={{ color: 'var(--accent-2)' }}>13 documents</span>
                  {' · '}
                  <span style={{ color: 'var(--accent-2)' }}>15 chunks</span>
                </div>
              </div>

              {/* Suggestion buttons */}
              <div style={{
                display:       'flex',
                flexDirection: 'column',
                gap:           10,
                width:         '100%',
                maxWidth:      560,
              }}>
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(s)}
                    style={{
                      background:   'var(--bg-card)',
                      border:       '1px solid var(--border)',
                      borderRadius: 8,
                      padding:      '12px 16px',
                      fontSize:     13,
                      color:        'var(--text-muted)',
                      cursor:       'pointer',
                      textAlign:    'left',
                      fontFamily:   'JetBrains Mono, monospace',
                      transition:   'all 0.15s',
                      lineHeight:   1.5,
                    }}
                    onMouseEnter={e => {
                      (e.target as HTMLElement).style.borderColor = 'var(--accent)'
                      ;(e.target as HTMLElement).style.color = 'var(--text)'
                    }}
                    onMouseLeave={e => {
                      (e.target as HTMLElement).style.borderColor = 'var(--border)'
                      ;(e.target as HTMLElement).style.color = 'var(--text-muted)'
                    }}
                  >
                    → {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Render each message */}
          {messages.map(msg => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onEdit={handleEdit}
            />
          ))}

          {/* Thinking animation */}
          {loading && (
            <div className="fade-up" style={{ marginBottom: 24 }}>
              <div style={{
                fontSize:      11,
                color:         'var(--text-muted)',
                marginBottom:  8,
                fontFamily:    'JetBrains Mono, monospace',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}>
                assistant · thinking
              </div>
              <div style={{
                display:      'inline-flex',
                gap:          6,
                padding:      '14px 18px',
                background:   'var(--bg-card)',
                border:       '1px solid var(--border)',
                borderRadius: '12px 12px 12px 4px',
              }}>
                <span className="thinking-dot" />
                <span className="thinking-dot" />
                <span className="thinking-dot" />
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div style={{
              padding:      '12px 16px',
              background:   '#e05c5c18',
              border:       '1px solid #e05c5c40',
              borderRadius: 8,
              fontSize:     13,
              color:        '#e05c5c',
              fontFamily:   'JetBrains Mono, monospace',
              marginBottom: 20,
              lineHeight:   1.5,
              whiteSpace:   'pre-wrap',
            }}>
              ⚠ {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input bar ────────────────────────────── */}
        <div style={{
          padding:    '18px 24px',
          borderTop:  '1px solid var(--border)',
          background: 'var(--bg-card)',
          flexShrink: 0,
        }}>
          <div
            style={{
              display:      'flex',
              gap:          12,
              alignItems:   'flex-end',
              background:   'var(--bg-input)',
              border:       '1px solid var(--border)',
              borderRadius: 10,
              padding:      '12px 16px',
              transition:   'border-color 0.2s',
            }}
            onFocus={e => (e.currentTarget.style.borderColor = 'var(--accent)')}
            onBlur={e  => (e.currentTarget.style.borderColor = 'var(--border)')}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question... (Enter to send, Shift+Enter for newline)"
              rows={1}
              style={{
                flex:       1,
                background: 'none',
                border:     'none',
                outline:    'none',
                resize:     'none',
                fontSize:   14,
                color:      'var(--text)',
                fontFamily: 'JetBrains Mono, monospace',
                lineHeight: 1.5,
                maxHeight:  140,
                overflow:   'auto',
              }}
              onInput={e => {
                const t = e.target as HTMLTextAreaElement
                t.style.height = 'auto'
                t.style.height = Math.min(t.scrollHeight, 140) + 'px'
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              style={{
                background:   loading || !input.trim() ? 'var(--border)' : 'var(--accent)',
                border:       'none',
                borderRadius: 6,
                padding:      '8px 18px',
                fontSize:     13,
                color:        '#fff',
                cursor:       loading || !input.trim() ? 'not-allowed' : 'pointer',
                fontFamily:   'JetBrains Mono, monospace',
                transition:   'background 0.2s',
                flexShrink:   0,
              }}
            >
              {loading ? '...' : 'send →'}
            </button>
          </div>

          <div style={{
            fontSize:   11,
            color:      'var(--text-muted)',
            marginTop:  8,
            fontFamily: 'JetBrains Mono, monospace',
            textAlign:  'center',
            lineHeight: 1.5,
          }}>
            answers grounded in your knowledge base · citations expandable
          </div>
        </div>

      </div>

      {/* ── Conversation Drawer — slides in from right ── */}
      {drawerOpen && (
        <div style={{
          position:       'fixed',
          inset:          0,
          zIndex:         50,
          display:        'flex',
          justifyContent: 'flex-end',
        }}>
          {/* backdrop */}
          <div
            onClick={() => setDrawerOpen(false)}
            style={{
              position:   'absolute',
              inset:      0,
              background: 'rgba(0,0,0,0.4)',
            }}
          />

          {/* drawer panel */}
          <div style={{
            position:      'relative',
            width:         360,
            height:        '100vh',
            background:    'var(--bg-card)',
            borderLeft:    '1px solid var(--border)',
            display:       'flex',
            flexDirection: 'column',
            zIndex:        51,
          }}>
            {/* drawer header */}
            <div style={{
              display:         'flex',
              alignItems:      'center',
              justifyContent:  'space-between',
              padding:         '16px 20px',
              borderBottom:    '1px solid var(--border)',
              flexShrink:      0,
            }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', fontFamily: 'Syne, sans-serif' }}>
                  Conversation
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', marginTop: 2 }}>
                  {messages.length} message{messages.length !== 1 ? 's' : ''}
                </div>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-muted)', fontSize: 18, lineHeight: 1, padding: 4,
                }}
              >
                ✕
              </button>
            </div>

            {/* drawer messages — questions only */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
              {messages.filter(msg => msg.role === 'user').length === 0 ? (
                <div
                  style={{
                    fontSize:   11,
                    color:      'var(--text-muted)',
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: 1.5,
                  }}
                >
                  No questions yet
                </div>
              ) : (
                messages
                  .filter(msg => msg.role === 'user')
                  .map((msg, i) => (
                    <button
                      key={msg.id}
                      onClick={() => {
                        setDrawerOpen(false)

                        setTimeout(() => {
                          document
                            .getElementById(`msg-${msg.id}`)
                            ?.scrollIntoView({
                              behavior: 'smooth',
                              block: 'center',
                            })
                        }, 150)
                      }}
                      style={{
                        display:      'block',
                        width:        '100%',
                        textAlign:    'left',
                        background:   'none',
                        border:       'none',
                        borderLeft:   '2px solid var(--border)',
                        padding:      '8px 12px',
                        marginBottom: 6,
                        cursor:       'pointer',
                        transition:   'all 0.15s',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.borderLeftColor = 'var(--accent)'
                        e.currentTarget.style.background = 'var(--bg-input)'
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.borderLeftColor = 'var(--border)'
                        e.currentTarget.style.background = 'none'
                      }}
                    >
                      <div
                        style={{
                          fontSize:     10,
                          color:        'var(--text-muted)',
                          fontFamily:   'JetBrains Mono, monospace',
                          marginBottom: 3,
                        }}
                      >
                        Q{i + 1} ·{' '}
                        {new Date(msg.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>

                      <div
                        style={{
                          fontSize:     12,
                          color:        'var(--text)',
                          fontFamily:   'JetBrains Mono, monospace',
                          lineHeight:   1.5,
                          whiteSpace:   'nowrap',
                          overflow:     'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {msg.content}
                      </div>
                    </button>
                  ))
              )}
            </div>
          </div>
        </div>
      )}

      <MetricsModal
        isOpen={metricsOpen}
        onClose={() => setMetricsOpen(false)}
      />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Small reusable sidebar components
// ─────────────────────────────────────────────────────────────────────────────

/** Section wrapper with label */
function SidebarSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontSize:      10,
        fontFamily:    'JetBrains Mono, monospace',
        color:         'var(--text-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        marginBottom:  8,
      }}>
        {label}
      </div>
      {children}
    </div>
  )
}

/** Sidebar action button */
function SidebarButton({
  icon, label, onClick, disabled,
}: {
  icon: string; label: string; onClick: () => void; disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        width:         '100%',
        display:       'flex',
        alignItems:    'center',
        gap:           8,
        background:    'var(--bg-input)',
        border:        '1px solid var(--border)',
        borderRadius:  6,
        padding:       '9px 12px',
        fontSize:      13,
        color:         disabled ? 'var(--text-muted)' : 'var(--text)',
        cursor:        disabled ? 'not-allowed' : 'pointer',
        fontFamily:    'JetBrains Mono, monospace',
        transition:    'all 0.15s',
        lineHeight:    1.5,
        textAlign:     'left',
      }}
      onMouseEnter={e => {
        if (!disabled) (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'
      }}
    >
      <span style={{ fontSize: 15 }}>{icon}</span>
      {label}
    </button>
  )
}

/** Thin horizontal divider */
function Divider() {
  return (
    <div style={{
      height:     1,
      background: 'var(--border)',
      margin:     '12px 0',
    }} />
  )
}

/** Small status feedback pill */
function StatusPill({ text }: { text: string }) {
  const color = text.startsWith('✅') ? 'var(--high)'
              : text.startsWith('❌') ? 'var(--low)'
              : text.startsWith('⚠️') ? 'var(--medium)'
              : 'var(--text-muted)'

  return (
    <div style={{
      marginTop:  8,
      fontSize:   11,
      fontFamily: 'JetBrains Mono, monospace',
      color:      color,
      lineHeight: 1.5,
    }}>
      {text}
    </div>
  )
}
