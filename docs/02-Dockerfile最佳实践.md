# Dockerfile 最佳实践

> Dockerfile 就像一份「烹饪食谱」——告诉 Docker 怎样一步步把原材料（基础镜像）变成一道菜（你的应用镜像）。写得好，菜又快又好吃（镜像小、构建快、安全）；写得差，又慢又臃肿还有安全隐患。

---

## 目录

1. [Dockerfile 指令详解](#1-dockerfile-指令详解)
2. [多阶段构建（Multi-stage Build）](#2-多阶段构建multi-stage-build)
3. [镜像优化技巧](#3-镜像优化技巧)
4. [安全最佳实践](#4-安全最佳实践)
5. [实战示例](#5-实战示例)
6. [常见问题和踩坑经验](#6-常见问题和踩坑经验)

---

## 1. Dockerfile 指令详解

### 1.1 FROM — 选择基础镜像

`FROM` 是 Dockerfile 的第一行，决定了你的「起点」。就像盖房子，地基选得好，上面的工程就省事。

```dockerfile
# 三种常见的基础镜像风格
FROM python:3.12          # 完整版，约 900MB，包含大量预装工具
FROM python:3.12-slim     # 精简版，约 130MB，只保留运行必需的库
FROM python:3.12-alpine   # 极简版，约 50MB，基于 Alpine Linux
```

**区别对比：**

| 镜像类型 | 大小 | 适用场景 | 注意事项 |
|---------|------|---------|---------|
| `full` | ~900MB | 开发调试、需要编译工具 | 生产环境不推荐，太大 |
| `slim` | ~130MB | **生产推荐**，平衡大小和兼容性 | 大多数场景的最佳选择 |
| `alpine` | ~50MB | 对镜像大小极致敏感 | 用 musl libc，可能有兼容性问题 |

**为什么 alpine 不总是最佳选择？**

Alpine 用的是 `musl libc` 而不是主流的 `glibc`。某些 Python/Node 包包含 C 扩展，编译时可能会出问题。slim 基于 Debian，用的是 glibc，兼容性更好。

```bash
# 对比镜像大小
docker images python:3.12 python:3.12-slim python:3.12-alpine
```

**最佳实践：**
- 生产环境优先用 `slim` 版本
- 只有确认所有依赖都兼容 musl 时才用 `alpine`
- 完整版只在开发/调试时使用
- 固定版本号，不用 `latest`

```dockerfile
# ❌ 不推荐
FROM python:latest

# ✅ 推荐
FROM python:3.12-slim
```

---

### 1.2 RUN — 执行命令

`RUN` 就像在容器里敲命令。每执行一条 `RUN`，就会生成一个镜像层（Layer）。

```dockerfile
# ❌ 错误示范：每个命令一个 RUN，产生 3 层
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# ✅ 正确示范：合并成一个 RUN，只产生 1 层
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

**为什么？**

1. **层数 = 镜像大小**：每一层都会被保存，即使后面的层删除了文件，前面的层依然包含它们。
2. **缓存**：Docker 会缓存每一层。如果某条 RUN 没变，就直接用缓存，不重新执行。

**类比：** 想象你在画一幅画。每画一层就拍一张照片（层）。如果你先画了蓝色（安装软件），然后用白色涂掉（删除文件），蓝色其实还在照片里。合并成一步，就只有一张「干净」的照片。

```dockerfile
# 实际例子：安装 Node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get purge -y --auto-remove curl gnupg && \
    rm -rf /var/lib/apt/lists/*
```

---

### 1.3 COPY vs ADD — 区别和使用场景

这两个指令都是把文件复制到镜像里，但 `ADD` 有「隐藏技能」。

```dockerfile
# COPY：简单直接，就是复制文件
COPY requirements.txt /app/
COPY . /app/

# ADD：比 COPY 多两个功能
ADD app.tar.gz /app/    # 自动解压 tar 包！
ADD https://example.com/file.txt /app/  # 自动下载远程文件！
```

**什么时候用哪个？**

| 指令 | 功能 | 推荐场景 |
|------|------|---------|
| `COPY` | 纯粹的文件复制 | **99% 的情况都应该用 COPY** |
| `ADD` | 复制 + 自动解压 / 下载远程文件 | 只在需要自动解压 tar 包时使用 |

**为什么优先用 COPY？**

`ADD` 的行为不直观。看到 `ADD` 时，你不确定它到底是复制、解压还是下载。`COPY` 的行为完全可预测——就是复制文件。

```dockerfile
# ❌ 不推荐：用 ADD 复制普通文件（行为不明确）
ADD requirements.txt /app/

# ✅ 推荐：用 COPY（意图清晰）
COPY requirements.txt /app/

# ✅ 用 ADD 的合理场景：自动解压
ADD node-v20.10.0-linux-x64.tar.gz /usr/local/
```

---

### 1.4 CMD vs ENTRYPOINT — 区别和组合使用

这两个指令都用来定义容器启动时运行的命令，但行为不同。

**类比：**
- `ENTRYPOINT` = 你是一家餐厅的固定招牌菜（不容易被覆盖）
- `CMD` = 今天的推荐套餐（顾客可以换成别的）

```dockerfile
# CMD：默认命令，可以被 docker run 后面的参数覆盖
CMD ["python", "app.py"]

# ENTRYPOINT：固定入口，不容易被覆盖
ENTRYPOINT ["python"]
CMD ["app.py"]
```

**区别演示：**

```dockerfile
# Dockerfile A：只有 CMD
FROM python:3.12-slim
CMD ["python", "app.py"]
```

```bash
# 运行：执行 python app.py
docker run myapp

# 运行：CMD 被覆盖，执行 bash
docker run myapp bash
```

```dockerfile
# Dockerfile B：ENTRYPOINT + CMD
FROM python:3.12-slim
ENTRYPOINT ["python"]
CMD ["app.py"]
```

```bash
# 运行：执行 python app.py
docker run myapp

# 运行：执行 python bash（bash 作为参数传给了 python！）
docker run myapp bash

# 想覆盖 ENTRYPOINT？需要加 --entrypoint
docker run --entrypoint bash myapp
```

**最佳实践：组合使用**

```dockerfile
# 推荐模式：ENTRYPOINT 定义主程序，CMD 定义默认参数
ENTRYPOINT ["python"]
CMD ["app.py"]

# 运行时可以方便地传入不同参数
# docker run myapp                    → python app.py
# docker run myapp test.py            → python test.py
# docker run myapp -m pytest          → python -m pytest
```

**Shell 格式 vs Exec 格式：**

```dockerfile
# ❌ Shell 格式：命令通过 /bin/sh -c 执行，信号处理有问题
CMD python app.py
ENTRYPOINT python app.py

# ✅ Exec 格式：直接执行，信号正确传递（可以优雅停机）
CMD ["python", "app.py"]
ENTRYPOINT ["python", "app.py"]
```

**为什么 Exec 格式更好？**

Shell 格式下，PID 1 是 `/bin/sh` 而不是你的应用。当你 `docker stop` 时，SIGTERM 发给了 shell，而不是你的应用，导致应用无法优雅停机，只能等超时后被 SIGKILL 强杀。

---

### 1.5 ENV — 环境变量

`ENV` 设置的环境变量会持久存在于镜像中，容器运行时也能访问。

```dockerfile
# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app
ENV PORT=8000

# 可以在后续指令中引用
WORKDIR $APP_HOME
EXPOSE $PORT
```

**常见用途：**

```dockerfile
# Python：禁用输出缓冲，让日志实时可见
ENV PYTHONUNBUFFERED=1

# Node.js：设置生产环境
ENV NODE_ENV=production

# 设置时区
ENV TZ=Asia/Shanghai
```

**注意事项：**

```dockerfile
# ❌ 不要用 ENV 存放敏感信息！会暴露在镜像元数据中
ENV DB_PASSWORD=supersecret123

# ✅ 运行时通过 docker run -e 传入
# docker run -e DB_PASSWORD=supersecret123 myapp
```

---

### 1.6 ARG — 构建参数

`ARG` 只在构建阶段（`docker build`）有效，运行时不可用。

```dockerfile
# 声明构建参数
ARG PYTHON_VERSION=3.12
ARG APP_VERSION=1.0.0

# 在 FROM 中使用 ARG
FROM python:${PYTHON_VERSION}-slim

# 在其他指令中使用
LABEL version=$APP_VERSION
```

```bash
# 构建时传入参数
docker build --build-arg PYTHON_VERSION=3.11 -t myapp .

# 查看 ARG 的值（只能在构建阶段看到）
docker build --build-arg APP_VERSION=2.0.0 -t myapp .
```

**ARG vs ENV 的区别：**

| 特性 | ARG | ENV |
|------|-----|-----|
| 生效阶段 | 仅构建时 | 构建时 + 运行时 |
| 安全性 | 构建后不可见 | 镜像元数据中可见 |
| 用法 | 传递构建参数 | 设置运行时环境 |

```dockerfile
# 结合使用：用 ARG 定义默认值，用 ENV 传递到运行时
ARG APP_PORT=8000
ENV PORT=$APP_PORT
EXPOSE $PORT
```

---

### 1.7 EXPOSE — 声明端口

`EXPOSE` 只是「声明」容器监听哪个端口，实际上并不会发布端口。

```dockerfile
# 声明容器监听 8000 端口
EXPOSE 8000

# 声明 TCP 和 UDP
EXPOSE 8000/tcp
EXPOSE 5353/udp
```

**类比：** `EXPOSE` 就像在门上贴了个标签「这里是餐厅入口」，但门本身并没有打开。真正开门需要 `-p` 参数。

```bash
# EXPOSE 只是文档性质，实际发布端口需要 -p
docker build -t myapp .
docker run -p 8080:8000 myapp  # 把宿主机 8080 映射到容器 8000
```

**最佳实践：** 保留 `EXPOSE` 作为文档，说明容器需要哪些端口。

---

### 1.8 WORKDIR — 工作目录

`WORKDIR` 设置后续指令的工作目录。如果目录不存在，会自动创建。

```dockerfile
# 设置工作目录
WORKDIR /app

# 后续所有命令都在 /app 下执行
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

**为什么不用 `RUN cd /app`？**

```dockerfile
# ❌ 不推荐：cd 只在当前 RUN 生效，下一条 RUN 又回到根目录
RUN cd /app
RUN python app.py    # 报错！找不到 app.py

# ✅ 推荐：WORKDIR 持久生效
WORKDIR /app
RUN python app.py    # 正常运行
```

**类比：** `RUN cd` 就像你走进一个房间做了一件事，然后又走出来了。`WORKDIR` 就像你搬进了一个房间，之后所有活动都在这里。

---

### 1.9 USER — 运行用户

默认情况下，容器以 `root` 用户运行。`USER` 指令可以切换到非 root 用户。

```dockerfile
# 创建非 root 用户并切换
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "app.py"]
```

**为什么不要用 root？**

如果容器被攻破，root 用户可以做任何事情（访问宿主机内核漏洞等）。非 root 用户限制了攻击者的权限。

```dockerfile
# Node.js 镜像自带 node 用户，可以直接用
FROM node:20-slim
WORKDIR /app
COPY --chown=node:node . .
RUN npm ci --production
USER node
CMD ["node", "server.js"]
```

---

### 1.10 HEALTHCHECK — 健康检查

告诉 Docker 怎么判断容器是否「健康运行」。

```dockerfile
# 每 30 秒检查一次，超时 10 秒，连续 3 次失败则标记为不健康
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**为什么需要健康检查？**

没有健康检查时，Docker 只知道容器是否「在运行」，不知道应用是否「正常工作」。比如你的应用卡死了，进程还在，Docker 会认为它是健康的。

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' mycontainer

# 状态：starting → healthy → unhealthy
```

**实际例子：**

```dockerfile
# Python Flask 应用
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 或者安装 curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
```

---

### 1.11 LABEL — 元数据

`LABEL` 给镜像添加描述信息，方便管理和查找。

```dockerfile
LABEL maintainer="yourname@example.com"
LABEL version="1.0.0"
LABEL description="A sample web application"
LABEL org.opencontainers.image.source="https://github.com/user/repo"
```

```bash
# 查看镜像的 labels
docker inspect --format='{{json .Config.Labels}}' myimage | python -m json.tool
```

---

### 1.12 指令速查表

| 指令 | 用途 | 构建时 | 运行时 |
|------|------|--------|--------|
| `FROM` | 指定基础镜像 | ✅ | — |
| `RUN` | 执行命令 | ✅ | — |
| `COPY` | 复制文件 | ✅ | — |
| `ADD` | 复制文件（支持解压/URL） | ✅ | — |
| `CMD` | 默认启动命令 | — | ✅（可覆盖） |
| `ENTRYPOINT` | 固定启动入口 | — | ✅（不易覆盖） |
| `ENV` | 环境变量 | ✅ | ✅ |
| `ARG` | 构建参数 | ✅ | ❌ |
| `EXPOSE` | 声明端口 | — | 文档 |
| `WORKDIR` | 设置工作目录 | ✅ | ✅ |
| `USER` | 设置运行用户 | ✅ | ✅ |
| `HEALTHCHECK` | 健康检查 | — | ✅ |
| `LABEL` | 元数据标签 | ✅ | ✅ |

---

## 2. 多阶段构建（Multi-stage Build）

### 2.1 为什么需要多阶段构建？

**问题：** 编译应用需要很多工具（编译器、SDK），但运行时只需要编译好的二进制文件。把这些工具留在最终镜像里，就像搬家时把施工工具也搬进了新家——浪费空间。

**类比：** 多阶段构建就像先在一个「工作间」（构建阶段）里把零件组装好，然后只把成品搬到「展厅」（最终镜像）里。

### 2.2 语法

```dockerfile
# 阶段 1：构建（命名为 builder）
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp .

# 阶段 2：运行（全新的小镜像）
FROM alpine:3.19
COPY --from=builder /app/myapp /usr/local/bin/myapp
CMD ["myapp"]
```

关键点：
- 每个 `FROM` 开始一个新阶段
- `AS name` 给阶段命名
- `COPY --from=stage_name` 从其他阶段复制文件

### 2.3 实战：Go 应用的多阶段构建

Go 是最适合多阶段构建的语言，因为它编译成静态二进制文件。

```go
// main.go
package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "Hello from Go multi-stage build!")
    })
    fmt.Println("Server starting on :8080")
    http.ListenAndServe(":8080", nil)
}
```

```dockerfile
# Dockerfile
# ===== 阶段 1：构建 =====
FROM golang:1.22-alpine AS builder

WORKDIR /app

# 先复制依赖文件，利用缓存
COPY go.mod go.sum ./
RUN go mod download

# 复制源码并编译
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o server .

# ===== 阶段 2：运行 =====
FROM scratch

# 从构建阶段复制二进制文件
COPY --from=builder /app/server /server

EXPOSE 8080
CMD ["/server"]
```

```bash
# 构建并运行
docker build -t go-multi-stage .
docker run -p 8080:8080 go-multi-stage

# 查看镜像大小
docker images go-multi-stage
# 结果：约 8MB！如果不用多阶段构建，会超过 800MB
```

**`FROM scratch` 是什么？**

`scratch` 是一个空镜像，什么都没有。Go 编译出的静态二进制文件不需要任何运行时依赖，所以可以从空白镜像开始。

### 2.4 实战：Python 应用的多阶段构建

Python 的情况和 Go 不同——Python 需要运行时，但我们仍然可以把构建工具和运行环境分开。

```python
# app.py
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Python multi-stage build!"

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

```
# requirements.txt
flask==3.0.0
gunicorn==21.2.0
```

```dockerfile
# Dockerfile
# ===== 阶段 1：构建依赖 =====
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== 阶段 2：运行 =====
FROM python:3.12-slim

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

```bash
# 构建并运行
docker build -t python-multi-stage .
docker run -p 5000:5000 python-multi-stage
```

**为什么用虚拟环境？**

在多阶段构建中，虚拟环境的好处是它是一个完整的、可移植的目录。你可以直接 `COPY --from=builder /opt/venv /opt/venv`，所有依赖都在里面，干净又完整。

### 2.5 实战：Node.js 应用的多阶段构建

```javascript
// server.js
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello from Node.js multi-stage build!');
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

```json
// package.json
{
  "name": "myapp",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js",
    "build": "echo 'Build step'"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "jest": "^29.7.0"
  }
}
```

```dockerfile
# Dockerfile
# ===== 阶段 1：安装依赖 =====
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ===== 阶段 2：构建（如果需要构建步骤，如前端编译） =====
FROM node:20-alpine AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build 2>/dev/null || true

# ===== 阶段 3：生产运行 =====
FROM node:20-alpine

WORKDIR /app

# 只复制生产需要的文件
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY server.js ./

# 创建非 root 用户（node 镜像自带 node 用户）
USER node

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "server.js"]
```

```bash
# 构建并运行
docker build -t node-multi-stage .
docker run -p 3000:3000 node-multi-stage
```

### 2.6 镜像大小对比

| 语言 | 单阶段 | 多阶段 | 减少 |
|------|--------|--------|------|
| Go | ~800MB (golang:1.22) | ~8MB (scratch) | **99%** |
| Python | ~1.2GB (python:3.12) | ~150MB (python:3.12-slim) | **87%** |
| Node.js | ~1.1GB (node:20) | ~120MB (node:20-alpine) | **89%** |
| Java | ~600MB (eclipse-temurin) | ~250MB (jre-slim) | **58%** |

---

## 3. 镜像优化技巧

### 3.1 选择合适的基础镜像

```dockerfile
# ❌ 完整版，900MB
FROM python:3.12

# ✅ 精简版，130MB
FROM python:3.12-slim

# ✅ 极简版，50MB（注意兼容性）
FROM python:3.12-alpine
```

### 3.2 合并 RUN 指令

```dockerfile
# ❌ 3 层
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# ✅ 1 层
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

### 3.3 利用构建缓存

Docker 按顺序逐行构建，某一行变了就从那里开始重新构建。所以，**把变化频率低的指令放前面，变化频率高的放后面**。

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# ① 依赖文件很少变化 → 放前面，最大化缓存命中
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ② 源码经常变化 → 放后面
COPY . .

CMD ["python", "app.py"]
```

**为什么？** 如果你先 `COPY . .` 再装依赖，每次改一行代码，pip install 都要重新执行（因为 COPY . . 产生的层变了，后面的层全部重建）。

### 3.4 使用 .dockerignore

`.dockerignore` 就像 `.gitignore`，告诉 Docker 哪些文件不要复制到构建上下文中。

```
# .dockerignore
.git
.gitignore
__pycache__
*.pyc
*.pyo
.env
.venv
venv/
node_modules/
Dockerfile
docker-compose*.yml
*.md
.dockerignore
.coverage
.pytest_cache
dist/
build/
```

**为什么重要？**

1. **构建速度**：`.git` 目录可能很大，复制到构建上下文很慢
2. **镜像大小**：不需要的文件不应该进入镜像
3. **安全**：防止 `.env`、密钥文件被复制进镜像

```bash
# 查看构建上下文大小（构建时第一行会显示）
docker build -t myapp .
# Sending build context to Docker daemon  2.048kB  ← 越小越好
```

### 3.5 减少层数

每条指令（`RUN`、`COPY`、`ADD`）都会创建一个新层。合理合并指令可以减少层数。

```dockerfile
# ❌ 多个 COPY，每条一个层
COPY requirements.txt /app/
COPY app.py /app/
COPY templates/ /app/templates/
COPY static/ /app/static/

# ✅ 合并成一个 COPY（如果所有文件都需要的话）
COPY . /app/
```

### 3.6 清理不必要的文件

```dockerfile
# 在同一个 RUN 中安装并清理
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    # ... 编译步骤 ... \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# pip 安装时不缓存
RUN pip install --no-cache-dir -r requirements.txt

# npm 安装时清理缓存
RUN npm ci --production && npm cache clean --force
```

### 3.7 使用多阶段构建

这是最有效的优化手段，详见[第 2 节](#2-多阶段构建multi-stage-build)。

### 优化效果对比

```bash
# 优化前
docker images myapp:unoptimized
# REPOSITORY   TAG              SIZE
# myapp        unoptimized      1.2GB

# 优化后
docker images myapp:optimized
# REPOSITORY   TAG              SIZE
# myapp        optimized        150MB

# 大小减少约 87%！
```

---

## 4. 安全最佳实践

### 4.1 不要以 Root 运行

```dockerfile
# ❌ 以 root 运行（默认行为）
FROM python:3.12-slim
WORKDIR /app
COPY . .
CMD ["python", "app.py"]

# ✅ 以非 root 用户运行
FROM python:3.12-slim
WORKDIR /app

# 创建专用用户
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser

# 复制文件并设置权限
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

CMD ["python", "app.py"]
```

**类比：** 以 root 运行容器就像给快递员你家的万能钥匙——他只需要开门放个包裹，你却给了他所有房间的钥匙。

### 4.2 使用可信的基础镜像

```dockerfile
# ❌ 不信任的镜像
FROM randomuser/super-python

# ✅ 官方镜像
FROM python:3.12-slim

# ✅ Docker 官方认证镜像（带 Verified Publisher 标记）
FROM bitnami/python:3.12
```

**如何判断镜像是否可信？**
- Docker Hub 上找「Official Image」标记
- 查看下载量和星标数
- 检查 Dockerfile 源码是否公开
- 使用 `docker scout` 扫描安全漏洞

### 4.3 扫描镜像漏洞

```bash
# 使用 Docker Scout 扫描（Docker Desktop 自带）
docker scout cves myapp:latest

# 使用 Trivy 扫描（推荐，更全面）
# 安装 Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# 扫描镜像
trivy image myapp:latest

# 只显示高危和严重漏洞
trivy image --severity HIGH,CRITICAL myapp:latest
```

### 4.4 不要在镜像中存储密钥

```dockerfile
# ❌ 绝对不要这样做！密钥会被永久保存在镜像层中
COPY .env /app/
ENV AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE
COPY id_rsa /root/.ssh/

# ✅ 运行时注入密钥
# docker run -e DB_PASSWORD=secret myapp
# docker run -v /host/secret:/app/secret:ro myapp

# ✅ 使用 Docker secrets（Swarm 模式）
# 或使用 Kubernetes secrets

# ✅ 构建时需要密钥（如 npm install 私有包）
# 使用 BuildKit 的 secret mount
# docker build --secret id=npmrc,source=.npmrc .
RUN --mount=type=secret,id=npmrc,target=/app/.npmrc npm ci
```

```bash
# 检查镜像中是否包含敏感信息
docker history --no-trunc myapp:latest
docker inspect myapp:latest

# 搜索镜像中的字符串
docker run --rm myapp:latest grep -r "password" /app/ 2>/dev/null
```

### 4.5 使用 .dockerignore

除了优化构建速度，`.dockerignore` 还能防止敏感文件被复制进镜像。

```
# .dockerignore
.env
.env.*
*.pem
*.key
id_rsa
credentials.json
```

---

## 5. 实战示例

### 5.1 Python 应用的最佳 Dockerfile

```python
# app.py
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify(message="Hello from Python!", env=os.environ.get("ENV", "development"))

@app.route("/health")
def health():
    return jsonify(status="healthy"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
```

```
# requirements.txt
flask==3.0.0
gunicorn==21.2.0
```

```dockerfile
# Dockerfile
# ===== 阶段 1：构建依赖 =====
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装编译依赖（某些 Python 包需要编译 C 扩展）
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ===== 阶段 2：生产运行 =====
FROM python:3.12-slim

# 设置元数据
LABEL maintainer="yourname@example.com"
LABEL description="Python Flask production image"

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 创建非 root 用户
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser

# 复制应用代码
COPY --chown=appuser:appuser . .

# 切换用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

EXPOSE 5000

# 使用 gunicorn 作为生产服务器
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]
```

```bash
# 构建
docker build -t python-app:latest .

# 运行
docker run -d --name python-app \
    -p 5000:5000 \
    -e ENV=production \
    python-app:latest

# 测试
curl http://localhost:5000/
curl http://localhost:5000/health
```

### 5.2 Node.js 应用的最佳 Dockerfile

```javascript
// server.js
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.json({ message: 'Hello from Node.js!', env: process.env.NODE_ENV });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

```json
// package.json
{
  "name": "myapp",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.2"
  }
}
```

```dockerfile
# Dockerfile
# ===== 阶段 1：安装依赖 =====
FROM node:20-alpine AS deps

WORKDIR /app

# 只复制 package 文件，利用缓存
COPY package.json package-lock.json ./

# 只安装生产依赖
RUN npm ci --only=production && \
    # 单独保存生产依赖
    cp -R node_modules /prod_node_modules && \
    # 安装所有依赖（包括 devDependencies）
    npm ci

# ===== 阶段 2：生产运行 =====
FROM node:20-alpine

LABEL maintainer="yourname@example.com"
LABEL description="Node.js production image"

ENV NODE_ENV=production \
    PORT=3000

WORKDIR /app

# 只复制生产依赖
COPY --from=deps /prod_node_modules ./node_modules

# 复制应用代码
COPY --chown=node:node package.json server.js ./

# 使用 node 用户（node 镜像自带）
USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["node", "server.js"]
```

```bash
# 构建
docker build -t node-app:latest .

# 运行
docker run -d --name node-app \
    -p 3000:3000 \
    node-app:latest

# 测试
curl http://localhost:3000/
curl http://localhost:3000/health
```

### 5.3 Go 应用的最佳 Dockerfile

```go
// main.go
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "os"
)

type Response struct {
    Message string `json:"message"`
    Env     string `json:"env"`
}

func main() {
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(Response{
            Message: "Hello from Go!",
            Env:     os.Getenv("ENV"),
        })
    })

    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
    })

    fmt.Printf("Server starting on :%s\n", port)
    http.ListenAndServe(":"+port, nil)
}
```

```dockerfile
# Dockerfile
# ===== 阶段 1：构建 =====
FROM golang:1.22-alpine AS builder

# 安装 SSL 证书（如果需要 HTTPS 请求）
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

# 先复制依赖文件，利用缓存
COPY go.mod go.sum ./
RUN go mod download

# 复制源码并编译
COPY . .

# CGO_ENABLED=0：禁用 CGO，生成静态二进制
# -ldflags="-s -w"：去掉调试信息，减小体积
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -o /server .

# ===== 阶段 2：运行 =====
FROM scratch

# 从构建阶段复制必要的文件
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /server /server

# 设置环境变量
ENV PORT=8080
ENV ENV=production

EXPOSE 8080

ENTRYPOINT ["/server"]
```

```bash
# 构建
docker build -t go-app:latest .

# 运行
docker run -d --name go-app \
    -p 8080:8080 \
    -e ENV=production \
    go-app:latest

# 测试
curl http://localhost:8080/
curl http://localhost:8080/health

# 查看镜像大小（应该只有几 MB）
docker images go-app
```

### 5.4 Java 应用的最佳 Dockerfile

```java
// src/main/java/com/example/App.java
package com.example;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

public class App {
    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);

        server.createContext("/", exchange -> {
            String response = "{\"message\":\"Hello from Java!\",\"env\":\"" +
                System.getenv().getOrDefault("ENV", "development") + "\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.getBytes().length);
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        });

        server.createContext("/health", exchange -> {
            String response = "{\"status\":\"healthy\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.getBytes().length);
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        });

        System.out.println("Server starting on port " + port);
        server.start();
    }
}
```

```dockerfile
# Dockerfile（使用 Maven 构建）
# ===== 阶段 1：构建 =====
FROM maven:3.9-eclipse-temurin-21-alpine AS builder

WORKDIR /app

# 先复制 pom.xml，利用缓存
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 复制源码并打包
COPY src ./src
RUN mvn package -DskipTests -B

# ===== 阶段 2：运行 =====
FROM eclipse-temurin:21-jre-alpine

LABEL maintainer="yourname@example.com"
LABEL description="Java production image"

ENV PORT=8080

WORKDIR /app

# 创建非 root 用户
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# 从构建阶段复制 JAR 文件
COPY --from=builder /app/target/*.jar app.jar

# 切换到非 root 用户
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

EXPOSE 8080

# JVM 优化参数
ENTRYPOINT ["java", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "-jar", "app.jar"]
```

```bash
# 构建
docker build -t java-app:latest .

# 运行
docker run -d --name java-app \
    -p 8080:8080 \
    -e ENV=production \
    java-app:latest

# 测试
curl http://localhost:8080/
curl http://localhost:8080/health
```

**Java 镜像优化说明：**

| 优化项 | 说明 |
|-------|------|
| `JRE` 而非 `JDK` | JRE 只有运行时，比 JDK 小很多 |
| `Alpine` 版本 | 进一步减小体积 |
| `-XX:+UseContainerSupport` | 让 JVM 自动识别容器的 CPU 和内存限制 |
| `-XX:MaxRAMPercentage=75.0` | 限制 JVM 最大堆内存为容器内存的 75% |
| `-Djava.security.egd=...` | 加快随机数生成，避免启动慢 |

---

## 6. 常见问题和踩坑经验

### 6.1 构建缓存不生效

**问题：** 每次构建都重新执行所有步骤，很慢。

**原因：** `COPY . .` 放在了 `pip install` 前面，每次改代码都会导致后面的层全部重建。

```dockerfile
# ❌ 缓存不友好
COPY . .
RUN pip install -r requirements.txt

# ✅ 缓存友好
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### 6.2 镜像太大

**问题：** 镜像动辄 1GB+。

**排查步骤：**

```bash
# 查看镜像层
docker history myapp:latest

# 使用 dive 工具分析（强烈推荐）
# 安装：https://github.com/wagoodman/dive
dive myapp:latest
```

**常见原因和解决方案：**

| 原因 | 解决方案 |
|------|---------|
| 用了完整版基础镜像 | 换 `slim` 或 `alpine` |
| 没有多阶段构建 | 使用多阶段构建 |
| 安装了不必要的包 | 用 `--no-install-recommends` |
| 缓存文件没清理 | 同一个 RUN 中清理 |
| 复制了不需要的文件 | 添加 `.dockerignore` |

### 6.3 容器启动后立即退出

**问题：** `docker run` 后容器立刻退出了。

```bash
# 查看退出原因
docker logs mycontainer
docker inspect mycontainer | grep -A5 "State"
```

**常见原因：**

1. **CMD 使用了 Shell 格式导致前台进程丢失**

```dockerfile
# ❌ 后台运行（容器会退出）
CMD ["nginx"]  # 如果 nginx 默认 daemonize 为 true

# ✅ 前台运行
CMD ["nginx", "-g", "daemon off;"]
```

2. **主进程退出了**

```dockerfile
# ❌ 脚本执行完就退出了
CMD ["sh", "-c", "echo hello"]

# ✅ 保持运行
CMD ["python", "app.py"]  # app.py 里有 HTTP server
```

### 6.4 文件权限问题

**问题：** 切换到非 root 用户后，无法写入文件。

```dockerfile
# ❌ 文件属于 root，非 root 用户无法写入
COPY . .
USER appuser

# ✅ 先设置文件所有权，再切换用户
COPY --chown=appuser:appuser . .
USER appuser
```

### 6.5 时区问题

**问题：** 容器里的时间和宿主机不一致。

```dockerfile
# Debian/Ubuntu 基础镜像
ENV TZ=Asia/Shanghai
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Alpine 基础镜像
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apk del tzdata
```

### 6.6 DNS 解析问题

**问题：** 容器内无法访问外部网络。

```bash
# 检查 DNS
docker run --rm alpine nslookup google.com

# 手动指定 DNS
docker run --dns 8.8.8.8 myapp
```

### 6.7 构建上下文太大

**问题：** `docker build` 时发送到 Docker daemon 的文件太多，很慢。

```bash
# 看到这个提示说明上下文太大
# Sending build context to Docker daemon  2.1GB

# 解决：添加 .dockerignore
echo ".git" >> .dockerignore
echo "node_modules" >> .dockerignore
echo "venv" >> .dockerignore
```

### 6.8 ADD 和 COPY 的坑

```dockerfile
# ADD 的隐藏行为：自动解压
ADD app.tar.gz /app/
# 这会解压 app.tar.gz 到 /app/，而不是复制 tar 文件！

# 如果你确实想复制 tar 文件本身
COPY app.tar.gz /app/
```

---

## 附录：Dockerfile 模板

### 通用 Python 模板

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN useradd -r -s /bin/false appuser
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

### 通用 Node.js 模板

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production

FROM node:20-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --chown=node:node . .
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

### 通用 Go 模板

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /server .

FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

---

> **总结：** 好的 Dockerfile = 合适的基础镜像 + 利用缓存 + 多阶段构建 + 非 root 运行 + 不含敏感信息。记住这些原则，你就能构建出小、快、安全的镜像。
