import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketHook {
  sendMessage: (message: any) => void;
  lastMessage: MessageEvent | null;
  connectionStatus: 'Connecting' | 'Connected' | 'Disconnected' | 'Error';
  reconnect: () => void;
}

export const useWebSocket = (url: string): WebSocketHook => {
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Connected' | 'Disconnected' | 'Error'>('Disconnected');
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${url}`;

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('Connecting');
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setConnectionStatus('Connected');
      reconnectAttempts.current = 0;
      console.log('WebSocket connected');
    };

    ws.current.onclose = (event) => {
      setConnectionStatus('Disconnected');
      console.log('WebSocket disconnected:', event.code, event.reason);

      // Attempt to reconnect if it wasn't a manual close
      if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, delay);
      }
    };

    ws.current.onerror = (error) => {
      setConnectionStatus('Error');
      console.error('WebSocket error:', error);
    };

    ws.current.onmessage = (event) => {
      setLastMessage(event);
    };
  }, [wsUrl]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    reconnectAttempts.current = 0;
    if (ws.current) {
      ws.current.close();
    }
    connect();
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  return {
    sendMessage,
    lastMessage,
    connectionStatus,
    reconnect,
  };
};