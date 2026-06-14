# ============================================
# 多阶段构建 Dockerfile 示例
# ============================================
# 多阶段构建的优势：
# 1. 减小最终镜像体积
# 2. 分离构建环境和运行环境
# 3. 提高安全性（不包含构建工具）
# ============================================

# ---- 阶段 1：构建阶段 ----
FROM python:3.11-slim AS builder

WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

# 安装依赖到临时目录
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- 阶段 2：运行阶段 ----
FROM python:3.11-slim

LABEL maintainer="docker-learning@example.com"
LABEL description="Flask Docker App - 多阶段构建示例"

# 创建非 root 用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 从构建阶段复制安装好的依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY app.py .

# 设置环境变量
ENV FLASK_ENV=production
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 切换到非 root 用户
USER appuser

# 使用 gunicorn 作为生产级 WSGI 服务器
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
