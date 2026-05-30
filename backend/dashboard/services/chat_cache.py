import logging
from dashboard._utils.redis_client import RedisClient
from dashboard._utils.redis_keys import *
from dashboard.models import ChatSession, ChatMessage
from django.utils import timezone

logger = logging.getLogger(__name__)

redis_client = RedisClient() 


def cache_session(session):
    """缓存单个会话  string实现"""
    key=KEY_CHAT_SESSION_TPL.format(session.session_id)
    data = {
        "id": session.id,
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    redis_client.set(key, data, expire=EXPIRE_CHAT_SESSION)
    
def get_session(session_id):
    """获取单个会话"""
    key=KEY_CHAT_SESSION_TPL.format(session_id)
    data = redis_client.get(key)
    if data:
        return data
    try:
        session = ChatSession.objects.get(session_id=session_id)
        cache_session(session)
        return {
            "id": session.id,
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    except ChatSession.DoesNotExist:
        return None    







def cache_sessions(sessions):
    """缓存会话列表 string实现"""
    data=[]
    for session in sessions:
        data.append({
            "id": session.id,
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        })
    redis_client.set(KEY_CHAT_SESSIONS, data, expire=EXPIRE_CHAT_SESSIONS)    
    
def get_sessions():
    """获取会话列表"""
    data = redis_client.get(KEY_CHAT_SESSIONS)
    if data:
        return data
    sessions = ChatSession.objects.all()
    cache_sessions(sessions)
    return [{
        "id": session.id,
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    } for session in sessions]





def cache_messages( session_id, content, message_id=None, created_at=None, role=None):    
    """缓存会话消息列表 list实现"""
    key=KEY_CHAT_MESSAGES_TPL.format(session_id)
    data = {
        "id": message_id,
        "session_id": session_id,
        "content": content,
        "created_at": created_at or timezone.now().isoformat(),
        "role": role
    }
    redis_client.lpush(key, data, expire=EXPIRE_CHAT_MESSAGES, maxlen=CHAT_MESSAGES_MAXLEN)
    
def get_messages(session_id):    
    """获取会话消息列表"""
    key=KEY_CHAT_MESSAGES_TPL.format(session_id)
    data=redis_client.lrange(key)
    if data:
        return data[::-1]  # 反转列表，保持消息顺序
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = session.messages.all().order_by("created_at")
        for msg in messages:
            cache_messages(
                session_id=session_id,
                content=msg.content,
                message_id=msg.id,
                created_at=msg.created_at.isoformat(),
                role=msg.role
            )
        return [{
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        } for msg in messages]    
    except ChatSession.DoesNotExist:
        return []    
