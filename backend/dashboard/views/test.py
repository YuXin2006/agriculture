from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def broadcast_test(request):
    """测试 WebSocket 广播接口"""
    if request.method == 'POST':
        try:
            # 获取请求体数据
            payload = json.loads(request.body.decode('utf-8'))
            
            # 调用广播函数
            from dashboard.services.mqtt_cache import broadcast_to_channel
            broadcast_to_channel('sensor_updates', payload)
            
            return JsonResponse({'status': 'success', 'message': 'Broadcast sent'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)