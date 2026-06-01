class WebSocketClient {
  constructor() {
    this.socket = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 10000;
    this.callbacks = {};
    this.connected = false;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    let wsUrl = `${protocol}//127.0.0.1:8000/ws/sensor/`;
    
    // 如果是开发环境且配置了 VITE_BASE_URL
    /* const baseURL = import.meta.env.VITE_BASE_URL;
    if (baseURL) {
      const baseHost = baseURL.replace('http://', '').replace('https://', '');
      wsUrl = `${protocol}//${baseHost}/ws/sensor/`;
    } */
    
    console.log('WebSocket connecting to:', wsUrl);
    
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.connected = true;
      this.reconnectDelay = 1000;
      this._trigger('open');
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this._trigger('message', data);
        if (data.type) {
          this._trigger(data.type, data.data);
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connected = false;
      this._trigger('error', error);
    };
    
    this.socket.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.connected = false;
      this._trigger('close', event);
      this._reconnect();
    };
  }

  _reconnect() {
    setTimeout(() => {
      console.log('Reconnecting WebSocket...');
      this.connect();
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    }, this.reconnectDelay);
  }

  on(eventName, callback) {
    if (!this.callbacks[eventName]) {
      this.callbacks[eventName] = [];
    }
    this.callbacks[eventName].push(callback);
  }

  off(eventName, callback) {
    if (this.callbacks[eventName]) {
      this.callbacks[eventName] = this.callbacks[eventName].filter(cb => cb !== callback);
    }
  }

  _trigger(eventName, data) {
    if (this.callbacks[eventName]) {
      this.callbacks[eventName].forEach(callback => callback(data));
    }
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  close() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

// 创建单例
const socketClient = new WebSocketClient();

export default socketClient;
export { WebSocketClient };