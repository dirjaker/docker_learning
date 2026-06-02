# 05 - Docker Compose 入门

## 一、什么是 Docker Compose？

Docker Compose 是 Docker 官方提供的**多容器编排工具**。它允许你用一个 YAML 文件来定义和管理多个相互关联的容器，然后用一条命令把它们全部启动、停止或销毁。

简单来说：
- **Docker** = 管理单个容器
- **Docker Compose** = 管理多个容器组成的"应用栈"

---

## 二、为什么需要 Docker Compose？

想象你要搭建一个 Web 应用，需要：
- 一个 Nginx 反向代理
- 一个 Node.js 后端
- 一个 Redis 缓存
- 一个 PostgreSQL 数据库

**不用 Compose 的痛苦：**

```bash
# 创建网络
docker network create myapp

# 启动数据库
docker run -d --name postgres --network myapp \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15

# 启动 Redis
docker run -d --name redis --network myapp redis:7

# 启动后端（依赖上面两个）
docker run -d --name backend --network myapp \
  -e DATABASE_URL=postgres://postgres:secret@postgres:5432/mydb \
  -e REDIS_URL=redis://redis:6379 \
  -p 3000:3000 \
  my-backend:latest

# 启动 Nginx（依赖后端）
docker run -d --name nginx --network myapp \
  -p 80:80 \
  -v ./nginx.conf:/etc/nginx/nginx.conf \
  nginx:latest
```

每次启动要敲 5 条命令，停止又要 5 条，还容易搞错顺序。

**用 Compose 的优雅：**

```bash
docker compose up -d
# 一条命令，全部搞定！
```

---

## 三、Compose vs docker run 的区别

| 对比项 | `docker run` | `docker compose` |
|--------|-------------|-----------------|
| 容器数量 | 一次一个 | 一次全部 |
| 配置管理 | 参数散落在命令行 | 集中在 YAML 文件 |
| 网络 | 需手动创建和连接 | 自动创建和连接 |
| 依赖管理 | 需自己控制顺序 | `depends_on` 自动处理 |
| 版本控制 | 不方便 | YAML 文件可提交到 Git |
| 可复现性 | 命令容易遗漏 | 一份文件，到处运行 |

---

## 四、安装 Docker Compose

### Docker Desktop（Mac/Windows）

Docker Compose **已经内置**在 Docker Desktop 中，安装完 Docker Desktop 就自动可用。

### Linux 服务器

Docker Compose V2 已作为 Docker CLI 插件内置。安装 Docker Engine 后通常自带：

```bash
# 验证安装
docker compose version
# 输出类似：Docker Compose version v2.27.0

# 注意：V2 命令格式是 docker compose（空格）
# 老版本 V1 是 docker-compose（连字符）
```

如果发现没有，可以手动安装插件：

```bash
# 下载 Docker Compose 插件
DOCKER_COMPOSE_VERSION=v2.27.0
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# 验证
docker compose version
```

> **⚠️ 注意：** `docker-compose`（连字符）是 V1 的旧命令格式，`docker compose`（空格）是 V2 的新格式。V1 已经停止维护，建议统一使用 V2 格式。

---

## 五、docker-compose.yml 语法详解

### 5.1 基本结构

```yaml
version: "3.8"          # Compose 文件版本（V2 可省略）

services:                # 服务定义（核心）
  web:
    image: nginx:latest
    ports:
      - "80:80"

networks:                # 自定义网络（可选）
  mynet:
    driver: bridge

volumes:                 # 自定义卷（可选）
  dbdata:
```

一个 Compose 文件包含三个顶级元素：
1. **services**（必需）—— 定义要运行的容器
2. **networks**（可选）—— 定义网络
3. **volumes**（可选）—— 定义持久化卷

### 5.2 version — 版本声明

```yaml
version: "3.8"
```

- 指定 Compose 文件格式的版本
- **V2 版的 Compose CLI 可以省略此字段**，会自动检测
- 常见版本：`"3.0"` ~ `"3.8"`
- 推荐写上，明确兼容性

### 5.3 services — 服务定义

`services` 是整个文件的核心，每个 key 代表一个服务（即一组容器）。

#### image — 使用现有镜像

```yaml
services:
  redis:
    image: redis:7-alpine
```

#### build — 从 Dockerfile 构建

```yaml
services:
  app:
    build: .                    # 使用当前目录的 Dockerfile

  api:
    build:
      context: ./api            # 构建上下文路径
      dockerfile: Dockerfile.dev  # 指定 Dockerfile 文件名
      args:                     # 构建参数
        NODE_ENV: development

  # 可以同时指定 build 和 image
  web:
    build: ./frontend
    image: myapp/frontend:v1   # 构建后打上这个标签
```

#### ports — 端口映射

```yaml
services:
  web:
    ports:
      - "80:80"           # 宿主机端口:容器端口
      - "443:443"
      - "8080:3000"       # 宿主机 8080 映射到容器 3000
      - "127.0.0.1:3000:3000"  # 只绑定本地回环地址
      - "3000-3005:3000-3005"  # 端口范围映射
```

> **⚠️ 踩坑提醒：** 端口号一定要用引号包裹！`"8080:3000"` ✅，`8080:3000` ❌。不加引号时，YAML 可能把 `8080:3000` 解析为其他类型导致报错。

#### volumes — 卷挂载

```yaml
services:
  db:
    volumes:
      # 命名卷（持久化数据）
      - dbdata:/var/lib/postgresql/data
      # 绑定挂载（开发时用）
      - ./config:/etc/app/config
      # 只读挂载
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

#### environment — 环境变量

```yaml
services:
  db:
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=myapp
    # 或者用映射语法
    # environment:
    #   POSTGRES_PASSWORD: secret
    #   POSTGRES_DB: myapp
```

#### env_file — 环境变量文件

当环境变量很多时，可以放到单独文件中：

```yaml
services:
  app:
    env_file:
      - .env              # 默认路径
      - .env.production   # 可以多个
```

对应的 `.env` 文件：

```bash
# .env
DATABASE_URL=postgres://postgres:secret@db:5432/myapp
REDIS_URL=redis://redis:6379
APP_SECRET=my-super-secret-key
```

> **⚠️ 注意：** `env_file` 和 `environment` 都可以设置环境变量。如果两者有同名变量，`environment` 的值优先级更高。

#### depends_on — 依赖关系

```yaml
services:
  app:
    image: my-app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15

  redis:
    image: redis:7
```

`depends_on` 还支持更精确的健康检查等待：

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy    # 等 db 健康后再启动
      redis:
        condition: service_started    # 等 redis 启动即可（默认）

  db:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

> **⚠️ 踩坑提醒：** `depends_on` 默认只保证容器"已启动"，不保证服务"已就绪"。数据库容器启动后还需要初始化时间。生产环境务必配合 `healthcheck` 使用！

#### restart — 重启策略

```yaml
services:
  app:
    restart: unless-stopped
```

| 策略 | 说明 |
|------|------|
| `no` | 默认，不自动重启 |
| `always` | 总是重启，包括手动停止后 |
| `on-failure` | 仅非正常退出时重启 |
| `unless-stopped` | 总是重启，除非手动停止（推荐） |

#### command — 覆盖启动命令

```yaml
services:
  app:
    image: node:18
    command: npm run dev          # 覆盖默认 CMD
    # 或者用数组格式
    # command: ["npm", "run", "dev"]
```

#### healthcheck — 健康检查

```yaml
services:
  db:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s       # 检查间隔
      timeout: 5s         # 超时时间
      retries: 5          # 重试次数
      start_period: 30s   # 启动等待时间
```

常见的健康检查示例：

```yaml
# Redis
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s

# Nginx
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/"]
  interval: 30s

# 通用 HTTP 服务
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/health"]
  interval: 15s
```

#### networks — 服务的网络配置

```yaml
services:
  web:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend    # db 只在 backend 网络，web 访问不到 db 的直接端口

networks:
  frontend:
  backend:
```

通过分离网络，可以实现服务间的**网络隔离**。

### 5.4 networks — 顶层网络定义

```yaml
networks:
  # 默认桥接网络
  mynet:
    driver: bridge

  # 自定义子网
  appnet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

  # 使用已存在的外部网络
  existing-net:
    external: true
```

### 5.5 volumes — 顶层卷定义

```yaml
volumes:
  # 普通命名卷
  dbdata:

  # 使用已存在的外部卷
  external-vol:
    external: true

  # 带驱动选项的卷
  logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/log/myapp
```

---

## 六、Compose 常用命令

> **注意：** 以下命令使用 V2 格式（`docker compose`），如果用 V1 请替换为 `docker-compose`。

### 6.1 docker compose up — 启动

```bash
# 前台启动（可看日志，Ctrl+C 停止）
docker compose up

# 后台启动（最常用）
docker compose up -d

# 启动前先重新构建镜像
docker compose up --build

# 只启动指定服务及其依赖
docker compose up -d db redis

# 强制重新创建容器（即使配置没变）
docker compose up -d --force-recreate

# 不使用缓存重新构建
docker compose up -d --build --no-cache
```

### 6.2 docker compose down — 停止并清理

```bash
# 停止并删除容器、默认网络
docker compose down

# 同时删除命名卷（⚠️ 数据会丢失！）
docker compose down -v

# 同时删除关联的镜像
docker compose down --rmi all

# 只删除本地构建的镜像
docker compose down --rmi local
```

> **⚠️ 重要提醒：** `docker compose down` 会删除容器，但**不会**删除命名卷（除非加 `-v`）。你的数据库数据是安全的。

### 6.3 docker compose ps — 查看状态

```bash
# 查看当前项目的服务状态
docker compose ps

# 包含已停止的服务
docker compose ps -a

# 只显示容器 ID（便于管道操作）
docker compose ps -q

# JSON 格式输出
docker compose ps --format json
```

输出示例：

```
NAME                IMAGE              COMMAND              SERVICE   CREATED         STATUS          PORTS
myapp-web-1         nginx:latest       "/docker-entry..."   web       2 minutes ago   Up 2 minutes    0.0.0.0:80->80/tcp
myapp-db-1          postgres:15        "docker-entry..."    db        2 minutes ago   Up (healthy)    5432/tcp
myapp-redis-1       redis:7            "docker-entry..."    redis     2 minutes ago   Up 2 minutes    6379/tcp
```

### 6.4 docker compose logs — 查看日志

```bash
# 查看所有服务的日志
docker compose logs

# 实时跟踪日志（类似 tail -f）
docker compose logs -f

# 查看指定服务的日志
docker compose logs -f web

# 只看最后 100 行
docker compose logs --tail 100

# 显示时间戳
docker compose logs -f -t

# 多个服务的日志
docker compose logs -f web app
```

### 6.5 docker compose exec — 进入运行中的容器

```bash
# 进入容器的交互式 Shell
docker compose exec db bash

# 执行单条命令
docker compose exec db psql -U postgres

# 以 root 用户进入
docker compose exec -u root web sh

# 指定工作目录
docker compose exec -w /app app npm test
```

> **⚠️ 注意：** `exec` 只能操作正在运行的容器。如果容器已停止，用 `docker compose run` 来启动临时容器。

### 6.6 docker compose build — 构建镜像

```bash
# 构建所有服务的镜像
docker compose build

# 构建指定服务
docker compose build web

# 不使用缓存
docker compose build --no-cache

# 构建前先拉取最新基础镜像
docker compose build --pull
```

### 6.7 docker compose pull — 拉取镜像

```bash
# 拉取所有服务的镜像
docker compose pull

# 拉取指定服务
docker compose pull redis

# 并行拉取（更快）
docker compose pull --parallel
```

### 6.8 docker compose restart — 重启

```bash
# 重启所有服务
docker compose restart

# 重启指定服务
docker compose restart web

# 指定超时时间（秒）
docker compose restart -t 5 web
```

### 6.9 docker compose run — 运行一次性命令

```bash
# 在 app 服务中运行一条命令（会创建新容器）
docker compose run app npm test

# 运行后自动删除容器
docker compose run --rm app npm install

# 不启动依赖服务
docker compose run --no-deps app echo "hello"

# 使用指定端口
docker compose run -p 9090:9090 app
```

> **`run` vs `exec` 的区别：**
> - `exec`：在**已运行**的容器中执行命令
> - `run`：**创建新容器**来执行命令（开发和测试常用）

### 6.10 docker compose scale — 扩容

```bash
# 启动 3 个 web 实例（旧语法）
docker compose up -d --scale web=3

# 或使用 deploy.replicas（推荐，在 YAML 中配置）
# services:
#   web:
#     deploy:
#       replicas: 3
```

> **⚠️ 注意：** 扩容时如果服务映射了固定宿主机端口（如 `80:80`），会因为端口冲突失败。需要用端口范围或反向代理配合。

### 6.11 其他实用命令

```bash
# 查看服务进程详情
docker compose top

# 查看资源使用情况
docker compose stats

# 暂停所有服务（冻结进程）
docker compose pause
docker compose unpause

# 停止所有服务（不删除容器）
docker compose stop

# 启动已停止的容器
docker compose start

# 验证 YAML 文件语法
docker compose config

# 查看服务的端口映射
docker compose port web 80

# 查看镜像列表
docker compose images
```

---

## 七、实战：Web + Redis + PostgreSQL

下面我们搭建一个完整的 Web 应用栈：
- **Python Flask** 应用（Web 服务）
- **Redis**（缓存/计数器）
- **PostgreSQL**（数据库）

### 7.1 项目结构

```
myproject/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── .env.example
```

### 7.2 Flask 应用代码

```python
# app/app.py
import os
from flask import Flask, jsonify
import redis
import psycopg2

app = Flask(__name__)

# 从环境变量读取配置
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://postgres:secret@db:5432/myapp")

# Redis 连接
r = redis.from_url(REDIS_URL, decode_responses=True)

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def index():
    # 访问计数
    count = r.incr("visit_count")
    return jsonify({
        "message": "Hello from Docker Compose!",
        "visit_count": count
    })

@app.route("/health")
def health():
    try:
        r.ping()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route("/users")
def users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"users": rows})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

```txt
# app/requirements.txt
flask==3.0.0
redis==5.0.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
```

### 7.3 Dockerfile

```dockerfile
# app/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 先复制依赖文件（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制源代码
COPY . .

EXPOSE 5000

# 生产环境用 gunicorn，开发环境用 flask 内置服务器
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:app"]
```

### 7.4 环境变量文件

```bash
# .env（实际环境，不要提交到 Git！）
POSTGRES_USER=postgres
POSTGRES_PASSWORD=supersecret123
POSTGRES_DB=myapp
REDIS_PASSWORD=redis_secret
APP_SECRET_KEY=my-production-secret-key
FLASK_ENV=production
```

```bash
# .env.example（模板，提交到 Git 供参考）
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me
POSTGRES_DB=myapp
REDIS_PASSWORD=change_me
APP_SECRET_KEY=change_me
FLASK_ENV=development
```

### 7.5 完整的 docker-compose.yml

```yaml
version: "3.8"

services:
  # ============ Web 应用 ============
  web:
    build:
      context: ./app
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - APP_SECRET_KEY=${APP_SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - appnet
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============ PostgreSQL 数据库 ============
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    restart: unless-stopped
    networks:
      - appnet
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  # ============ Redis 缓存 ============
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redisdata:/data
    restart: unless-stopped
    networks:
      - appnet
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

# ============ 网络定义 ============
networks:
  appnet:
    driver: bridge

# ============ 卷定义 ============
volumes:
  pgdata:
  redisdata:
```

### 7.6 初始化 SQL（可选）

```sql
-- init.sql（放在项目根目录，会在数据库首次初始化时自动执行）
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES
    ('张三', 'zhangsan@example.com'),
    ('李四', 'lisi@example.com'),
    ('王五', 'wangwu@example.com');
```

### 7.7 启动和验证

```bash
# 进入项目目录
cd myproject

# 检查配置是否有语法错误
docker compose config

# 后台启动
docker compose up -d

# 查看启动状态
docker compose ps

# 实时查看日志
docker compose logs -f

# 等所有服务 healthy 后测试
curl http://localhost:5000/
# {"message":"Hello from Docker Compose!","visit_count":1}

curl http://localhost:5000/users
# {"users":[[1,"张三","zhangsan@example.com","2024-01-01..."], ...]}

curl http://localhost:5000/health
# {"status":"healthy"}

# 多次访问，观察计数递增
curl http://localhost:5000/
# {"message":"Hello from Docker Compose!","visit_count":3}
```

### 7.8 日常操作

```bash
# 查看实时日志（只看 web 服务）
docker compose logs -f web

# 进入数据库容器执行 SQL
docker compose exec db psql -U postgres -d myapp

# 进入 Redis 容器
docker compose exec redis redis-cli

# 进入 Web 应用容器
docker compose exec web bash

# 重启单个服务
docker compose restart web

# 重新构建并启动（代码修改后）
docker compose up -d --build web

# 停止所有服务
docker compose down

# 停止并删除所有数据（⚠️ 危险！）
docker compose down -v
```

---

## 八、常见问题和踩坑经验

### 🐛 问题 1：服务启动顺序问题

**现象：** 应用启动后连接数据库失败，报 `Connection refused`。

**原因：** `depends_on` 只等容器启动，不等服务就绪。数据库容器虽然"启动了"，但 PostgreSQL 还在初始化。

**解决：**

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy   # 等健康检查通过才启动
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 30s
```

### 🐛 问题 2：环境变量不生效

**现象：** `.env` 文件里的变量在容器里没有生效。

**原因：** `docker compose` 会自动读取项目目录下的 `.env` 文件用于 **YAML 模板替换**（`${VAR}`），但不会自动把 `.env` 注入容器。需要显式使用 `env_file` 或 `environment`。

```yaml
services:
  app:
    # 方式 1：在 environment 中引用（推荐，用于 YAML 变量替换）
    environment:
      - DB_PASSWORD=${POSTGRES_PASSWORD}

    # 方式 2：直接用 env_file 注入容器
    env_file:
      - .env
```

### 🐛 问题 3：端口已被占用

**现象：** `Error: Bind for 0.0.0.0:5432 failed: port is already allocated`

**原因：** 宿主机上已经有服务占用了该端口。

**解决：**

```bash
# 查看谁占用了端口
sudo lsof -i :5432
# 或
sudo ss -tlnp | grep 5432

# 方案 1：停掉占用端口的服务
sudo systemctl stop postgresql

# 方案 2：换一个宿主机端口
ports:
  - "15432:5432"    # 用 15432 映射
```

### 🐛 问题 4：挂载卷权限问题

**现象：** 容器内应用无法写入挂载目录，报 `Permission denied`。

**原因：** 宿主机目录的所有者和容器内用户不一致。

**解决：**

```bash
# 方案 1：修改宿主机目录权限
chmod -R 777 ./data    # 开发环境凑合用

# 方案 2：在 Dockerfile 中处理
# 创建与宿主机 UID 匹配的用户
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/sh appuser
RUN chown -R appuser:appuser /app
USER appuser

# 方案 3：Compose 中指定用户
services:
  app:
    user: "1000:1000"
```

### 🐛 问题 5：容器名冲突

**现象：** `The container name "/xxx" is already in use`

**原因：** 存在同名容器（可能是之前手动 `docker run` 创建的）。

**解决：**

```bash
# 删除冲突容器
docker rm -f 容器名

# 或者 Compose 自动管理，先 down 再 up
docker compose down
docker compose up -d
```

### 🐛 问题 6：修改配置后不生效

**现象：** 修改了 `docker-compose.yml`，但 `up -d` 后没有变化。

**原因：** Compose 不会自动检测所有配置变更。

**解决：**

```bash
# 方案 1：加 --build（构建相关变更）
docker compose up -d --build

# 方案 2：先 down 再 up（配置变更）
docker compose down
docker compose up -d

# 方案 3：强制重新创建
docker compose up -d --force-recreate
```

### 🐛 问题 7：网络问题——容器间无法通信

**现象：** 容器 A ping 不到容器 B。

**原因：** 容器不在同一个网络中。

**解决：**

```yaml
# 确保需要通信的服务在同一个网络中
services:
  web:
    networks:
      - appnet
  db:
    networks:
      - appnet    # 和 web 在同一个网络

networks:
  appnet:
```

容器间通过**服务名**互相访问（不是容器名也不是 IP）：

```bash
# 在 web 容器中
ping db       # ✅ 用服务名
ping 172.20.0.3  # ❌ IP 可能变，不推荐
```

### 🐛 问题 8：磁盘空间不足

**现象：** `no space left on device`

**解决：**

```bash
# 查看 Docker 磁盘使用
docker system df

# 清理无用资源
docker system prune          # 清理停止的容器、悬空镜像、未使用的网络
docker system prune -a       # 更彻底（⚠️ 删除所有未使用的镜像）
docker system prune --volumes # 包含未使用的卷（⚠️ 数据会丢！）

# 只清理悬空镜像
docker image prune
```

---

## 九、最佳实践总结

### 文件组织

```
myproject/
├── docker-compose.yml          # 主配置
├── docker-compose.override.yml # 本地开发覆盖（自动加载）
├── docker-compose.prod.yml     # 生产环境配置
├── .env                        # 环境变量（不要提交 Git）
├── .env.example                # 环境变量模板（提交 Git）
├── .gitignore                  # 忽略 .env
├── app/
│   ├── Dockerfile
│   └── ...
└── init.sql
```

```bash
# .gitignore 中加上
.env
*.log
```

### 多环境配置

```bash
# 开发环境（自动加载 docker-compose.yml + docker-compose.override.yml）
docker compose up -d

# 生产环境（显式指定文件）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

```yaml
# docker-compose.prod.yml
services:
  web:
    environment:
      - FLASK_ENV=production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
```

### 使用变量插值

```yaml
services:
  web:
    image: myapp:${APP_VERSION:-latest}   # 默认值语法 ${VAR:-默认值}
    ports:
      - "${APP_PORT:-8080}:5000"
```

### 其他建议

1. **永远不要把密码硬编码**在 YAML 中，用 `.env` + `.gitignore`
2. **生产环境**一定要配置 `healthcheck`
3. **数据库卷**一定要用命名卷（named volume），不要用绑定挂载
4. **开发环境**可以用 `watch` 模式自动重新构建：
   ```bash
   docker compose watch   # V2.22+ 支持
   ```
5. 给所有服务配置 `restart: unless-stopped`，服务器重启后自动恢复
6. 用 `docker compose config` 检查 YAML 语法后再启动
7. **日志**不要写到容器里，通过挂载卷或日志驱动收集

---

## 十、常用命令速查表

```bash
# ==================== 生命周期 ====================
docker compose up -d                    # 后台启动
docker compose up -d --build            # 构建并启动
docker compose down                      # 停止并删除容器
docker compose down -v                   # 停止并删除容器和卷
docker compose stop                      # 停止（不删除）
docker compose start                     # 启动已停止的服务
docker compose restart                   # 重启

# ==================== 查看状态 ====================
docker compose ps                        # 服务状态
docker compose ps -a                     # 包含已停止
docker compose logs -f                   # 实时日志
docker compose logs -f web               # 指定服务日志
docker compose top                       # 进程信息
docker compose stats                     # 资源使用

# ==================== 操作容器 ====================
docker compose exec web bash             # 进入容器
docker compose exec db psql -U postgres  # 执行命令
docker compose run --rm app npm test     # 一次性运行
docker compose cp web:/app/log.txt .     # 复制文件出来

# ==================== 镜像管理 ====================
docker compose build                     # 构建镜像
docker compose build --no-cache          # 无缓存构建
docker compose pull                      # 拉取镜像
docker compose push                      # 推送镜像

# ==================== 调试 ====================
docker compose config                    # 验证配置
docker compose config --services         # 列出所有服务名
docker compose images                    # 列出使用的镜像
docker compose port web 80               # 查看端口映射
```

---

> **下一篇：** [06-Dockerfile 最佳实践](./06-Dockerfile最佳实践.md)
