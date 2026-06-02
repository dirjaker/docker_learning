# 01 - Docker 基础入门

> 🐳 从零开始，一步步掌握 Docker 的核心概念和基本操作。

---

## 目录

- [什么是 Docker？](#什么是-docker)
- [安装 Docker](#安装-docker)
- [镜像操作](#镜像操作)
- [容器操作](#容器操作)
- [Dockerfile 基础](#dockerfile-基础)
- [实战：第一个 Docker 应用](#实战第一个-docker-应用)
- [常见问题与踩坑](#常见问题与踩坑)

---

## 什么是 Docker？

### 一句话理解

Docker 是一个**打包和运行应用的工具**——它把你的应用和运行所需的一切（代码、依赖库、配置）打包成一个标准化的「集装箱」，在任何装了 Docker 的机器上都能直接运行，不会出现"在我电脑上能跑啊"的问题。

### Docker vs 虚拟机：公寓 vs 独栋别墅

要理解 Docker，最好的方式是和虚拟机（VM）做对比：

```
┌─────────────────────────────────────┐
│         虚拟机（独栋别墅）             │
│                                     │
│  ┌─────────┐ ┌─────────┐           │
│  │  App A  │ │  App B  │           │
│  │ Bins/   │ │ Bins/   │           │
│  │ Libs    │ │ Libs    │           │
│  ├─────────┤ ├─────────┤           │
│  │ Guest   │ │ Guest   │  ← 每栋别墅都有自己的地基（完整OS）│
│  │   OS    │ │   OS    │           │
│  └─────────┘ └─────────┘           │
│  ┌──────────────────────┐           │
│  │    Hypervisor        │  ← 小区物业（虚拟化层）│
│  ├──────────────────────┤           │
│  │     Host OS          │           │
│  └──────────────────────┘           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         Docker（公寓楼）              │
│                                     │
│  ┌─────────┐ ┌─────────┐           │
│  │  App A  │ │  App B  │           │
│  │ Bins/   │ │ Bins/   │           │
│  │ Libs    │ │ Libs    │           │
│  ├─────────┤ ├─────────┤           │
│  │     Docker Engine    │  ← 公寓共享地基（宿主机内核）│
│  ├──────────────────────┤           │
│  │     Host OS          │           │
│  └──────────────────────┘           │
└─────────────────────────────────────┘
```

| 对比项 | 虚拟机（别墅） | Docker（公寓） |
|--------|--------------|---------------|
| 启动速度 | 分钟级（要盖房子） | 秒级（拎包入住） |
| 占用资源 | 每个 VM 都有完整 OS，很重 | 共享宿主机内核，很轻 |
| 隔离性 | 强隔离（每栋独立） | 进程级隔离（隔墙隔音） |
| 镜像大小 | GB 级 | MB 级 |
| 密度 | 一台物理机跑几十个 VM | 一台物理机跑成百上千个容器 |

**为什么选 Docker？**
- **开发环境一致**：打包一次，到处运行
- **快速部署**：几秒启动一个服务
- **资源高效**：不浪费资源在重复的 OS 上
- **版本控制**：镜像可以版本化管理，随时回滚

### 三大核心概念

```
开发者电脑                     Docker 仓库（Registry）
┌──────────┐                 ┌──────────────────┐
│ Dockerfile│ ──build──→     │   Docker Hub      │
│           │   镜像(Image)   │   阿里云镜像仓库    │
└──────────┘      ↑          │   私有仓库(Harbor) │
                  │          └──────────────────┘
            ┌─────┴─────┐           │
            │  Image    │ ←─pull────┘
            │  (镜像)    │
            └─────┬─────┘
                  │ run
            ┌─────┴─────┐
            │ Container │  ← 运行中的实例
            │  (容器)    │
            └───────────┘
```

1. **镜像（Image）**：只读的模板，相当于"安装光盘"。比如 `nginx:latest`、`python:3.11`
2. **容器（Container）**：镜像的运行实例，相当于"正在运行的程序"。可以启动、停止、删除
3. **仓库（Registry）**：存放镜像的地方，相当于"应用商店"。最大的公共仓库是 [Docker Hub](https://hub.docker.com)

### Docker 架构：Client-Server 模型

```
┌──────────────────────────────────────────────┐
│  Docker Host                                  │
│                                               │
│  ┌──────────┐     ┌──────────────────────┐   │
│  │ Docker   │────→│   Docker Daemon      │   │
│  │ Client   │ API │   (dockerd)          │   │
│  └──────────┘     │                      │   │
│       ↑           │  ┌────────┐┌───────┐ │   │
│       │           │  │Container││Image  │ │   │
│       │           │  └────────┘└───────┘ │   │
│    用户输入        └──────────────────────┘   │
│  docker run ...                              │
└──────────────────────────────────────────────┘
```

- **Docker Client**：你输入命令的终端（`docker` 命令）
- **Docker Daemon（dockerd）**：后台服务，负责构建、运行、分发容器
- 两者通过 REST API 通信（默认走 Unix Socket `/var/run/docker.sock`）

---

## 安装 Docker

### Linux (Ubuntu) 安装

```bash
# 1. 卸载旧版本（如果有）
sudo apt-get remove docker docker-engine docker.io containerd runc

# 2. 安装依赖
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# 3. 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 4. 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
newgrp docker
```

### macOS 安装

```bash
# 方式一：Homebrew（推荐）
brew install --cask docker

# 安装后启动 Docker Desktop 应用
open /Applications/Docker.app
```

或者从 [Docker 官网](https://www.docker.com/products/docker-desktop/) 下载 Docker Desktop for Mac 安装包。

### Windows 安装

1. 从官网下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 双击安装包，按向导完成安装
3. 确保已启用 WSL 2（安装向导会自动检测和引导）

> ⚠️ Windows Home 版需要 WSL 2 后端；Windows Pro/Enterprise 也可以用 Hyper-V 后端。

### 验证安装

```bash
# 查看版本
$ docker version
Client: Docker Engine - Community
 Version:           27.5.1
 API version:       1.47
 Go version:        go1.22.11
 Git commit:        9f9e405
 Built:             Mon Jan 20 15:36:12 2026
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          27.5.1
  API version:      1.47 (minimum version 1.24)
  Go version:       go1.22.11
  Git commit:       594e0e1
  Built:            Mon Jan 20 15:36:12 2026
  OS/Arch:          linux/amd64
  Experimental:     false

# 查看系统信息
$ docker info
Client: Docker Engine - Community
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
  compose: Docker Compose (Docker Inc.)

Server:
 Containers: 3
  Running: 1
  Paused: 0
  Stopped: 2
 Images: 5
 Server Version: 27.5.1
 Storage Driver: overlay2
 ...
```

> 💡 **小技巧**：运行 `docker run hello-world` 能拉取一个测试镜像并运行，如果看到 "Hello from Docker!" 说明安装成功。

```bash
$ docker run hello-world
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
c1ec31eb5944: Pull complete
Digest: sha256:...
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```

---

## 镜像操作

### docker pull —— 拉取镜像

从仓库下载镜像到本地。

```bash
# 拉取最新版 nginx
$ docker pull nginx
Using default tag: latest
latest: Pulling from library/nginx
a2abf6c4d29d: Pull complete
a9edb18cadd1: Pull complete
589b7251471a: Pull complete
Digest: sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
Status: Downloaded newer image for nginx:latest
docker.io/library/nginx:latest

# 拉取指定版本
$ docker pull python:3.11-slim
3.11-slim: Pulling from library/python
Digest: sha256:...
Status: Downloaded newer image for python:3.11-slim

# 拉取指定平台镜像（多架构场景）
$ docker pull --platform linux/arm64 nginx:latest
```

### docker images —— 列出本地镜像

```bash
$ docker images
REPOSITORY   TAG         IMAGE ID       CREATED        SIZE
nginx        latest      a6bd71f48f68   2 weeks ago    187MB
python       3.11-slim   a3e06e4dd2ab   3 weeks ago    145MB
hello-world  latest      d2c94e258dcb   6 months ago   13.3kB

# 只显示镜像 ID
$ docker images -q
a6bd71f48f68
a3e06e4dd2ab
d2c94e258dcb

# 显示包括中间层镜像
$ docker images -a
```

### docker rmi —— 删除镜像

```bash
$ docker rmi hello-world
Untagged: hello-world:latest
Untagged: hello-world@sha256:...
Deleted: sha256:d2c94e258dcb4df7c8f9...

# 强制删除（有容器引用时也能删）
$ docker rmi -f nginx:latest

# 删除所有镜像
$ docker rmi $(docker images -q)
```

### docker tag —— 打标签

给镜像起一个新名字/版本标签（不创建新镜像，只是别名）。

```bash
# 给 nginx 打上自己的标签
$ docker tag nginx:latest myregistry.com/myproject/nginx:v1.0

$ docker images | grep nginx
nginx                    latest      a6bd71f48f68   2 weeks ago   187MB
myregistry.com/myproject/nginx   v1.0   a6bd71f48f68   2 weeks ago   187MB
# 注意 IMAGE ID 相同，说明是同一个镜像
```

### docker inspect —— 查看镜像详情

```bash
$ docker inspect nginx:latest
[
    {
        "Id": "sha256:a6bd71f48f686...",
        "RepoTags": ["nginx:latest"],
        "Architecture": "amd64",
        "Os": "linux",
        "Size": 187319756,
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:e4d0e810d54a...",
                "sha256:4713cb24eeff...",
                "sha256:5b1e27e74313..."
            ]
        }
        ...
    }
]

# 只看特定字段（用 jq 过滤）
$ docker inspect nginx:latest | jq '.[0].Size'
187319756
```

### 镜像的分层结构（Layer）

Docker 镜像由多个**只读层（Layer）**叠加而成，这是它的核心设计之一。

```
┌─────────────────────────┐
│  可写层 (Container Layer)│  ← 容器启动后添加的层
├─────────────────────────┤
│  Layer 4: COPY app.py   │  ← 你的代码
├─────────────────────────┤
│  Layer 3: RUN pip install│  ← 安装依赖
├─────────────────────────┤
│  Layer 2: RUN apt-get   │  ← 安装系统包
├─────────────────────────┤
│  Layer 1: Ubuntu 22.04  │  ← 基础镜像
└─────────────────────────┘
```

**为什么要分层？**

- **共享**：不同镜像可以共享相同的底层。比如 `python:3.11` 和 `python:3.11-slim` 可能共享同一个基础 Ubuntu 层，不用重复下载
- **缓存**：构建镜像时，如果某一层没变化，就直接用缓存，不用重新构建
- **高效存储**：同一层在本地只存一份

```bash
# 查看镜像的分层历史
$ docker history nginx:latest
IMAGE          CREATED      CREATED BY                                      SIZE      COMMENT
a6bd71f48f68   2 weeks ago  CMD ["nginx" "-g" "daemon off;"]                0B        buildkit.dockerfile.v0
<missing>      2 weeks ago  STOPSIGNAL SIGQUIT                              0B
<missing>      2 weeks ago  EXPOSE map[80/tcp:{}]                           0B
<missing>      2 weeks ago  ENTRYPOINT ["/docker-entrypoint.sh"]            0B
<missing>      2 weeks ago  COPY 30-tune-worker-processes.sh ...            4.62kB
<missing>      2 weeks ago  RUN /bin/sh -c set -x && addgroup -g 101 ...   61.1MB
<missing>      2 weeks ago  ENV NJS_MODULE_VERSION=0.8.9                    0B
<missing>      2 weeks ago  /bin/sh -c #(nop) ADD file:... in /            77.8MB
```

---

## 容器操作

### docker run —— 创建并启动容器

这是最常用的命令，选项很多，逐个来：

```bash
# 最基本的运行
$ docker run nginx
# 前台运行，Ctrl+C 停止

# -d: 后台运行（detached mode）
$ docker run -d nginx
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

# --name: 给容器起个名字
$ docker run -d --name my-nginx nginx
a1b2c3d4e5f6...

# -it: 交互式 + 终端（常用于进入容器调试）
$ docker run -it python:3.11-slim bash
root@a1b2c3d4e5f6:/# python3 --version
Python 3.11.8
root@a1b2c3d4e5f6:/# exit

# -p: 端口映射（宿主机端口:容器端口）
$ docker run -d -p 8080:80 --name web nginx
# 现在访问 http://localhost:8080 就能看到 nginx 默认页面

# -v: 挂载卷（宿主机目录:容器目录）
$ docker run -d -p 8080:80 -v /home/user/html:/usr/share/nginx/html nginx
# 宿主机的 /home/user/html 目录会映射到容器内

# --rm: 容器退出后自动删除（适合临时任务）
$ docker run --rm alpine echo "Hello, I'll be gone after this"
Hello, I'll be gone after this
# 容器已经自动删除了

# --network: 指定网络
$ docker run -d --network host nginx
# 使用宿主机网络，不需要 -p 端口映射

# 组合使用
$ docker run -d \
  --name production-nginx \
  -p 80:80 -p 443:443 \
  -v /data/nginx/conf:/etc/nginx/conf.d \
  -v /data/nginx/html:/usr/share/nginx/html \
  --restart unless-stopped \
  nginx:1.25
```

### docker ps —— 列出容器

```bash
# 列出运行中的容器
$ docker ps
CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS         PORTS                  NAMES
a1b2c3d4e5f6   nginx     "/docker-entrypoint.…"   5 minutes ago   Up 5 minutes   0.0.0.0:8080->80/tcp   web

# 列出所有容器（包括已停止的）
$ docker ps -a
CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS                     PORTS                  NAMES
a1b2c3d4e5f6   nginx          "/docker-entrypoint.…"   5 min ago       Up 5 min                   0.0.0.0:8080->80/tcp   web
b2c3d4e5f6g7   python:3.11    "python3"                10 min ago      Exited (0) 8 min ago                              romantic_tesla
c3d4e5f6g7h8   hello-world    "/hello"                 30 min ago      Exited (0) 30 min ago                             nifty_wilson

# 只显示容器 ID（常用于批量操作）
$ docker ps -q
a1b2c3d4e5f6

# 显示容器大小
$ docker ps -s
CONTAINER ID   IMAGE   ...   SIZE
a1b2c3d4e5f6   nginx   ...   1.09kB (virtual 187MB)
```

### docker start/stop/restart —— 容器生命周期

```bash
# 停止容器
$ docker stop web
web

# 启动已停止的容器
$ docker start web
web

# 重启容器
$ docker restart web
web

# 停止所有运行中的容器
$ docker stop $(docker ps -q)

# 删除所有已停止的容器
$ docker container prune
WARNING! This will remove all stopped containers.
Are you sure you want to continue? [y/N] y
Deleted Containers:
b2c3d4e5f6g7...
c3d4e5f6g7h8...
```

### docker logs —— 查看日志

```bash
# 查看容器日志
$ docker logs web
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
...
172.17.0.1 - - [01/Jun/2026:10:00:00 +0000] "GET / HTTP/1.1" 200 615

# 实时跟踪日志（类似 tail -f）
$ docker logs -f web
# Ctrl+C 退出

# 显示最后 10 行
$ docker logs --tail 10 web

# 显示时间戳
$ docker logs -t web
2026-06-01T10:00:00.123456789Z /docker-entrypoint.sh: ...

# 查看指定时间之后的日志
$ docker logs --since 2026-06-01T10:00:00 web
```

### docker exec —— 进入运行中的容器

```bash
# 进入容器的交互式 shell
$ docker exec -it web bash
root@a1b2c3d4e5f6:/# cat /etc/nginx/nginx.conf
...
root@a1b2c3d4e5f6:/# ls /usr/share/nginx/html/
index.html
root@a1b2c3d4e5f6:/# exit

# 在容器内执行单条命令（不进入交互模式）
$ docker exec web nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

# 以特定用户执行
$ docker exec -u www-data web whoami
www-data
```

### docker cp —— 文件拷贝

```bash
# 从容器拷贝文件到宿主机
$ docker cp web:/etc/nginx/nginx.conf ./nginx.conf
Successfully copied 3.58kB to /home/user/nginx.conf

# 从宿主机拷贝文件到容器
$ docker cp ./index.html web:/usr/share/nginx/html/index.html
Successfully copied 2.05kB to web:/usr/share/nginx/html/index.html
```

### docker rm —— 删除容器

```bash
# 删除已停止的容器
$ docker rm romantic_tesla
romantic_tesla

# 强制删除运行中的容器
$ docker rm -f web
web

# 删除所有已停止的容器
$ docker rm $(docker ps -aq --filter status=exited)
```

---

## Dockerfile 基础

Dockerfile 是一个文本文件，包含一系列指令，告诉 Docker **如何构建一个镜像**。

### 常用指令详解

#### FROM —— 基础镜像

每个 Dockerfile 必须以 `FROM` 开头，指定基础镜像。

```dockerfile
# 使用官方 Python 镜像
FROM python:3.11-slim

# 使用 Alpine 版本（更小）
FROM python:3.11-alpine

# 使用 scratch（空镜像，适合静态二进制）
FROM scratch
```

> 💡 **最佳实践**：尽量用 `slim` 或 `alpine` 版本，镜像更小。

#### RUN —— 执行命令

在构建过程中执行命令，每个 `RUN` 会创建新的一层。

```dockerfile
# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir flask gunicorn

# 合并多个命令减少层数（最佳实践）
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*
```

#### COPY / ADD —— 复制文件

```dockerfile
# COPY：简单复制（推荐使用）
COPY requirements.txt /app/requirements.txt
COPY . /app/

# ADD：COPY 的增强版，支持 URL 下载和自动解压 tar 包
ADD https://example.com/file.tar.gz /tmp/
ADD local-file.tar.gz /app/

# 💡 建议：优先用 COPY，只在需要自动解压时用 ADD
```

#### CMD / ENTRYPOINT —— 启动命令

```dockerfile
# CMD：容器启动时的默认命令，可被 docker run 的参数覆盖
CMD ["python", "app.py"]

# ENTRYPOINT：容器的入口点，不会被轻易覆盖
ENTRYPOINT ["python", "app.py"]

# 常见搭配：ENTRYPOINT 定义主命令，CMD 提供默认参数
ENTRYPOINT ["python"]
CMD ["app.py"]
# 这样 docker run myimage test.py 会执行 python test.py
```

| | `docker run myimage arg` | 是否可被覆盖 |
|---|---|---|
| CMD | `arg` 替换 CMD | ✅ 是 |
| ENTRYPOINT | `arg` 作为参数追加 | 需要 `--entrypoint` |

#### ENV —— 环境变量

```dockerfile
ENV APP_HOME=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 可在运行时覆盖
# docker run -e APP_HOME=/opt/app myimage
```

#### EXPOSE —— 声明端口

```dockerfile
EXPOSE 80
EXPOSE 443
EXPOSE 8080/tcp

# EXPOSE 只是声明文档，不会实际映射端口
# 实际映射需要 docker run -p
```

#### WORKDIR —— 工作目录

```dockerfile
WORKDIR /app
# 后续的 RUN、CMD、COPY 等命令都在 /app 下执行

COPY . .          # 复制到 /app/
RUN pip install . # 在 /app/ 下执行
```

### 构建镜像：docker build

```bash
# 基本构建
$ docker build -t myapp:v1.0 .
[+] Building 12.5s (8/8) FINISHED
 => [internal] load build definition from Dockerfile        0.0s
 => [internal] load .dockerignore                           0.0s
 => [internal] load metadata for docker.io/library/python:  1.2s
 => [1/4] FROM docker.io/library/python:3.11-slim@sha256:   3.1s
 => [2/4] WORKDIR /app                                      0.1s
 => [3/4] COPY requirements.txt .                           0.0s
 => [4/4] RUN pip install -r requirements.txt               7.8s
 => exporting to image                                      0.3s
 => => naming to docker.io/library/myapp:v1.0               0.0s

# 指定 Dockerfile 路径
$ docker build -f docker/Dockerfile -t myapp:v1.0 .

# 不使用缓存（完全重新构建）
$ docker build --no-cache -t myapp:v1.0 .

# 构建时传入参数
$ docker build --build-arg VERSION=1.0 -t myapp:v1.0 .
```

---

## 实战：第一个 Docker 应用

我们来打包一个简单的 Python Flask Web 应用。

### 第 1 步：创建项目结构

```
my-flask-app/
├── app.py
├── requirements.txt
└── Dockerfile
```

### 第 2 步：编写应用代码

**app.py**:
```python
from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    return f"""
    <h1>🐳 Hello Docker!</h1>
    <p>运行在容器: <strong>{hostname}</strong></p>
    <p>Python 版本: <strong>{os.sys.version}</strong></p>
    <p>环境变量 MESSAGE: <strong>{os.environ.get('MESSAGE', '未设置')}</strong></p>
    """

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**requirements.txt**:
```
flask==3.1.0
```

### 第 3 步：编写 Dockerfile

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 设置元数据
LABEL maintainer="yourname@example.com"
LABEL description="A simple Flask demo app"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 先复制依赖文件（利用缓存！）
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 再复制应用代码
COPY app.py .

# 声明端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
```

> 💡 **为什么先 COPY requirements.txt，再 COPY app.py？**
>
> 因为 Docker 会缓存每一层。如果只改了 app.py 而 requirements.txt 没变，Docker 会直接用缓存的 `pip install` 层，不用重新安装依赖，构建速度更快。

### 第 4 步：构建镜像

```bash
$ cd my-flask-app/
$ docker build -t my-flask-app:v1.0 .
[+] Building 15.3s (9/9) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/python:3.11-slim
 => [1/4] FROM docker.io/library/python:3.11-slim@sha256:...
 => [2/4] WORKDIR /app
 => [3/4] COPY requirements.txt .
 => [4/4] RUN pip install --no-cache-dir -r requirements.txt
 => [5/4] COPY app.py .
 => exporting to image
 => => naming to docker.io/library/my-flask-app:v1.0

$ docker images | grep my-flask
my-flask-app   v1.0   a1b2c3d4e5f6   10 seconds ago   145MB
```

### 第 5 步：运行容器

```bash
$ docker run -d \
  --name flask-demo \
  -p 5000:5000 \
  -e MESSAGE="你好，Docker！" \
  my-flask-app:v1.0

b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

验证：

```bash
$ curl http://localhost:5000
    <h1>🐳 Hello Docker!</h1>
    <p>运行在容器: <strong>b2c3d4e5f6g7</strong></p>
    <p>Python 版本: <strong>3.11.8</strong></p>
    <p>环境变量 MESSAGE: <strong>你好，Docker！</strong></p>

$ curl http://localhost:5000/health
{"status":"healthy"}
```

### 第 6 步：查看日志

```bash
$ docker logs flask-demo
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
Press CTRL+C to quit
172.17.0.1 - - [01/Jun/2026 10:00:00] "GET / HTTP/1.1" 200 -
172.17.0.1 - - [01/Jun/2026 10:00:05] "GET /health HTTP/1.1" 200 -
```

### 第 7 步：进入容器调试

```bash
$ docker exec -it flask-demo bash
root@b2c3d4e5f6g7:/app# ls -la
total 12
drwxr-xr-x 1 root root  120 Jun  1 10:00 .
drwxr-xr-x 1 root root 4096 Jun  1 10:00 ..
-rw-r--r-- 1 root root  456 Jun  1 10:00 app.py
-rw-r--r-- 1 root root   13 Jun  1 10:00 requirements.txt

root@b2c3d4e5f6g7:/app# python3 -c "import flask; print(flask.__version__)"
3.1.0

root@b2c3d4e5f6g7:/app# cat /etc/os-release
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
...

root@b2c3d4e5f6g7:/app# exit
```

---

## 常见问题与踩坑

### 1. 权限问题：每次都要 sudo？

**问题**：运行 `docker` 命令提示 `permission denied`

```bash
$ docker ps
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

**解决**：

```bash
# 方法一：将用户加入 docker 组（推荐，一劳永逸）
sudo usermod -aG docker $USER
# 然后重新登录或运行
newgrp docker

# 方法二：每次加 sudo（不推荐）
sudo docker ps
```

> ⚠️ 注意：加入 docker 组后，该用户等同于 root 权限，请确保只给可信用户。

### 2. 镜像拉取太慢？配置镜像加速器

**问题**：`docker pull` 速度极慢甚至超时

**解决**（以国内镜像加速器为例）：

```bash
# 编辑 /etc/docker/daemon.json
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.1panel.live"
  ]
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
$ docker info | grep -A 5 "Registry Mirrors"
 Registry Mirrors:
  https://mirror.ccs.tencentyun.com
  https://docker.1panel.live
```

> 💡 macOS / Windows：在 Docker Desktop → Settings → Docker Engine 中编辑 JSON 配置。

### 3. 容器内时区不对？

**问题**：容器内的时间比宿主机差 8 小时

```bash
# 容器内默认是 UTC 时区
$ docker exec myapp date
Mon Jun  1 02:00:00 UTC 2026
```

**解决**：

```bash
# 方法一：运行时挂载时区文件
$ docker run -d \
  -v /etc/localtime:/etc/localtime:ro \
  -v /etc/timezone:/etc/timezone:ro \
  myapp

# 方法二：设置环境变量
$ docker run -d \
  -e TZ=Asia/Shanghai \
  myapp

# 方法三：在 Dockerfile 中设置
# ENV TZ=Asia/Shanghai
# RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime
```

### 4. 容器内无法解析域名（DNS 问题）

**问题**：容器内 `curl` 外网地址报错 `Could not resolve host`

```bash
$ docker exec myapp curl -I https://baidu.com
curl: (6) Could not resolve host: baidu.com
```

**解决**：

```bash
# 方法一：指定 DNS 服务器
$ docker run -d --dns 8.8.8.8 --dns 114.114.114.114 myapp

# 方法二：全局配置 Docker DNS
# 编辑 /etc/docker/daemon.json
{
  "dns": ["8.8.8.8", "114.114.114.114"]
}
# 重启 Docker: sudo systemctl restart docker

# 方法三：检查宿主机网络是否正常
$ ping baidu.com  # 宿主机先确认网络
```

### 5. 其他常见踩坑

**容器内进程看到的是容器自己的 PID 1，不是宿主机进程**：
```bash
$ docker exec myapp ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.2  0.1  56780 23456 ?        Ss   10:00   0:01 python app.py
root        15  0.0  0.0  34568  3456 pts/0    Rs+  10:05   0:00 ps aux
```

**端口已被占用**：
```bash
$ docker run -d -p 8080:80 nginx
docker: Error response from daemon: driver failed programming external connectivity on endpoint web: Bind for 0.0.0.0:8080 failed: port is already allocated.

# 解决：换一个端口，或者先停掉占用 8080 的容器/进程
$ lsof -i :8080  # 查看谁占用了端口
```

**容器退出了怎么办？**
```bash
# 查看退出原因
$ docker ps -a
CONTAINER ID   IMAGE   ...   STATUS
a1b2c3d4e5f6   myapp   ...   Exited (137) 2 minutes ago

# Exit code 含义：
# 0   - 正常退出
# 1   - 应用错误
# 137 - 被 SIGKILL 杀掉（可能 OOM）
# 139 - 段错误 (SIGSEGV)

# 查看退出前的日志
$ docker logs --tail 50 a1b2c3d4e5f6
```

---

## 总结

到这里，你已经掌握了 Docker 的核心知识：

| 你学到了 | 关键命令 |
|---------|---------|
| Docker 是什么 | 比虚拟机更轻量的容器技术 |
| 镜像操作 | `pull`、`images`、`rmi`、`tag`、`inspect` |
| 容器操作 | `run`、`ps`、`start/stop`、`logs`、`exec`、`cp`、`rm` |
| Dockerfile | `FROM`、`RUN`、`COPY`、`CMD`、`ENV`、`EXPOSE`、`WORKDIR` |
| 构建运行 | `docker build -t name .` → `docker run -d -p` |
| 排查问题 | 权限、镜像加速、时区、DNS |

**下一步学习**：
- [02-Docker网络详解](./02-Docker网络详解.md) — 理解容器间的通信
- [03-Docker数据卷与持久化](./03-Docker数据卷与持久化.md) — 数据不丢失
- [04-Docker Compose](./04-Docker-Compose.md) — 多容器编排
