# 1. 使用稳健的 3.12 瘦身版基础镜像
FROM python:3.12-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 【优化】环境变量提前，确保从一开始就不产生 .pyc 垃圾，且日志实时刷新
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. 安装系统依赖（MySQL 客户端及编译工具），干完活立刻清理缓存垃圾
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. 先复制依赖文件并安装（只要 requirements.txt 不变，以后每次构建这里都能秒过）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# 6. 复制项目所有代码
COPY . .

# 7. 创建日志文件夹
RUN mkdir -p /app/logs

# 8. 声明容器内部监听 8000 端口
EXPOSE 8000

# 9. 启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "agri_backend.wsgi:application"]