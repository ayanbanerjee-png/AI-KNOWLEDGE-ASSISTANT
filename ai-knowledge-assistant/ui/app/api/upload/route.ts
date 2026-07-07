import { NextRequest, NextResponse } from 'next/server'

const API_TOKEN = process.env.API_TOKEN || ''

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData()
    const file = formData.get('file') as File | null

    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      )
    }

    const forward = new FormData()
    forward.append('file', file, file.name)

    const res  = await fetch('http://localhost:8000/upload', {
      method:  'POST',
      headers: { 'Authorization': `Bearer ${API_TOKEN}` },
      body:    forward,
    })

    const data = await res.json()
    return NextResponse.json(data, { status: res.status })

  } catch (e: any) {
    return NextResponse.json(
      { error: `Upload failed: ${e.message}` },
      { status: 500 }
    )
  }
}