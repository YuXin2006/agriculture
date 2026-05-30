import json

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from dashboard.services.chat_cache import *
from dashboard.services.chat_agent import (
    ChatServiceError,
    clear_chat_session,
    get_chat_history,
    send_chat_message,
    stream_chat_events,
)


class ChatAPIView(APIView):
    """POST /api/chat/ — 发送消息并获取 AI 回复。"""

    def post(self, request):
        message = request.data.get("message", "")
        session_id = request.data.get("session_id") or None
        try:
            result = send_chat_message(message, session_id)
            return Response(result)
        except ChatServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"AI 服务异常: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatStreamAPIView(APIView):
    """POST /api/chat/stream/ — SSE 流式返回 AI 回复。"""

    def post(self, request):
        message = request.data.get("message", "")
        session_id = request.data.get("session_id") or None

        try:
            events = stream_chat_events(message, session_id)
        except ChatServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"AI 服务异常: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        def sse_generator():
            try:
                for event in events:
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except ChatServiceError as exc:
                yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)}, ensure_ascii=False)}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'detail': f'AI 服务异常: {exc}'}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(
            sse_generator(),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class ChatHistoryAPIView(APIView):
    """GET /api/chat/history/ — 获取会话历史。"""

    def get(self, request):
        session_id = request.query_params.get("session_id") or None
        return Response(get_chat_history(session_id))


class ChatClearAPIView(APIView):
    """POST /api/chat/clear/ — 清空会话并返回新 session_id。"""

    def post(self, request):
        session_id = request.data.get("session_id") or None
        return Response(clear_chat_session(session_id))
