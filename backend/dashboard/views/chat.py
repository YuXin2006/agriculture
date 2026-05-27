from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.services.chat_agent import (
    ChatServiceError,
    clear_chat_session,
    get_chat_history,
    send_chat_message,
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
