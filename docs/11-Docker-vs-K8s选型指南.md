# 11. Docker vs Kubernetes 选型指南

## 1. 三者关系与定位

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes                            │
│   多节点编排 · 自动扩缩容 · 自愈 · 滚动更新 · 服务发现    │
│                                                         │
│   ┌───────────────────────────────────────────────────┐ │
│   │              Docker Compose                       │ │
│   │   单机多容器编排 · 声明式配置 · 一键启停            │ │
│   │                                                   │ │
│   │   ┌─────────────────────────────────────────────┐ │ │
│   │   │              Docker Engine                  │ │ │
│   │   │   容器运行时 · 镜像构建 · 基础网络/存储      │ │ │
│   │   └─────────────────────────────────────────────┘ │ │
│   └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

| 工具 | 一句话定位 | 核心价值 |
|------|-----------|---------|
| **Docker** | 容器运行时 + 构建工具 | "把应用打包成容器" |
| **Docker Compose** | 单机多容器编排 | "一条命令启动整个开发环境" |
| **Kubernetes** | 分布式容器编排平台 | "在生产环境大规模管理容器" |

> **关键理解**：三者不是竞争关系，而是层层递进。Docker 是基础，Compose 简化本地多容器管理，K8s 解决生产环境的复杂编排问题。

---

## 2. 能力对比

### 2.1 功能对比表

| 能力 | Docker | Docker Compose | Kubernetes |
|------|--------|----------------|------------|
| 容器构建 | ✅ docker build | ✅ (调用 Docker) | ❌ (依赖外部) |
| 容器运行 | ✅ | ✅ | ✅ |
| 多容器编排 | ❌ 手动管理 | ✅ 声明式 YAML | ✅ 声明式 YAML |
| 多节点部署 | ❌ | ❌ 单机 | ✅ |
| 自动扩缩容 | ❌ | ❌ | ✅ HPA/VPA |
| 自动故障恢复 | ❌ | ✅ restart policy | ✅ 自愈机制 |
| 滚动更新 | ❌ | ❌ | ✅ |
| 服务发现/负载均衡 | ❌ | ✅ 基础 DNS | ✅ Service/Ingress |
| 配置/密钥管理 | 基础 env | .env 文件 | ✅ ConfigMap/Secret |
| 存储编卷 | ✅ volume | ✅ volume | ✅ PV/PVC/StorageClass |
| 网络策略 | 基础 bridge | ✅ 自定义网络 | ✅ NetworkPolicy |
| RBAC 权限控制 | ❌ | ❌ | ✅ |
| 命名空间隔离 | ❌ | ❌ | ✅ |
| 监控/日志集成 | 基础 | 基础 | ✅ 生态丰富 |
| 安装复杂度 | ⭐ | ⭐ | ⭐⭐⭐⭐ |
| 学习曲线 | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

### 2.2 适用场景对比

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 本地开发单个应用 | Docker | 最简单直接 |
| 本地开发全栈应用 | Docker Compose | 一键启动前后端 + 数据库 |
| CI/CD 流水线 | Docker + Compose | 构建镜像，Compose 跑测试环境 |
| 小团队内部工具 | Docker Compose | 足够简单，单机够用 |
| 中小项目生产部署 | Docker Compose 或轻量 K8s | 视复杂度而定 |
| 大规模生产系统 | Kubernetes | 高可用、自动扩缩、滚动更新 |
| 多租户 SaaS 平台 | Kubernetes | 命名空间隔离、RBAC、多团队 |
| 混合云/多云部署 | Kubernetes | 抽象底层基础设施 |

---

## 3. 选型决策树

```
你要部署多少个服务？
│
├── 只有 1 个 → Docker 直接运行
│   docker run -d -p 8080:80 myapp
│
├── 多个服务，跑在单台机器上
│   │
│   ├── 开发/测试环境 → Docker Compose ✅
│   │
│   └── 生产环境？
│       │
│       ├── 流量小、容错要求低 → Docker Compose + restart policy
│       │
│       └── 流量大、需要高可用 → Kubernetes
│
└── 多台机器 / 需要弹性伸缩 → Kubernetes ✅
```

### 3.1 什么时候从 Compose 迁移到 K8s？

当出现以下信号时，说明该考虑 Kubernetes 了：

| 信号 | 说明 |
|------|------|
| 📈 流量增长 | 单机扛不住，需要水平扩展 |
| 🔴 停机成本高 | 需要零停机部署、自动故障恢复 |
| 🖥️ 一台机器不够 | 服务多到需要跨机器部署 |
| 👥 团队增长 | 多团队需要隔离和独立部署 |
| 🌍 多环境 | 需要统一管理 dev/staging/prod |
| 📋 合规要求 | 需要 RBAC、审计日志、网络策略 |

---

## 4. 迁移指南：Compose → Kubernetes

### 4.1 使用 Kompose 自动转换

[Kompose](https://kompose.io/) 是官方提供的转换工具：

```bash
# 安装 Kompose
curl -L https://github.com/kubernetes/kompose/releases/latest/download/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/

# 转换
kompose convert -f docker-compose.yml

# 直接部署到 K8s 集群
kompose up -f docker-compose.yml
```

转换映射关系：

| Compose 概念 | Kubernetes 对应 |
|-------------|-----------------|
| service | Deployment + Service |
| volumes | PersistentVolumeClaim |
| network | (通常需手动处理) |
| environment | ConfigMap / Secret |
| ports | Service.spec.ports |
| depends_on | initContainers / 就绪探针 |
| restart: always | restartPolicy: Always |

### 4.2 手动迁移示例

**Compose 版本：**
```yaml
services:
  web:
    image: nginx:1.25
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    environment:
      - APP_ENV=production
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Kubernetes 版本：**
```yaml
# web-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3              # Compose 没有这个
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.25
          ports:
            - containerPort: 80
          env:
            - name: APP_ENV
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: APP_ENV
          volumeMounts:
            - name: html
              mountPath: /usr/share/nginx/html
          readinessProbe:       # 替代 depends_on
            httpGet:
              path: /
              port: 80
      volumes:
        - name: html
          persistentVolumeClaim:
            claimName: web-html

---
# web-service.yml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80

---
# configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
```

### 4.3 迁移注意事项

| 方面 | Compose 做法 | K8s 做法 |
|------|-------------|---------|
| **环境变量** | `.env` 文件 | ConfigMap + Secret |
| **数据持久化** | bind mount / named volume | PV + PVC + StorageClass |
| **服务间通信** | 服务名直接访问 | Service DNS (`svc-name.namespace.svc.cluster.local`) |
| **启动顺序** | `depends_on` | initContainers / readinessProbe |
| **配置文件挂载** | volume mount | ConfigMap 挂载 |
| **日志收集** | `docker logs` | DaemonSet + EFK/Loki |
| **健康检查** | (可选) healthcheck | livenessProbe + readinessProbe |

---

## 5. 成本对比

### 5.1 学习成本

| 项目 | Docker | Docker Compose | Kubernetes |
|------|--------|----------------|------------|
| 入门时间 | 1-2 天 | 半天 | 1-2 周 |
| 熟练使用 | 1-2 周 | 1-3 天 | 1-3 月 |
| 深入掌握 | 1 月 | 1 周 | 6-12 月 |
| 概念量 | 少 | 少 | 极多 |
| 调试难度 | 低 | 低 | 高 |

### 5.2 运维成本

| 项目 | Docker Compose | Kubernetes |
|------|----------------|------------|
| 集群维护 | 无 (单机) | 需要专人或托管服务 |
| 升级难度 | 低 | 中高 (版本兼容性) |
| 监控告警 | 简单 | 需要 Prometheus + Grafana 等 |
| 备份恢复 | 简单 | etcd 备份、Velero 等 |
| 安全维护 | 基础 | RBAC、网络策略、镜像扫描 |

### 5.3 基础设施成本

| 项目 | Docker Compose | K8s (托管) | K8s (自建) |
|------|----------------|------------|------------|
| 最低配置 | 1 台 2C4G | 3 节点托管集群 | 3+ 台服务器 |
| 月成本估算 | ¥50-200 | ¥500-2000 | ¥1000+ |
| 适合规模 | 1-20 个容器 | 10-1000+ 容器 | 100+ 容器 |

> **建议**：小项目别上 K8s，杀鸡用牛刀。当月流量或服务数量增长到 Compose 管理吃力时再考虑。

---

## 6. 总结与建议

### 6.1 初学者路线

```
1. 学 Docker 基础 (1-2 周)
   → 理解镜像、容器、Dockerfile
   → 能独立运行和构建容器

2. 学 Docker Compose (2-3 天)
   → 用 Compose 搭建本地开发环境
   → 实践：前后端 + 数据库一键启动

3. 用在实际项目中 (持续)
   → 用 Compose 管理你的个人项目
   → 积累容器化经验

4. 按需学 Kubernetes (需要时)
   → 当项目规模或工作需求要求时
   → 推荐从 minikube 或 kind 开始
```

### 6.2 生产环境建议

| 项目规模 | 建议方案 | 理由 |
|---------|---------|------|
| 个人项目 / MVP | Docker Compose | 够用、简单、快 |
| 小型团队 (3-5 人) | Compose 或轻量 K8s (k3s) | 平衡复杂度和能力 |
| 中型项目 (10+ 服务) | Kubernetes (托管) | 阿里云 ACK / AWS EKS |
| 大型系统 | Kubernetes + 完整生态 | 需要专职 SRE |

### 6.3 一句话总结

> **Docker 是基石，Compose 是加速器，K8s 是护城河。**
>
> 不要为了用 K8s 而用 K8s。能用 Compose 解决的问题，就别上 K8s。
> 当你的系统真的需要 K8s 时，你会自然感受到那个痛点。

---

## 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Kubernetes 官方文档](https://kubernetes.io/zh-cn/docs/)
- [Kompose 转换工具](https://kompose.io/)
- [k3s - 轻量级 K8s](https://k3s.io/)

---

> 🎉 **恭喜！** 你已经完成了 Docker 学习项目的全部理论文档！接下来请查看 `cheatsheets/` 目录下的速查表，随时查阅常用命令。
