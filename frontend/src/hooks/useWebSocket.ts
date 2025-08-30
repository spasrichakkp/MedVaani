import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketService, WebSocketEventType, WebSocketEventHandler } from '@/services/webSocketService';
import { HealthStatus, ProgressUpdate } from '@/types/api';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectOnClose?: boolean;
}

export interface UseWebSocketReturn {
  connectionState: string;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  lastHealthUpdate: HealthStatus | null;
  lastProgressUpdate: ProgressUpdate | null;
  error: string | null;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true, reconnectOnClose = true } = options;
  
  const [connectionState, setConnectionState] = useState<string>('disconnected');
  const [lastHealthUpdate, setLastHealthUpdate] = useState<HealthStatus | null>(null);
  const [lastProgressUpdate, setLastProgressUpdate] = useState<ProgressUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Use refs to store handlers to avoid re-registering on every render
  const handlersRef = useRef<{
    healthUpdate: WebSocketEventHandler;
    progressUpdate: WebSocketEventHandler;
    error: WebSocketEventHandler;
    connectionStatus: WebSocketEventHandler;
  }>();

  // Initialize handlers
  useEffect(() => {
    handlersRef.current = {
      healthUpdate: (data: HealthStatus) => {
        setLastHealthUpdate(data);
        setError(null); // Clear error on successful update
      },
      
      progressUpdate: (data: ProgressUpdate) => {
        setLastProgressUpdate(data);
        setError(null); // Clear error on successful update
      },
      
      error: (data: { message: string }) => {
        setError(data.message);
        console.error('[useWebSocket] Error:', data.message);
      },
      
      connectionStatus: (data: { status: string }) => {
        setConnectionState(data.status);
        if (data.status === 'connected') {
          setError(null); // Clear error on successful connection
        }
      },
    };
  }, []);

  // Register event handlers
  useEffect(() => {
    const handlers = handlersRef.current;
    if (!handlers) return;

    // Register handlers
    webSocketService.on('health_update', handlers.healthUpdate);
    webSocketService.on('progress_update', handlers.progressUpdate);
    webSocketService.on('error', handlers.error);
    webSocketService.on('connection_status', handlers.connectionStatus);

    // Cleanup function
    return () => {
      webSocketService.off('health_update', handlers.healthUpdate);
      webSocketService.off('progress_update', handlers.progressUpdate);
      webSocketService.off('error', handlers.error);
      webSocketService.off('connection_status', handlers.connectionStatus);
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      if (!reconnectOnClose) {
        webSocketService.disconnect();
      }
    };
  }, [autoConnect, reconnectOnClose]);

  // Update connection state from service
  useEffect(() => {
    const updateConnectionState = () => {
      setConnectionState(webSocketService.getConnectionState());
    };

    // Update immediately
    updateConnectionState();

    // Set up interval to check connection state
    const interval = setInterval(updateConnectionState, 1000);

    return () => clearInterval(interval);
  }, []);

  const connect = useCallback(async (): Promise<void> => {
    try {
      setError(null);
      await webSocketService.connect();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const disconnect = useCallback((): void => {
    webSocketService.disconnect();
    setError(null);
  }, []);

  const isConnected = connectionState === 'connected';

  return {
    connectionState,
    isConnected,
    connect,
    disconnect,
    lastHealthUpdate,
    lastProgressUpdate,
    error,
  };
}

// Specialized hook for health monitoring
export function useHealthMonitor(autoConnect: boolean = true) {
  const webSocket = useWebSocket({ autoConnect });
  
  return {
    healthStatus: webSocket.lastHealthUpdate,
    connectionState: webSocket.connectionState,
    isConnected: webSocket.isConnected,
    error: webSocket.error,
    reconnect: webSocket.connect,
  };
}

// Specialized hook for progress tracking
export function useProgressTracker(consultationId?: string) {
  const webSocket = useWebSocket({ autoConnect: true });
  
  // Filter progress updates for specific consultation
  const relevantProgress = consultationId && webSocket.lastProgressUpdate?.consultation_id === consultationId
    ? webSocket.lastProgressUpdate
    : null;
  
  return {
    progress: relevantProgress,
    connectionState: webSocket.connectionState,
    isConnected: webSocket.isConnected,
    error: webSocket.error,
  };
}
