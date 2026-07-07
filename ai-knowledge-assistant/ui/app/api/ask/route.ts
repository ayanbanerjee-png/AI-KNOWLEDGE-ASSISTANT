import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const API_TOKEN   = process.env.API_TOKEN   || ''

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    const response = await fetch(`${BACKEND_URL}/ask`, {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: JSON.stringify({ question: body.question, top_k: body.top_k || 5 }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || 'Backend error' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)

  } catch (err: any) {
    if (err.code === 'ECONNREFUSED') {
      return NextResponse.json(
        { error: 'Cannot connect to backend. Make sure the API server is running:\n  uvicorn api.main:app --reload --port 8000' },
        { status: 503 }
      )
    }
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}