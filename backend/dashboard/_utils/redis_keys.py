# dashboard/utils/redis_keys.py
"""Redis缓存键命名常量"""

# 最新数据
KEY_LATEST_ENV = "agri:latest:env"
KEY_LATEST_SOIL = "agri:latest:soil"
KEY_LATEST_SENSOR = "agri:latest:sensor"
KEY_LATEST_ALARMS = "agri:latest:alarms"

# 历史数据
KEY_HISTORY_ENV = "agri:history:env"
KEY_HISTORY_SOIL = "agri:history:soil"

# 汇总数据
KEY_SUMMARY = "agri:summary"

#chatbot数据
KEY_CHAT_SESSION_TPL = "agri:chat:session:{}"  # 单个会话
KEY_CHAT_MESSAGES_TPL = "agri:chat:messages:{}"  # 会话消息列表
KEY_CHAT_SESSIONS = "agri:chat:sessions"  # 会话列表

# 过期时间（秒）
EXPIRE_LATEST_DATA = 600  # 10分钟
EXPIRE_ALARMS = 3600      # 1小时
EXPIRE_SUMMARY = 300      # 5分钟
EXPIRE_HISTORY = 86400    # 24小时
EXPIRE_CHAT_SESSION = 86400  # 24小时
EXPIRE_CHAT_MESSAGES = 86400  # 24小时
EXPIRE_CHAT_SESSIONS = 3600   # 1小时

# 会话消息列表最大长度
CHAT_MESSAGES_MAXLEN = 100

# 历史数据窗口大小
HISTORY_WINDOW_SIZE = 288  # 5分钟/次 × 24小时