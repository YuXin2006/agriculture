# backend/gunicorn.conf.py
import multiprocessing

# 1. 绑定的端口：让 Django 守住 8000 端口
bind = "0.0.0.0:8000"

# 2. 并发核心配置（黄金公式）：根据你刚刚查到的服务器 CPU 核心数自动计算！
# 比如 2 核服务器，(2 * 2) + 1 = 5 个工作进程
workers = multiprocessing.cpu_count() * 2 + 1

# 3. 工作模式：使用地表最强、最适合高频网络 I/O 的 gevent 异步模式（需要 pip install gevent）
# 如果追求稳定，也可以不写这行，默认是 'sync' 同步多进程
worker_class = 'gevent'

# 4. 最大并发连接数：每个 worker 进程允许的最大同时连接数（针对物联网高频大屏优化）
worker_connections = 1000

# 5. 超时时间：如果一个大棚数据处理超过 30 秒没响应，自动重启该进程，防止死锁
timeout = 30

# 6. 日志记录：把访问日志和报错日志都存下来，方便以后排查大屏为什么不亮
loglevel = 'info'
accesslog = './logs/gunicorn_access.log'
errorlog = './logs/gunicorn_error.log'