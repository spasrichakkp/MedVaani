import { WebSocketMessage, HealthStatus, ProgressUpdate } from '@/types/api';

export type WebSocketEventType = 'health_update' | 'progress_update' | 'error' | 'connection_status';

export interface WebSocketEventHandler {
  (data: any): void;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private eventHandlers: Map<WebSocketEventType, WebSocketEventHandler[]> = new Map();
  private isConnecting = false;
  private shouldReconnect = true;

  constructor() {
    this.url = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/health';
    this.initializeEventHandlers();
  }

  private initializeEventHandlers(): void {
    this.eventHandlers.set('health_update', []);
    this.eventHandlers.set('progress_update', []);
    this.eventHandlers.set('error', []);
    this.eventHandlers.set('connection_status', []);
  }

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;
      this.shouldReconnect = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to health monitoring');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.emit('connection_status', { status: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
            this.emit('error', { message: 'Failed to parse WebSocket message' });
          }
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] Connection closed:', event.code, event.reason);
          this.isConnecting = false;
          this.ws = null;
          this.emit('connection_status', { status: 'disconnected' });

          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Connection error:', error);
          this.isConnecting = false;
          this.emit('error', { message: 'WebSocket connection error' });
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    console.log('[WebSocket] Received message:', message.type);
    
    switch (message.type) {
      case 'health_update':
        this.emit('health_update', message.data as HealthStatus);
        break;
      case 'progress_update':
        this.emit('progress_update', message.data as ProgressUpdate);
        break;
      case 'error':
        this.emit('error', message.data);
        break;
      default:
        console.warn('[WebSocket] Unknown message type:', message.type);
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`[WebSocket] Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.connect().catch((error) => {
          console.error('[WebSocket] Reconnect failed:', error);
        });
      }
    }, delay);
  }

  public disconnect(): void {
    this.shouldReconnect = false;
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.emit('connection_status', { status: 'disconnected' });
  }

  public on(eventType: WebSocketEventType, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.push(handler);
    this.eventHandlers.set(eventType, handlers);
  }

  public off(eventType: WebSocketEventType, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(eventType) || [];
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
      this.eventHandlers.set(eventType, handlers);
    }
  }

  private emit(eventType: WebSocketEventType, data: any): void {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`[WebSocket] Error in ${eventType} handler:`, error);
      }
    });
  }

  public getConnectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }

  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;
