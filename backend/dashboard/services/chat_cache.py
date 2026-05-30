import logging
import json
from dashboard._utils.redis_client import RedisClient
from dashboard._utils.redis_keys import *
from dashboard.models import ChatSession, ChatMessage
from django.utils import timezone

logger = logging.getLogger(__name__)

redis_client = RedisClient()

# 预热标识，确保只执行一次
_warmup_done = False 


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


# ==================== 缓存预热 ====================

def warmup_chat_cache():
    """预热聊天缓存（系统启动时调用）"""
    global _warmup_done
    
    if _warmup_done:
        logger.info("聊天缓存已预热过，跳过")
        return
    
    logger.info("=== 开始预热聊天缓存 ===")
    
    try:
        # 1. 预热会话列表
        warmup_session_list()
        
        # 2. 预热最近会话的消息
        warmup_recent_messages()
        
        # 3. 预热系统常见问题
        warmup_system_faq()
        
        _warmup_done = True
        logger.info("=== 聊天缓存预热完成 ===")
        
    except Exception as e:
        logger.error(f"聊天缓存预热失败: {e}")


def warmup_session_list():
    """预热会话列表"""
    try:
        # 获取最近活跃的会话（最多50个）
        sessions = ChatSession.objects.order_by("-updated_at")[:50]
        
        if not sessions:
            logger.info("暂无会话需要预热")
            return
        
        # 缓存会话列表
        cache_sessions(sessions)
        logger.info(f"预热会话列表: {len(sessions)} 条")
        
    except Exception as e:
        logger.error(f"预热会话列表失败: {e}")


def warmup_recent_messages(limit=10):
    """预热最近活跃会话的消息"""
    try:
        # 获取最近活跃的会话
        sessions = ChatSession.objects.order_by("-updated_at")[:limit]
        
        for session in sessions:
            # 获取会话消息
            messages = session.messages.filter(role__in=("user", "assistant")).order_by("created_at")
            
            if not messages:
                continue
            
            # 使用 pipeline 批量缓存
            key = KEY_CHAT_MESSAGES_TPL.format(session.session_id)
            pipeline = redis_client._client.pipeline()
            
            for msg in messages:
                data = {
                    "id": msg.id,
                    "session_id": session.session_id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "role": msg.role
                }
                pipeline.lpush(key, json.dumps(data))
            
            pipeline.ltrim(key, 0, CHAT_MESSAGES_MAXLEN - 1)
            pipeline.expire(key, EXPIRE_CHAT_MESSAGES)
            pipeline.execute()
            
            logger.info(f"预热会话消息: {session.session_id} ({len(messages)} 条)")
            
    except Exception as e:
        logger.error(f"预热会话消息失败: {e}")


def warmup_system_faq():
    """预热系统常见问题"""
    try:
        faq_data = {
            "questions": [
                {"q": "今天天气怎么样？", "a": "请查看环境监测模块获取实时天气数据"},
                {"q": "如何查看设备状态？", "a": "请访问设备管理页面查看所有设备状态"},
                {"q": "告警如何处理？", "a": "请前往告警中心查看并处理告警"},
                {"q": "土壤湿度多少？", "a": "请查看土壤监测模块获取实时数据"},
                {"q": "如何创建新会话？", "a": "直接发送消息即可自动创建新会话"},
            ],
            "templates": {
                "greeting": "您好！我是智慧农业助手，请问有什么可以帮助您的？",
                "goodbye": "感谢您的使用，祝您工作愉快！",
            }
        }
        
        redis_client.set("agri:chat:faq", faq_data, expire=86400)
        logger.info("预热系统常见问题完成")
        
    except Exception as e:
        logger.error(f"预热系统常见问题失败: {e}")