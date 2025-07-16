import { NextRequest, NextResponse } from 'next/server';

const API_ENDPOINT = process.env.STUDENT_PROFILE_API_ENDPOINT || 'YOUR_STUDENT_PROFILE_API_ENDPOINT_HERE';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Student Profile API Error:', error);
    return NextResponse.json(
      { statusCode: 500, body: JSON.stringify({ error: 'Internal server error' }) },
      { status: 500 }
    );
  }
}