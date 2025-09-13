import { NextRequest, NextResponse } from 'next/server';

const API_ENDPOINT =
  process.env.CLASSES_API_ENDPOINT ||
  'https://6ll9oei3u3.execute-api.us-west-2.amazonaws.com/dev/getClassesForDashboard';

export async function POST(request: NextRequest) {
  try {
    console.log("CLASSES_API_ENDPOINT env:", process.env.CLASSES_API_ENDPOINT);
    console.log("Resolved API endpoint:", API_ENDPOINT);

    const body = await request.json();
    console.log("Incoming body:", body);

    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log("API Gateway response:", data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        statusCode: 500,
        body: JSON.stringify({ error: 'Internal server error' }),
      },
      { status: 500 }
    );
  }
}
