# 使用官方Python运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器中的/app
COPY . /app

# 安装项目依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装FastAPI和Uvicorn
RUN pip install fastapi uvicorn

# 创建/root/download_data/文件夹
RUN mkdir -p /root/download_data/

# 暴露端口8000供外部访问
EXPOSE 8000

# 定义环境变量
ENV NAME World

# 运行应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

# 声明卷，将/root/download_data/挂载出去
VOLUME ["/root/download_data/"]
