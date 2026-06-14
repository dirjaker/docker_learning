# Docker Compose 命令与配置速查表

## 1. 基本命令

### 生命周期管理
```bash
# 启动所有服务（后台）
docker compose up -d

# 启动指定服务（及其依赖）
docker compose up -d web redis

# 强制重建容器
docker compose up -d --build
docker compose up -d --force-recreate

# 停止所有服务
docker compose down

# 停止并删除卷和网络
docker compose down -v --remove-orphans

# 重启服务
docker compose restart
docker compose restart web

# 停止/启动（不删除容器）
docker compose stop
docker compose start
docker compose pause
docker compose unpause
```

### 查看状态
```bash
# 查看服务状态
docker compose ps
docker compose ps -a

# 查看日志
docker compose logs
docker compose logs -f                  # 实时跟踪所有服务
docker compose logs -f web              # 跟踪指定服务
docker compose logs --tail 50 web       # 最后 50 行

# 查看资源使用
docker compose top                      # 各服务的进程
```

### 执行命令
```bash
# 在运行中的服务容器内执行命令
docker compose exec web bash
docker compose exec web sh
docker compose exec web python manage.py migrate

# 一次性运行命令（创建新容器）
docker compose run --rm web python manage.py test
docker compose run --rm web sh -c "echo hello"

# 扩缩容（同服务多实例）
docker compose up -d --scale web=3
```

### 其他
```bash
# 验证配置文件
docker compose config
docker compose config --services       # 列出所有服务名

# 拉取最新镜像
docker compose pull

# 查看镜像
docker compose images

# 删除已停止的服务容器
docker compose rm
docker compose rm -f                   # 强制
```

---

## 2. docker-compose.yml 配置速查

### 基本结构
```yaml
version: "3.8"

services:
  web:
    # ...服务配置

  db:
    # ...服务配置

volumes:
  db-data:

networks:
  app-net:
```

### Service 配置项

#### 镜像与构建
```yaml
services:
  # 方式 1：使用已有镜像
  redis:
    image: redis:7-alpine

  # 方式 2：从 Dockerfile 构建
  web:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        VERSION: "1.0"
      target: production        # 多阶段构建目标
    image: myapp:1.0            # 构建后的镜像名称
```

#### 端口映射
```yaml
services:
  web:
    ports:
      - "8080:80"               # 宿主机:容器
      - "443:443"
      - "127.0.0.1:3000:3000"  # 绑定本地地址
      - "9090-9091:8080-8081"  # 端口范围
    expose:
      - "3000"                  # 仅对其他服务暴露
```

#### 环境变量
```yaml
services:
  web:
    # 方式 1：直接定义
    environment:
      - APP_ENV=production
      - DB_HOST=db
    # 方式 2：对象格式
    environment:
      APP_ENV: production
      DB_HOST: db
    # 方式 3：从文件加载
    env_file:
      - .env
      - .env.production
```

#### 卷挂载
```yaml
services:
  web:
    volumes:
      - ./src:/app/src              # bind mount
      - app-data:/app/data          # named volume
      - /tmp/cache:/cache           # 绝对路径
      - ./nginx.conf:/etc/nginx/nginx.conf:ro  # 只读挂载

volumes:
  app-data:                         # 声明 named volume
```

#### 网络配置
```yaml
services:
  web:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend
    # 指定静态 IP
    networks:
      backend:
        ipv4_address: 172.20.0.10

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### 依赖与启动顺序
```yaml
services:
  web:
    depends_on:
      db:
        condition: service_healthy   # 等 db 健康检查通过
      redis:
        condition: service_started   # 等 redis 启动
  db:
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

#### 重启策略
```yaml
services:
  web:
    restart: no                # 默认，不重启
    restart: always            # 总是重启
    restart: on-failure        # 非 0 退出码时重启
    restart: unless-stopped    # 除非手动停止
```

#### 资源限制
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: "1.5"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M
      replicas: 3              # 副本数
```

#### 日志配置
```yaml
services:
  web:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 3. 多文件与环境切换

```bash
# 指定配置文件
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 指定项目名称
docker compose -p myproject up -d
```

### 开发 vs 生产配置覆盖

**docker-compose.yml**（基础）
```yaml
services:
  web:
    build: .
    ports:
      - "80:80"
    environment:
      - APP_ENV=development
```

**docker-compose.prod.yml**（生产覆盖）
```yaml
services:
  web:
    image: myapp:1.0              # 用预构建镜像
    restart: always
    environment:
      - APP_ENV=production
    deploy:
      resources:
        limits:
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "10m"
```

---

## 4. 常用配置模板

### Web + DB + Redis
```yaml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "8080:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  pg-data:
```

### Nginx 反向代理 + 应用
```yaml
version: "3.8"
services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    restart: unless-stopped

  app:
    build: .
    expose:
      - "3000"
    restart: unless-stopped
```
