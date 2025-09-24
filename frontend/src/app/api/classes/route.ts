import { NextRequest, NextResponse } from 'next/server';

const endpoint = process.env.CLASSES_API_ENDPOINT;
if (!endpoint) {
  throw new Error("CLASSES_API_ENDPOINT is not defined");
}

const API_ENDPOINT: string = endpoint;


export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log("Incoming body:", body);
    console.log("Using hardcoded API endpoint:", API_ENDPOINT);

    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log("API Gateway response:", data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { statusCode: 500, body: JSON.stringify({ error: 'Internal server error' }) },
      { status: 500 }
    );
  }
}
