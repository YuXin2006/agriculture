import uuid

from django.conf import settings
from django.utils import timezone

from dashboard.models import ChatMessage, ChatSession
from dashboard.services.chat_context import build_agri_context_text
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage





MAX_HISTORY_MESSAGES = 20

SYSTEM_PROMPT = """你是「智慧农业作物监测系统」的 AI 助手，专门解答与环境监测、土壤数据、设备状态、告警分析、农事建议相关的问题。

回答要求：
1. 使用简洁清晰的中文
2. 结合下方提供的实时监测数据作答，不要编造未提供的数据
3. 若数据缺失，如实说明并给出一般性农事建议
4. 涉及紧急告警时提醒用户前往告警中心处理

【当前监测数据摘要】
{context}
"""


class ChatServiceError(Exception):
    pass


def _get_llm():
    

    if not settings.LLM_API_KEY:
        raise ChatServiceError(
            "未配置大模型 API Key，请在 backend/.env 中设置 OPENAI_API_KEY 或 LLM_API_KEY"
        )
    kwargs = {
        "model": settings.LLM_MODEL,
        "temperature": settings.LLM_TEMPERATURE,
        "api_key": settings.LLM_API_KEY,
    }
    if settings.LLM_API_BASE:
        kwargs["base_url"] = settings.LLM_API_BASE
    return ChatOpenAI(**kwargs)


def _get_or_create_session(session_id: str | None) -> ChatSession:
    if session_id:
        session = ChatSession.objects.filter(session_id=session_id).first()
        if session:
            return session
    return ChatSession.objects.create(session_id=uuid.uuid4().hex)


def _history_to_langchain(session: ChatSession) -> list:
    

    messages = []
    recent = list(
        session.messages.filter(role__in=("user", "assistant"))
        .order_by("-created_at")[:MAX_HISTORY_MESSAGES]
    )
    recent.reverse()
    for msg in recent:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    return messages


def _serialize_message(msg: ChatMessage) -> dict:
    return {
        "role": msg.role,
        "content": msg.content,
        "created_at": timezone.localtime(msg.created_at).strftime("%Y-%m-%d %H:%M:%S"),
    }

#核心函数 send_chat_message 发送消息
def send_chat_message(message: str, session_id: str | None = None) -> dict:
    message = (message or "").strip()
    if not message:
        raise ChatServiceError("message 不能为空")

    session = _get_or_create_session(session_id)
    ChatMessage.objects.create(session=session, role="user", content=message)

    

    context = build_agri_context_text()
    llm_messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        *_history_to_langchain(session),
    ]

    llm = _get_llm()
    response = llm.invoke(llm_messages)
    reply = (response.content or "").strip() or "暂无回复"

    ChatMessage.objects.create(session=session, role="assistant", content=reply)
    session.save(update_fields=["updated_at"])

    return {"reply": reply, "session_id": session.session_id}


def get_chat_history(session_id: str | None = None) -> dict:
    if not session_id:
        return {"session_id": None, "messages": []}

    session = ChatSession.objects.filter(session_id=session_id).first()
    if not session:
        return {"session_id": session_id, "messages": []}

    messages = [
        _serialize_message(msg)
        for msg in session.messages.filter(role__in=("user", "assistant")).order_by("created_at")
    ]
    return {"session_id": session_id, "messages": messages}


def clear_chat_session(session_id: str | None = None) -> dict:
    if session_id:
        ChatSession.objects.filter(session_id=session_id).delete()

    session = ChatSession.objects.create(session_id=uuid.uuid4().hex)
    return {"session_id": session.session_id, "cleared": True}
