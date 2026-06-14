# 示例 06：Kubernetes 生产级部署 🏭

演示生产级 Kubernetes 部署的最佳实践，包括 PostgreSQL、Redis 和 API 服务的完整部署。

## 学习目标

- 理解生产级 Kubernetes 部署的配置要点
- 学会使用 Secret 管理敏感数据
- 学会使用 PVC 持久化存储
- 理解探针（Probe）的三种类型
- 学会配置资源限制和请求
- 理解滚动更新策略

## 架构图

```
                          ┌─────────────┐
                          │   Ingress   │
                          │ (TLS/HTTPS) │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │ API Service │
                          │  ClusterIP  │
                          └──────┬──────┘
                                 │ 负载均衡
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
               ┌─────────┐ ┌─────────┐ ┌─────────┐
               │ API Pod │ │ API Pod │ │ API Pod │
               └────┬────┘ └────┬────┘ └────┬────┘
                    │           │           │
            ┌───────┴───────────┴───────────┘
            │
    ┌───────┴───────┐         ┌───────────┐
    ▼               ▼         ▼           │
┌────────────┐ ┌──────────┐               │
│ PostgreSQL │ │  Redis   │               │
│   (PVC)    │ │ (缓存)    │               │
└────────────┘ └──────────┘               │
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `namespace.yml` | 生产环境命名空间 |
| `configmap.yml` | 应用配置（非敏感） |
| `secret.yml` | 敏感数据（密码、密钥） |
| `postgres-deployment.yml` | PostgreSQL 部署 + Service |
| `postgres-pvc.yml` | 持久化存储声明 |
| `redis-deployment.yml` | Redis 部署 + Service |
| `api-deployment.yml` | API 服务部署 |
| `api-service.yml` | API 服务 Service |
| `ingress.yml` | Ingress 路由配置 |

## 快速开始

### 前置条件

```bash
# 确保连接到集群
kubectl cluster-info

# 如果使用 Minikube，启用 Ingress 插件
minikube addons enable ingress
```

### 1. 部署所有资源

```bash
# 按依赖顺序部署
kubectl apply -f namespace.yml
kubectl apply -f configmap.yml
kubectl apply -f secret.yml
kubectl apply -f postgres-pvc.yml
kubectl apply -f postgres-deployment.yml
kubectl apply -f redis-deployment.yml
kubectl apply -f api-deployment.yml
kubectl apply -f api-service.yml
kubectl apply -f ingress.yml

# 或一次性部署
kubectl apply -f .
```

### 2. 查看部署状态

```bash
# 查看所有资源
kubectl get all -n production

# 查看 Pod 状态（等待所有 Pod Running）
kubectl get pods -n production -w

# 查看 PVC 状态
kubectl get pvc -n production

# 查看 Ingress
kubectl get ingress -n production
```

### 3. 验证服务

```bash
# 端口转发 API 服务
kubectl port-forward svc/api-service 8080:80 -n production

# 测试访问
curl http://localhost:8080
```

### 4. 查看日志

```bash
# API 日志
kubectl logs -f deployment/api -n production

# PostgreSQL 日志
kubectl logs -f deployment/postgres -n production

# Redis 日志
kubectl logs -f deployment/redis -n production
```

### 5. 扩缩容

```bash
# 扩容 API 到 5 个副本
kubectl scale deployment api --replicas=5 -n production

# 设置自动扩缩容（需要 metrics-server）
kubectl autoscale deployment api --min=3 --max=10 --cpu-percent=70 -n production
```

### 6. 更新 API 镜像

```bash
# 更新镜像
kubectl set image deployment/api api=your-registry/api:v2.0.0 -n production

# 查看更新状态
kubectl rollout status deployment/api -n production

# 回滚
kubectl rollout undo deployment/api -n production
```

### 7. 清理

```bash
kubectl delete namespace production
```

## 最佳实践

### 1. 资源限制

```yaml
resources:
  requests:
    cpu: "100m"      # 最小保证
    memory: "128Mi"
  limits:
    cpu: "500m"      # 最大可用
    memory: "256Mi"
```

### 2. 三种探针

| 探针 | 用途 | 时机 |
|------|------|------|
| `startupProbe` | 应用启动检查 | 启动时 |
| `readinessProbe` | 是否可接收流量 | 运行中 |
| `livenessProbe` | 是否存活 | 运行中 |

### 3. Secret 管理

```bash
# 从文件创建 Secret
kubectl create secret generic api-secrets \
  --from-literal=POSTGRES_USER=appuser \
  --from-literal=POSTGRES_PASSWORD=securepassword \
  -n production

# 查看 Secret
kubectl get secret api-secrets -n production -o yaml
```

### 4. 优雅关闭

```yaml
terminationGracePeriodSeconds: 30
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 5"]
```

## 故障排查

```bash
# 查看 Pod 详情
kubectl describe pod <pod-name> -n production

# 查看事件
kubectl get events -n production --sort-by='.lastTimestamp'

# 进入 Pod 调试
kubectl exec -it <pod-name> -n production -- /bin/sh

# 查看资源使用
kubectl top pods -n production
```

## 下一步

- 学习 Helm Charts 打包和部署
- 了解 GitOps（ArgoCD / Flux）
- 学习 Service Mesh（Istio）
- 了解 Kubernetes Operator 模式
