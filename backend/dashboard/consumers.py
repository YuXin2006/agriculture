
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SensorConsumer(AsyncWebsocketConsumer):
    """传感器数据WebSocket消费者"""
    
    async def connect(self):
        """建立WebSocket连接"""
        await self.channel_layer.group_add(
            'sensor_updates',
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        await self.channel_layer.group_discard(
            'sensor_updates',
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
    
    async def broadcast_message(self, event):
        """接收广播消息并发送给客户端"""
        message = event['message']
        await self.send(text_data=json.dumps(message))