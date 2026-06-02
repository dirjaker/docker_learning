# 示例 02：Python Flask 应用 🐍

演示如何将一个标准 Flask 应用 Docker 化，使用多阶段构建优化镜像体积。

## 学习目标

- 理解多阶段构建（Multi-stage Build）的概念和优势
- 学会使用 `.dockerignore` 排除不需要的文件
- 理解 Docker 层缓存机制
- 学会使用 gunicorn 作为生产级 WSGI 服务器
- 学会创建非 root 用户运行容器

## 文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | Flask 应用代码 |
| `requirements.txt` | Python 依赖列表 |
| `Dockerfile` | 多阶段构建文件 |
| `.dockerignore` | 排除不需要复制到镜像的文件 |

## 快速开始

### 1. 构建镜像

```bash
docker build -t flask-app .
```

### 2. 运行容器

```bash
docker run -d -p 5000:5000 --name flask-app flask-app
```

### 3. 测试应用

```bash
# 首页（浏览器访问）
curl http://localhost:5000

# API 端点
curl http://localhost:5000/api/info
curl http://localhost:5000/api/health
curl http://localhost:5000/api/stats
```

### 4. 查看镜像大小

```bash
docker images flask-app
# 对比如果不使用多阶段构建的镜像大小
```

## Dockerfile 解析

### 多阶段构建

```dockerfile
# 阶段 1：安装依赖
FROM python:3.11-slim AS builder
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# 阶段 2：只复制运行时需要的文件
FROM python:3.11-slim
COPY --from=builder /install /usr/local
COPY app.py .
```

### 安全最佳实践

```dockerfile
# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

## 开发模式

```bash
# 以开发模式运行（开启热重载）
docker run -d -p 5000:5000 \
  -e FLASK_ENV=development \
  -v $(pwd):/app \
  --name flask-dev \
  python:3.11-slim \
  bash -c "pip install flask && python app.py"
```

## 下一步

继续学习 [03-multi-container](../03-multi-container/)，了解如何使用 Docker Compose 管理多容器应用。
