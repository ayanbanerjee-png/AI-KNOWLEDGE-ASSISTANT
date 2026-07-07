import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const res  = await fetch(`${BACKEND_URL}/metrics`)
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (e: any) {
    return NextResponse.json({ error: `Failed to fetch metrics: ${e.message}` }, { status: 500 })
  }
}
