# 使用官方 Python 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app


# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Scrapyd 和其他可能需要的依赖
RUN pip install --no-cache-dir scrapyd scrapy
VOLUME scrapyd-data /app/logs

VOLUME ["/scrapyd/logs"]



# 复制 Scrapyd 配置文件（如果有的话）
COPY scrapyd.conf /etc/scrapyd/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Scrapyd 默认端口
EXPOSE 6800

# 运行 Scrapyd
CMD ["scrapyd"]
