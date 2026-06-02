# ============================================
# 最简单的 Dockerfile 示例
# ============================================
# 这个 Dockerfile 展示了 Docker 的基本概念：
# - 基础镜像 (FROM)
# - 工作目录 (WORKDIR)
# - 复制文件 (COPY)
# - 暴露端口 (EXPOSE)
# - 启动命令 (CMD)
# ============================================

# 使用官方 Python 精简镜像作为基础
FROM python:3.11-slim

# 维护者信息（可选）
LABEL maintainer="docker-learning@example.com"
LABEL description="Hello Docker - 最简单的 Docker 示例"

# 设置工作目录
WORKDIR /app

# 复制应用代码到容器中
COPY app.py .

# 设置环境变量
ENV PORT=8000

# 暴露端口（文档作用，实际映射需要 -p 参数）
EXPOSE 8000

# 启动应用
CMD ["python", "app.py"]
