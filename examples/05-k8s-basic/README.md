# 示例 05：Kubernetes 基础 ☸️

演示 Kubernetes 的核心资源对象：Namespace、Deployment、Service、ConfigMap、Ingress。

## 学习目标

- 理解 Kubernetes 的核心概念和资源对象
- 学会创建 Namespace 隔离资源
- 学会使用 Deployment 管理 Pod
- 理解 Service 的类型（ClusterIP、NodePort）
- 学会使用 ConfigMap 管理配置
- 理解 Ingress 的路由规则

## 架构图

```
外部流量
    │
    ▼
┌─────────┐
│ Ingress │  demo-app.local → demo-app-service:80
└────┬────┘
     │
     ▼
┌─────────────┐
│   Service   │  ClusterIP: 10.x.x.x:80
│ (ClusterIP) │
└────┬────────┘
     │ 负载均衡
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Pod 1  │  │  Pod 2  │  │  Pod 3  │
│ (nginx) │  │ (nginx) │  │ (nginx) │
└─────────┘  └─────────┘  └─────────┘
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `namespace.yml` | 命名空间定义 |
| `deployment.yml` | Deployment（Pod 管理） |
| `service.yml` | Service（网络访问） |
| `configmap.yml` | ConfigMap（配置管理） |
| `ingress.yml` | Ingress（外部路由） |

## 快速开始

### 前置条件

确保已安装 kubectl 并连接到 Kubernetes 集群：

```bash
kubectl cluster-info
```

### 1. 创建所有资源

```bash
# 按顺序应用配置
kubectl apply -f namespace.yml
kubectl apply -f configmap.yml
kubectl apply -f deployment.yml
kubectl apply -f service.yml
kubectl apply -f ingress.yml

# 或者一次性应用
kubectl apply -f .
```

### 2. 查看资源状态

```bash
# 查看命名空间中的所有资源
kubectl get all -n demo-app

# 查看 Pod 状态
kubectl get pods -n demo-app -o wide

# 查看 Service
kubectl get svc -n demo-app

# 查看 Ingress
kubectl get ingress -n demo-app
```

### 3. 访问应用

```bash
# 方式 1：通过 NodePort 访问
curl http://<节点IP>:30080

# 方式 2：通过端口转发
kubectl port-forward svc/demo-app-service 8080:80 -n demo-app
curl http://localhost:8080

# 方式 3：通过 Ingress（需要配置 hosts 或 DNS）
echo "<INGRESS_IP> demo-app.local" | sudo tee -a /etc/hosts
curl http://demo-app.local
```

### 4. 查看日志

```bash
kubectl logs -f deployment/demo-app -n demo-app
```

### 5. 扩缩容

```bash
# 扩容到 5 个副本
kubectl scale deployment demo-app --replicas=5 -n demo-app

# 查看扩容结果
kubectl get pods -n demo-app -w
```

### 6. 更新应用

```bash
# 更新镜像
kubectl set image deployment/demo-app demo-app=nginx:1.25-alpine -n demo-app

# 查看滚动更新状态
kubectl rollout status deployment/demo-app -n demo-app

# 回滚（如果需要）
kubectl rollout undo deployment/demo-app -n demo-app
```

### 7. 清理资源

```bash
# 删除命名空间（会删除其中所有资源）
kubectl delete namespace demo-app
```

## 核心概念

### Namespace（命名空间）
用于隔离不同团队、项目或环境的资源。

### Deployment（部署）
- 声明式管理 Pod 的副本数量
- 支持滚动更新和回滚
- 自动修复失败的 Pod

### Service（服务）
- ClusterIP：集群内部访问
- NodePort：通过节点端口外部访问
- LoadBalancer：云厂商负载均衡器

### ConfigMap（配置映射）
存储非敏感的配置数据，可以作为环境变量或文件挂载到 Pod 中。

### Ingress（入口）
管理外部 HTTP/HTTPS 访问，支持基于主机名和路径的路由。

## 下一步

继续学习 [06-k8s-production](../06-k8s-production/)，了解生产级 Kubernetes 部署。
