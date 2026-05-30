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

# 过期时间（秒）
EXPIRE_LATEST_DATA = 600  # 10分钟
EXPIRE_ALARMS = 3600      # 1小时
EXPIRE_SUMMARY = 300      # 5分钟
EXPIRE_HISTORY = 86400    # 24小时

# 历史数据窗口大小
HISTORY_WINDOW_SIZE = 288  # 5分钟/次 × 24小时