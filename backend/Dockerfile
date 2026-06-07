# 1. 直接用你本地绝对存在的 nginx:alpine 作为地基，无需任何联网下载！
FROM nginx:alpine

# 2. 设置工作目录
WORKDIR /app

# 3. 环境变量提前，禁止生成垃圾文件
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. 核心改动：利用 Alpine 的包管理器 apk 离线编译安装环境
RUN apk update && apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    mariadb-connector-c-dev \
    pkgconfig

# 5. 修复软链接
RUN ln -sf python3 /usr/bin/python && ln -sf pip3 /usr/bin/pip

# 6. 先复制依赖文件并安装（💡【核心修正】末尾加上了 --break-system-packages 通行证）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt --break-system-packages

# 7. 强行打满组件补丁（💡【核心修正】末尾同样加上通行证）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn paho-mqtt gunicorn --break-system-packages

# 8. 复制项目所有代码
COPY . .

# 9. 创建日志文件夹
RUN mkdir -p /app/logs

# 10. 声明容器内部监听端口
EXPOSE 8000
EXPOSE 8001

# 默认启动命令
CMD ["gunicorn", "--config", "gunicorn.conf.py", "agri_backend.wsgi:application"]