import { NextRequest, NextResponse } from 'next/server';

const endpoint = process.env.CLASSES_API_ENDPOINT;
if (!endpoint) {
  throw new Error("CLASSES_API_ENDPOINT is not defined");
}

const API_ENDPOINT: string = endpoint;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log("Incoming body from frontend:", body);
    console.log("Using API endpoint from env:", API_ENDPOINT);

    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const rawText = await response.text(); // log raw first
    console.log("Backend response status:", response.status);
    console.log("Backend raw response:", rawText);

    let parsed;
    try {
      parsed = JSON.parse(rawText);
    } catch (parseError) {
      console.error("Failed to parse backend JSON:", parseError);
      parsed = { raw: rawText }; // fallback
    }

    return NextResponse.json(parsed, { status: response.status });
  } catch (error: any) {
    console.error("Error in /api/classes route:", error);

    return NextResponse.json(
      {
        error: "Internal server error",
        details: error.message || String(error),
      },
      { status: 500 }
    );
  }
}
