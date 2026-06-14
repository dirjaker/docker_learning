# 示例 01：Hello Docker 🐳

最简单的 Docker 镜像示例，使用 Python 内置 HTTP 服务器，无需任何外部依赖。

## 学习目标

- 理解 Dockerfile 的基本结构
- 学会构建 Docker 镜像
- 学会运行 Docker 容器
- 理解端口映射的概念

## 文件说明

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker 镜像构建文件 |
| `app.py` | 简单的 Python HTTP 服务器 |

## 快速开始

### 1. 构建镜像

```bash
docker build -t hello-docker .
```

### 2. 运行容器

```bash
docker run -d -p 8000:8000 --name hello hello-docker
```

### 3. 访问应用

```bash
# 使用浏览器访问
open http://localhost:8000

# 或使用 curl
curl http://localhost:8000
curl http://localhost:8000/info
curl http://localhost:8000/health
```

### 4. 查看容器日志

```bash
docker logs hello
```

### 5. 停止并删除容器

```bash
docker stop hello
docker rm hello
```

## Dockerfile 解析

```dockerfile
FROM python:3.11-slim    # 基础镜像：Python 3.11 精简版
WORKDIR /app              # 设置工作目录
COPY app.py .             # 复制代码到容器
ENV PORT=8000             # 设置环境变量
EXPOSE 8000               # 声明端口
CMD ["python", "app.py"]  # 启动命令
```

## 常用命令

```bash
# 查看本地镜像
docker images | grep hello-docker

# 查看运行中的容器
docker ps

# 进入容器内部
docker exec -it hello /bin/bash

# 查看容器详情
docker inspect hello
```

## 下一步

完成这个示例后，继续学习 [02-python-app](../02-python-app/)，了解如何构建更复杂的 Python 应用。
