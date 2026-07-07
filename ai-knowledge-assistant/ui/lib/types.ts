export interface Citation {
  rank:       number
  score:      number
  confidence: 'High' | 'Medium' | 'Low'
  title:      string
  source:     string
  snippet:    string
}

export interface Message {
  id:         string
  role:       'user' | 'assistant'
  content:    string
  citations?: Citation[]
  model?:     string
  latency_ms?: number
  timestamp:  Date
}
