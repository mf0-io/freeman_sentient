import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for managing WebSocket connections with auto-reconnect.
 * Handles connection lifecycle, message parsing, and error recovery.
 *
 * @param {string} url - WebSocket server URL
 * @param {Object} options - Configuration options
 * @param {number} options.reconnectInterval - Milliseconds between reconnection attempts (default: 3000)
 * @param {number} options.maxReconnectAttempts - Maximum reconnection attempts (default: 5)
 * @returns {Object} Connection state and controls
 */
export function useWebSocket(url, options = {}) {
  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [messageHistory, setMessageHistory] = useState([]);
  const reconnectAttempts = useRef(0);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  /**
   * Send a message through the WebSocket connection.
   */
  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const messageString = typeof message === 'string' ? message : JSON.stringify(message);
        wsRef.current.send(messageString);
      } catch (err) {
        setError(new Error(`Failed to send message: ${err.message}`));
      }
    } else {
      setError(new Error('WebSocket is not connected'));
    }
  }, []);

  /**
   * Manually disconnect the WebSocket connection.
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  /**
   * Manually reconnect the WebSocket connection.
   */
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    setError(null);
  }, [disconnect]);

  useEffect(() => {
    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    /**
     * Create WebSocket connection and set up event handlers.
     */
    const connect = () => {
      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          setError(null);
          reconnectAttempts.current = 0;
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            setData(message);
            setMessageHistory((prev) => [...prev, message]);
          } catch {
            // If not JSON, store as plain text
            setData(event.data);
            setMessageHistory((prev) => [...prev, { raw: event.data }]);
          }
        };

        ws.onerror = (event) => {
          setError(new Error('WebSocket error occurred'));
          // Don't set connected to false here - onclose will handle that
        };

        ws.onclose = () => {
          setConnected(false);
          wsRef.current = null;

          // Attempt reconnection if we haven't exceeded max attempts
          if (reconnectAttempts.current < maxReconnectAttempts) {
            reconnectAttempts.current += 1;
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, reconnectInterval);
          } else {
            setError(new Error(`WebSocket connection failed after ${maxReconnectAttempts} attempts`));
          }
        };
      } catch (err) {
        setError(new Error(`Failed to create WebSocket connection: ${err.message}`));
      }
    };

    connect();

    // Cleanup function
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url, reconnectInterval, maxReconnectAttempts]);

  return {
    data,
    connected,
    error,
    messageHistory,
    sendMessage,
    disconnect,
    reconnect,
  };
}
