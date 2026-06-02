# 示例 03：多容器应用 📦

演示如何使用 Docker Compose 编排多容器应用：Web 前端 + Worker 后端 + 消息队列。

## 学习目标

- 理解微服务架构的基本概念
- 学会使用 Docker Compose 编排多容器
- 理解服务间通信（消息队列）
- 学会使用 `depends_on` 管理服务依赖
- 学会使用 `deploy.replicas` 扩展服务

## 架构图

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   用户浏览器  │────▶│   Web (Flask) │────▶│  RabbitMQ 队列   │
│             │◀────│   :5000       │     │  :5672/:15672   │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Worker x2      │
                                          │  (后台处理)       │
                                          └─────────────────┘
```

## 文件结构

```
03-multi-container/
├── docker-compose.yml      # 编排文件
├── web/
│   ├── app.py              # Flask Web 应用
│   ├── Dockerfile
│   └── requirements.txt
└── worker/
    ├── worker.py           # 后台任务处理器
    └── Dockerfile
```

## 快速开始

### 1. 启动所有服务

```bash
docker-compose up -d
```

### 2. 查看服务状态

```bash
docker-compose ps
```

### 3. 访问应用

- **Web 应用**: http://localhost:5000
- **RabbitMQ 管理界面**: http://localhost:15672 (guest/guest)

### 4. 提交测试任务

```bash
# 通过 API 提交任务
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "测试任务", "data": {"key": "value"}}'

# 查看任务状态
curl http://localhost:5000/api/tasks
```

### 5. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只看 worker 日志
docker-compose logs -f worker
```

### 6. 扩展 Worker 数量

```bash
docker-compose up -d --scale worker=4
```

### 7. 停止所有服务

```bash
docker-compose down
# 停止并删除数据卷
docker-compose down -v
```

## 关键概念

### 服务依赖

```yaml
web:
  depends_on:
    rabbitmq:
      condition: service_healthy
```

Web 服务会等待 RabbitMQ 健康检查通过后才启动。

### 服务扩展

```yaml
worker:
  deploy:
    replicas: 2
```

可以运行多个 Worker 实例来并行处理任务。

## 下一步

继续学习 [04-docker-compose](../04-docker-compose/)，了解更复杂的 Docker Compose 编排。
