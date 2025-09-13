import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const apiEndpoint = process.env.CLASSES_API_ENDPOINT;

    console.log(
      'CLASSES_API_ENDPOINT env:',
      apiEndpoint ?? 'NOT FOUND'
    );

    if (!apiEndpoint) {
      return NextResponse.json(
        {
          statusCode: 500,
          body: JSON.stringify({
            error: 'CLASSES_API_ENDPOINT not set in environment',
          }),
        },
        { status: 500 }
      );
    }

    // Parse incoming request body
    const body = await request.json();
    console.log('Incoming body:', body);

    // Forward request to Lambda/API Gateway
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log('API Gateway response:', data);

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
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
