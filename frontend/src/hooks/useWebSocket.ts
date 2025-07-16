import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  message: string;
  conversation_id: string;
}

interface UseWebSocketProps {
  url: string;
  onMessage: (data: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: (event: CloseEvent) => void;
}

export const useWebSocket = ({ url, onMessage, onError, onClose }: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    // Clear any pending reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Close any existing connection first
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    console.log('Attempting WebSocket connection to:', url);
    setIsConnecting(true);
    try {
      wsRef.current = new WebSocket(url);
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setIsConnecting(false);
      return;
    }

    wsRef.current.onopen = () => {
      console.log('WebSocket connection opened successfully');
      setIsConnected(true);
      setIsConnecting(false);
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Log the received data for debugging
        console.log('Received WebSocket message:', data);
        
        // Check if this is a completion message with sessionId
        if (data.status === 'complete' && data.sessionId) {
          console.log('Received completion with sessionId:', data.sessionId);
        }
        
        onMessage(data);
      } catch (error) {
        console.error('Received non-JSON message from lambda:', event.data);
      }
    };

    wsRef.current.onerror = (error) => {
      setIsConnecting(false);
      const errorInfo = {
        type: error.type || 'error',
        url,
        readyState: wsRef.current?.readyState,
        readyStateText: wsRef.current?.readyState === WebSocket.CONNECTING ? 'CONNECTING' :
                       wsRef.current?.readyState === WebSocket.OPEN ? 'OPEN' :
                       wsRef.current?.readyState === WebSocket.CLOSING ? 'CLOSING' :
                       wsRef.current?.readyState === WebSocket.CLOSED ? 'CLOSED' : 'UNKNOWN',
        timestamp: new Date().toISOString(),
        message: error instanceof ErrorEvent ? error.message : 'WebSocket connection failed'
      };
      console.warn('WebSocket connection warning:', errorInfo);
      // Try to reconnect after a delay
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      reconnectTimeoutRef.current = setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          console.log('Attempting to reconnect WebSocket...');
          connect();
        }
        reconnectTimeoutRef.current = null;
      }, 3000);
      onError?.(error);
    };

    wsRef.current.onclose = (event) => {
      console.log('WebSocket connection closed:', { code: event.code, reason: event.reason, wasClean: event.wasClean });
      setIsConnected(false);
      setIsConnecting(false);
      onClose?.(event);
    };
  };

  const disconnect = () => {
    // Clear any pending reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const sendMessage = (payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const teacherID = window.localStorage.getItem('teacherID');
      const messageWithTeacher = {
        ...payload,
        teacherId: payload.teacherId || teacherID,
        body: payload.message,
        sessionId: payload.sessionId  // Changed from conversation_id to sessionId
      };
      
      // Debug log to verify the session ID
      console.log('Sending message with sessionId:', messageWithTeacher.sessionId);
      
      wsRef.current.send(JSON.stringify(messageWithTeacher));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);
  
  // Cleanup function for component unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    sendMessage
  };
};