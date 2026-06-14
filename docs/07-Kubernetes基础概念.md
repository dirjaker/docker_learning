# 07 - Kubernetes 基础概念

## 目录

- [什么是 Kubernetes？](#什么是-kubernetes)
- [Kubernetes 架构](#kubernetes-架构)
- [安装 Kubernetes](#安装-kubernetes)
- [Pod 基础](#pod-基础)
- [Namespace](#namespace)

---

## 什么是 Kubernetes？

### 一句话介绍

**Kubernetes**（简称 K8s）是一个**容器编排平台**，用来管理大量容器的部署、扩缩、网络和生命周期。

### Kubernetes 和 Docker 的关系

用一个类比来理解：

| 角色 | 类比 |
|------|------|
| **Docker** | 🧱 砖头 —— 负责把应用打包成容器 |
| **Kubernetes** | 🏗️ 建筑公司 —— 负责调度、管理成千上万块砖头 |

Docker 解决了「怎么打包和运行单个容器」的问题，Kubernetes 解决了「怎么管理成百上千个容器」的问题。

### 为什么需要 Kubernetes？

想象你只有 1 个容器，用 `docker run` 就搞定了。但当你的应用变成这样：

```
- 3 个前端实例
- 5 个后端实例
- 2 个数据库实例
- 1 个 Redis 缓存
- 1 个消息队列
```

手动管理这些容器你会遇到：

- **部署难**：12 个容器分布在 3 台服务器上，手动部署？
- **扩容难**：流量暴增，需要快速把后端从 5 个扩到 20 个？
- **故障处理难**：某个容器挂了，谁来自动重启？
- **更新难**：新版本发布，怎么做到零停机滚动更新？

Kubernetes 就是来解决这些问题的。

### Kubernetes 的核心能力

| 能力 | 说明 | 类比 |
|------|------|------|
| **自动部署** | 根据配置文件自动创建容器 | 施工图纸 → 自动盖楼 |
| **负载均衡** | 把流量均匀分配到多个实例 | 保安在多个门口分流人群 |
| **自动伸缩** | 根据 CPU/内存/自定义指标自动增减实例 | 人多了自动开新窗口 |
| **自愈能力** | 容器挂了自动重启，节点挂了自动迁移 | 墙塌了自动重建 |

---

## Kubernetes 架构

Kubernetes 采用**主从架构**，分为两大部分：

```
┌─────────────────────────────────────────────────────┐
│                Control Plane（控制平面）               │
│  ┌───────────┐ ┌──────┐ ┌──────────┐ ┌───────────┐  │
│  │ API Server│ │ etcd │ │Scheduler │ │Controller │  │
│  │  （前台）  │ │（数据库）││（调度员） │ │Manager（监工）│
│  └───────────┘ └──────┘ └──────────┘ └───────────┘  │
└─────────────────────────────────────────────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Node 1     │ │   Node 2     │ │   Node 3     │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │
│ │ kubelet  │ │ │ │ kubelet  │ │ │ │ kubelet  │ │
│ │ （管家）  │ │ │ │ （管家）  │ │ │ │ （管家）  │ │
│ ├──────────┤ │ │ ├──────────┤ │ │ ├──────────┤ │
│ │kube-proxy│ │ │ │kube-proxy│ │ │ │kube-proxy│ │
│ │（网络管理）│ │ │ │（网络管理）│ │ │ │（网络管理）│ │
│ ├──────────┤ │ │ ├──────────┤ │ │ ├──────────┤ │
│ │ 容器运行时 │ │ │ │ 容器运行时 │ │ │ │ 容器运行时 │ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │
│  [Pod][Pod]  │ │  [Pod][Pod]  │ │  [Pod][Pod]  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Control Plane（控制平面）

控制平面是集群的「大脑」，负责决策和管理。

#### API Server —— 集群的「前台」

```
所有操作都必须经过 API Server
```

- 它是整个集群的**唯一入口**
- 无论是你用 `kubectl` 发命令，还是内部组件通信，都走 API Server
- 负责认证、授权、准入控制

```bash
# 查看 API Server 的地址
kubectl cluster-info

# 直接调用 API Server 的 REST 接口
kubectl get --raw /api/v1
```

#### etcd —— 集群的「数据库」

```
所有集群状态都存在 etcd 里
```

- 一个高可用的**分布式键值存储**
- 存储了集群的所有状态信息：节点信息、Pod 信息、配置等
- 是集群中唯一的「真相来源」

```bash
# 查看 etcd 中存储的集群状态（通过 API Server 间接访问）
kubectl get all --all-namespaces
```

#### Scheduler —— 集群的「调度员」

```
决定 Pod 运行在哪个节点上
```

- 当你创建一个 Pod 时，Scheduler 负责选择最合适的 Node
- 调度策略：资源充足、亲和性、反亲和性、污点容忍等

```bash
# 查看调度结果：Pod 被分配到了哪个 Node
kubectl get pods -o wide
```

#### Controller Manager —— 集群的「监工」

```
确保实际状态 == 期望状态
```

- 持续监控集群状态，确保「你说要 3 个副本，那就一定有 3 个在运行」
- 包含多种控制器：Deployment Controller、Node Controller、Job Controller 等

```bash
# 你声明要 3 个副本
kubectl create deployment web --image=nginx --replicas=3

# Controller Manager 会确保始终有 3 个 Pod 在运行
kubectl get pods
```

### Node（工作节点）

工作节点是集群的「工人」，负责实际运行容器。

#### kubelet —— 节点的「管家」

- 运行在每个 Node 上
- 负责管理本节点上的 Pod 生命周期
- 向 API Server 汇报节点和 Pod 的状态

```bash
# 查看节点状态（由 kubelet 汇报）
kubectl get nodes
kubectl describe node <node-name>
```

#### kube-proxy —— 节点的「网络管理员」

- 负责实现 Kubernetes 的 **Service** 网络功能
- 维护网络规则，实现负载均衡和流量转发

#### Container Runtime —— 容器运行时

- 实际运行容器的软件
- 常见的有：containerd、CRI-O（Docker 已在 K8s 1.24 中弃用）

```bash
# 查看节点使用的容器运行时
kubectl get nodes -o wide
```

---

## 安装 Kubernetes

本地学习推荐以下三种方式：

### 方式一：minikube（推荐新手）

minikube 在本地创建一个**单节点**的 Kubernetes 集群，最适合学习。

```bash
# 安装 minikube（Linux）
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动集群
minikube start

# 查看集群状态
minikube status

# 查看集群信息
kubectl cluster-info

# 停止集群
minikube stop

# 删除集群
minikube delete
```

### 方式二：kind（Docker 中运行 K8s）

kind（Kubernetes IN Docker）使用 Docker 容器来模拟 K8s 节点，轻量快速。

```bash
# 安装 kind（Linux）
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# 创建集群
kind create cluster --name my-cluster

# 查看集群
kubectl cluster-info --context kind-my-cluster

# 创建多节点集群
cat <<EOF | kind create cluster --name multi-node --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

# 删除集群
kind delete cluster --name my-cluster
```

### 方式三：kubectl（命令行工具）

kubectl 是操作 Kubernetes 集群的**必备工具**，无论用哪种方式搭建集群都需要它。

```bash
# 安装 kubectl（Linux）
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# 验证安装
kubectl version --client
kubectl version --short

# 查看当前集群配置
kubectl config view

# 查看当前使用的 context（集群）
kubectl config current-context
```

---

## Pod 基础

### 什么是 Pod？

**Pod 是 Kubernetes 中最小的可调度单元。**

一个类比：

```
Pod 之于 K8s，就像 Container 之于 Docker。
```

- Docker 中，你操作的是容器
- K8s 中，你操作的是 Pod

一个 Pod 里面可以包含**一个或多个容器**，它们：
- 共享网络（同一个 IP，可以用 localhost 互相访问）
- 共享存储卷
- 一起调度到同一个 Node 上

```
┌─────── Pod ──────────────┐
│  ┌──────────┐ ┌────────┐ │
│  │ 主容器    │ │ 边车    │ │
│  │ (nginx)  │ │ (日志)  │ │
│  └──────────┘ └────────┘ │
│  共享: IP、网络、存储卷    │
└──────────────────────────┘
```

### Pod 和 Container 的关系

| 场景 | 说明 |
|------|------|
| **单容器 Pod**（最常见） | 一个 Pod 里只有一个容器 |
| **多容器 Pod** | 多个紧密耦合的容器，如主容器 + 日志收集 sidecar |

### Pod 的生命周期

Pod 有以下几个阶段（Phase）：

```
Pending → Running → Succeeded / Failed
           ↑
        Unknown（节点失联）
```

| 阶段 | 说明 |
|------|------|
| **Pending** | Pod 已创建，但容器还没完全启动（拉取镜像中、等待调度等） |
| **Running** | 至少一个容器正在运行 |
| **Succeeded** | 所有容器正常退出（适合一次性任务） |
| **Failed** | 至少一个容器异常退出 |
| **Unknown** | 无法获取 Pod 状态（通常是节点失联） |

### kubectl 操作 Pod

#### 创建 Pod

```bash
# 方式一：kubectl run（最快，适合测试）
kubectl run nginx-pod --image=nginx:latest

# 方式二：kubectl create + YAML 文件（声明式）
cat <<EOF > pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
    - name: nginx
      image: nginx:latest
      ports:
        - containerPort: 80
EOF
kubectl apply -f pod.yaml
```

#### 查看 Pod

```bash
# 查看所有 Pod
kubectl get pods

# 查看详细信息（包括 IP、所在 Node）
kubectl get pods -o wide

# 查看所有命名空间的 Pod
kubectl get pods --all-namespaces
# 简写
kubectl get pods -A

# 持续监听 Pod 变化（实时刷新）
kubectl get pods -w

# 查看 Pod 的 YAML 定义（服务器上实际的完整配置）
kubectl get pod nginx-pod -o yaml
```

#### 描述 Pod（排错利器）

```bash
# 查看 Pod 详细描述，包括事件信息（排错必用）
kubectl describe pod nginx-pod

# 常见排错流程：
# 1. 先看状态
kubectl get pods
# 2. 如果状态异常，describe 查看事件
kubectl describe pod <pod-name>
# 3. 查看容器日志
kubectl logs <pod-name>
```

#### 查看 Pod 日志

```bash
# 查看日志
kubectl logs nginx-pod

# 实时跟踪日志（类似 tail -f）
kubectl logs -f nginx-pod

# 查看最近 100 行日志
kubectl logs --tail=100 nginx-pod

# 查看多容器 Pod 中某个容器的日志
kubectl logs nginx-pod -c <container-name>
```

#### 进入 Pod（类似 docker exec）

```bash
# 进入 Pod 的容器（交互式 shell）
kubectl exec -it nginx-pod -- /bin/bash

# 如果容器没有 bash，用 sh
kubectl exec -it nginx-pod -- /bin/sh

# 在 Pod 中执行单条命令
kubectl exec nginx-pod -- cat /etc/nginx/nginx.conf
```

#### 删除 Pod

```bash
# 删除 Pod
kubectl delete pod nginx-pod

# 通过 YAML 文件删除
kubectl delete -f pod.yaml

# 强制删除（卡在 Terminating 状态时使用）
kubectl delete pod nginx-pod --grace-period=0 --force
```

### 完整示例：从创建到删除

```bash
# 1. 创建一个 Nginx Pod
kubectl run my-nginx --image=nginx:latest

# 2. 等待 Pod 运行
kubectl get pods -w
# NAME       READY   STATUS    RESTARTS   AGE
# my-nginx   1/1     Running   0          10s

# 3. 查看 Pod 详情
kubectl describe pod my-nginx

# 4. 查看日志
kubectl logs my-nginx

# 5. 进入容器
kubectl exec -it my-nginx -- /bin/bash

# 6. 退出后删除 Pod
kubectl delete pod my-nginx
```

---

## Namespace

### 什么是 Namespace？

**Namespace（命名空间）是 Kubernetes 中的虚拟集群**，用于将一个物理集群划分为多个逻辑隔离的区域。

类比：

```
一个 Kubernetes 集群 = 一栋办公楼
一个 Namespace       = 一个楼层
Pod                  = 员工
```

不同楼层的员工互相隔离，但可以通过电梯（网络）互相访问。

### 为什么需要 Namespace？

| 场景 | 说明 |
|------|------|
| **多团队共享集群** | 开发团队用 `dev`，测试团队用 `test`，生产用 `prod` |
| **环境隔离** | 开发环境和生产环境互不干扰 |
| **资源管理** | 可以给不同 Namespace 设置资源配额 |
| **权限控制** | 不同 Namespace 可以设置不同的访问权限 |

### K8s 默认的 Namespace

```bash
# 查看所有 Namespace
kubectl get namespaces

# 输出：
# NAME              STATUS   AGE
# default           Active   1d     ← 默认命名空间，不指定就用这个
# kube-node-lease   Active   1d     ← 节点心跳
# kube-public       Active   1d     ← 公共资源（所有人可读）
# kube-system       Active   1d     ← K8s 系统组件所在的空间
```

> ⚠️ **重要**：kube-system 里的 Pod 是 K8s 自身运行的组件，不要随便动！

### Namespace 操作

#### 创建 Namespace

```bash
# 方式一：命令行创建
kubectl create namespace dev
kubectl create namespace test
kubectl create namespace prod

# 方式二：YAML 文件创建
cat <<EOF > namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
  labels:
    env: development
EOF
kubectl apply -f namespace.yaml
```

#### 在指定 Namespace 中创建 Pod

```bash
# 在 dev 命名空间创建一个 Pod
kubectl run nginx-dev --image=nginx -n dev

# 在 prod 命名空间创建一个 Pod
kubectl run nginx-prod --image=nginx -n prod
```

#### 查看指定 Namespace 的资源

```bash
# 查看 dev 命名空间的所有 Pod
kubectl get pods -n dev

# 查看 prod 命名空间的所有 Pod
kubectl get pods -n prod

# 查看所有命名空间的所有 Pod
kubectl get pods -A

# 查看所有命名空间的所有资源
kubectl get all -A
```

#### 删除 Namespace 中的资源

```bash
# 删除 dev 命名空间中的 Pod
kubectl delete pod nginx-dev -n dev

# 删除整个命名空间（会删除该命名空间下的所有资源！）
kubectl delete namespace dev
```

#### 设置默认 Namespace

每次输入 `-n dev` 很麻烦？可以设置默认 Namespace：

```bash
# 临时切换默认命名空间（只对当前 context 生效）
kubectl config set-context --current --namespace=dev

# 验证
kubectl config view --minify | grep namespace

# 之后的命令就不需要 -n 了
kubectl get pods  # 等同于 kubectl get pods -n dev

# 切回默认
kubectl config set-context --current --namespace=default
```

### Namespace 完整示例

```bash
# 1. 创建 dev 和 prod 命名空间
kubectl create namespace dev
kubectl create namespace prod

# 2. 在 dev 中创建一个 nginx Pod
kubectl run nginx --image=nginx -n dev

# 3. 在 prod 中也创建一个 nginx Pod
kubectl run nginx --image=nginx -n prod

# 4. 分别查看（注意：两个同名的 Pod 在不同命名空间中不冲突！）
kubectl get pods -n dev
kubectl get pods -n prod

# 5. 查看所有命名空间的 Pod
kubectl get pods -A

# 6. 清理
kubectl delete pod nginx -n dev
kubectl delete pod nginx -n prod
kubectl delete namespace dev
kubectl delete namespace prod
```

---

## 总结

| 概念 | 一句话总结 |
|------|-----------|
| **Kubernetes** | 容器编排平台，管理大量容器的部署、伸缩和运维 |
| **Control Plane** | 集群大脑：API Server（前台）、etcd（数据库）、Scheduler（调度员）、Controller Manager（监工） |
| **Node** | 工作节点，运行实际容器，由 kubelet 管理 |
| **Pod** | K8s 最小调度单元，一个或多个容器的集合 |
| **Namespace** | 虚拟集群，用于逻辑隔离和多团队共享 |

### 常用命令速查

```bash
# 集群信息
kubectl cluster-info
kubectl get nodes

# Pod 操作
kubectl run <name> --image=<image>        # 创建 Pod
kubectl get pods                           # 查看 Pod
kubectl describe pod <name>                # Pod 详情
kubectl logs <name>                        # 查看日志
kubectl exec -it <name> -- /bin/bash       # 进入容器
kubectl delete pod <name>                  # 删除 Pod

# Namespace 操作
kubectl get namespaces                     # 查看命名空间
kubectl create namespace <name>            # 创建命名空间
kubectl get pods -n <namespace>            # 查看指定命名空间的 Pod
kubectl get pods -A                        # 查看所有命名空间的 Pod
```

---

> 📌 **下一篇**：我们将学习 Kubernetes 的工作负载资源 —— Deployment、ReplicaSet 和 DaemonSet，了解如何管理多个 Pod 副本。
