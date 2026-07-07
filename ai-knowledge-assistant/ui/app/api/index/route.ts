import { NextRequest, NextResponse } from 'next/server'

const API_TOKEN = process.env.API_TOKEN || ''

export async function POST(req: NextRequest) {
  try {
    const res  = await fetch('http://localhost:8000/index', {
      method:  'POST',
      headers: { 'Authorization': `Bearer ${API_TOKEN}` },
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (e: any) {
    return NextResponse.json(
      { error: `Index failed: ${e.message}` },
      { status: 500 }
    )
  }
}