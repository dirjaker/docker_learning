# 示例 04：Docker Compose 完整示例 🔢

演示如何使用 Docker Compose 编排 Flask + Redis 应用，包含数据持久化、环境变量管理、健康检查等最佳实践。

## 学习目标

- 深入理解 Docker Compose 的配置选项
- 学会使用环境变量和 `.env` 文件
- 理解数据卷（Volumes）的持久化
- 学会配置健康检查
- 学会使用 Profiles 按需启动服务

## 架构图

```
┌──────────────┐     ┌──────────────┐
│  Flask App   │────▶│    Redis     │
│   :5000      │     │    :6379     │
└──────────────┘     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │  redis-data  │
                     │  (Volume)    │
                     └──────────────┘
```

## 文件结构

```
04-docker-compose/
├── docker-compose.yml      # 编排配置
├── .env                    # 环境变量
└── app/
    ├── app.py              # Flask 应用
    ├── Dockerfile
    └── requirements.txt
```

## 快速开始

### 1. 启动服务

```bash
# 基础启动
docker-compose up -d

# 启动时包含调试工具
docker-compose --profile debug up -d
```

### 2. 访问应用

- **计数器应用**: http://localhost:5000
- **Redis Commander**（如启用）: http://localhost:8081

### 3. 测试 API

```bash
# 获取当前计数
curl http://localhost:5000/api/count

# 重置计数器
curl -X POST http://localhost:5000/api/reset

# 健康检查
curl http://localhost:5000/api/health
```

### 4. 查看服务状态

```bash
docker-compose ps
docker-compose logs -f app
```

### 5. 停止服务

```bash
docker-compose down
# 保留数据卷
docker-compose down
# 删除数据卷
docker-compose down -v
```

## 关键配置解析

### 环境变量管理

```yaml
environment:
  - REDIS_HOST=redis        # 直接设置
  - FLASK_ENV=${FLASK_ENV}  # 从 .env 文件读取
env_file:
  - .env                    # 加载整个 .env 文件
```

### 健康检查

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s    # 每 10 秒检查一次
  timeout: 5s      # 超时时间
  retries: 5       # 重试次数
```

### 数据持久化

```yaml
volumes:
  redis-data:
    driver: local
```

### Profiles（按需服务）

```yaml
profiles:
  - debug  # 只在指定 profile 时启动
```

```bash
docker-compose --profile debug up -d
```

## 下一步

继续学习 [05-k8s-basic](../05-k8s-basic/)，了解 Kubernetes 基础。
