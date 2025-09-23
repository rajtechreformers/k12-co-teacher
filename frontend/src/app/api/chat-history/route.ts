"use server";

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { teacherId, conversationId, classId } = body;

    if (!teacherId) {
      return NextResponse.json({
        statusCode: 400,
        body: 'Missing teacherId parameter'
      });
    }

    // Call the REST API endpoint
    const apiUrl = process.env.NEXT_PUBLIC_CHAT_HISTORY_API;
    if (!apiUrl) {
      throw new Error("NEXT_PUBLIC_CHAT_HISTORY_API is not defined");
    }
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        teacherId,
        conversationId,
        classId
      })
    });

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    return NextResponse.json({
      statusCode: 200,
      body: data
    });
    
  } catch (error) {
    console.error('Error in chat-history API:', error);
    return NextResponse.json({
      statusCode: 500,
      body: 'Internal server error'
    });
  }
}