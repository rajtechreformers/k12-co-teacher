import { NextRequest, NextResponse } from 'next/server';

const API_ENDPOINT = process.env.CLASSES_API_ENDPOINT || 'https://6ll9oei3u3.execute-api.us-west-2.amazonaws.com/dev/getClassesForDashboard';

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
    console.error('API Error:', error);
    return NextResponse.json(
      { statusCode: 500, body: JSON.stringify({ error: 'Internal server error' }) },
      { status: 500 }
    );
  }
}