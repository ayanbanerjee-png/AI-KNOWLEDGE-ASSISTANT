import { NextRequest, NextResponse } from 'next/server'

const API_TOKEN = process.env.API_TOKEN || ''

export async function POST(req: NextRequest) {
  try {
    const res  = await fetch('http://localhost:8000/reindex', {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: JSON.stringify({ mode: 'full' }),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (e: any) {
    return NextResponse.json(
      { error: `Reindex failed: ${e.message}` },
      { status: 500 }
    )
  }
}