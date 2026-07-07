import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const API_TOKEN   = process.env.API_TOKEN   || ''

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    const res = await fetch(`${BACKEND_URL}/export`, {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
      },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const err = await res.json()
      return NextResponse.json(
        { error: err.detail || 'Export failed' },
        { status: res.status }
      )
    }

    const blob        = await res.blob()
    const contentType = res.headers.get('content-type') || 'application/octet-stream'
    const disposition = res.headers.get('content-disposition') || `attachment; filename=answer.${body.format}`

    return new NextResponse(blob, {
      headers: {
        'Content-Type':        contentType,
        'Content-Disposition': disposition,
      }
    })

  } catch (e: any) {
    return NextResponse.json(
      { error: `Export failed: ${e.message}` },
      { status: 500 }
    )
  }
}