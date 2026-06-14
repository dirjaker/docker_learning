# 09 - Kubernetes 网络与存储

> 网络是集群的「高速公路」，存储是集群的「仓库」。掌握它们，你的应用才能真正跑起来、留得住数据。

---

## 一、Kubernetes 网络模型

### 1.1 核心原则：每个 Pod 一个 IP

K8s 的网络模型非常简洁，遵循以下原则：

- **每个 Pod 分配一个独立的 IP 地址**
- **所有 Pod 之间可以直接通信**（不需要 NAT）
- **Node 上的进程可以和该 Node 上的 Pod 通信**

> 🏠 **类比**：想象一个小区（集群），每户人家（Pod）都有一个唯一的门牌号（IP），任何两户之间可以直接写信通信，不需要经过物业转交。

### 1.2 Pod 到 Pod 通信

**同 Node 上的 Pod 通信：**

同一个 Node 上的 Pod 通过一个虚拟网桥（`cbr0`/`cni0`）互相通信，就像连在同一台交换机上。

```
┌─── Node 1 ───────────────────┐
│                               │
│  Pod A (10.244.1.5)           │
│  Pod B (10.244.1.6)           │
│       ↕ 直接通过网桥通信       │
│      [cni0 / cbr0]            │
└───────────────────────────────┘
```

**不同 Node 上的 Pod 通信：**

不同 Node 上的 Pod 通过网络插件（CNI）实现跨节点通信。常见的 CNI 插件：

| 插件 | 特点 |
|------|------|
| **Flannel** | 简单轻量，适合入门 |
| **Calico** | 支持网络策略，生产常用 |
| **Cilium** | 基于 eBPF，高性能 |

```
┌─── Node 1 ──────┐     ┌─── Node 2 ──────┐
│ Pod A (10.244.1.5)│     │ Pod C (10.244.2.7)│
│                   │ ←→ │                   │
│    [cni0]         │     │    [cni0]         │
│  节点IP: 192.168.1.10│  │ 节点IP: 192.168.1.11│
└───────────────────┘     └───────────────────┘
         ↕ CNI 插件负责封装/路由
```

### 1.3 Pod 到 Service 通信

Pod 的 IP 会随着重建而变化，所以我们需要一个稳定的访问入口——**Service**。

```yaml
# 09-files/service-demo.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: web
  ports:
    - port: 80          # Service 端口
      targetPort: 8080   # Pod 端口
  type: ClusterIP        # 默认类型，仅集群内访问
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deploy
spec:
  replicas: 3
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
          image: nginx:alpine
          ports:
            - containerPort: 8080
```

```bash
# 创建 Service
kubectl apply -f 09-files/service-demo.yaml

# 查看 Service
kubectl get svc my-service

# 从集群内任意 Pod 访问
kubectl run test-pod --image=busybox --rm -it -- wget -qO- http://my-service
```

> 📞 **类比**：Service 就像一个公司的「总机号码」。不管你找哪个员工（Pod），拨总机号就能接通。Pod 换了人，总机号不变。

### 1.4 集群外部到集群内部通信

外部流量进入集群有三种方式：

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **NodePort** | 在每个 Node 上开放一个端口（30000-32767） | 开发测试 |
| **LoadBalancer** | 使用云厂商负载均衡器 | 云环境生产 |
| **Ingress** | 七层路由，支持域名/路径 | 生产环境 |

```yaml
# NodePort 示例
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080   # 外部通过 <任意NodeIP>:30080 访问
```

---

## 二、Ingress —— 集群的「门卫」

### 2.1 什么是 Ingress？

Ingress 是 Kubernetes 中管理**外部 HTTP/HTTPS 流量**的资源对象。它可以根据域名和路径将请求路由到不同的 Service。

> 🏢 **类比**：Ingress 就像公司大楼的「前台门卫」。访客说"我要找市场部"，门卫引导到 A 楼层；说"找技术部"，引导到 B 楼层。所有访客都从同一个大门进，但被分到不同的目的地。

```
外部请求
  │
  ├─ api.example.com  ──→  Ingress  ──→  api-service (后端 API)
  ├─ web.example.com  ──→  Ingress  ──→  web-service (前端页面)
  └─ /static/*        ──→  Ingress  ──→  static-service (静态资源)
```

### 2.2 Ingress Controller

Ingress 资源本身只是一份「路由规则」，真正执行流量转发的是 **Ingress Controller**。最常用的是 **Nginx Ingress Controller**。

```bash
# 安装 Nginx Ingress Controller（使用 Helm）
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# 或者用 kubectl 直接部署
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# 检查是否就绪
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### 2.3 Ingress 资源定义

#### 基于域名的路由

```yaml
# 09-files/ingress-host.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-based-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
    - host: web.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
```

#### 基于路径的路由

```yaml
# 09-files/ingress-path.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
          - path: /web
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
```

### 2.4 TLS/HTTPS 配置

```yaml
# 09-files/ingress-tls.yaml
# 首先创建 TLS Secret
# kubectl create secret tls my-tls-secret --cert=tls.crt --key=tls.key
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - myapp.example.com
      secretName: my-tls-secret
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
```

```bash
# 创建自签名证书（测试用）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=myapp.example.com"

# 创建 Secret
kubectl create secret tls my-tls-secret --cert=tls.crt --key=tls.key

# 部署 Ingress
kubectl apply -f 09-files/ingress-tls.yaml

# 测试（需要配置 hosts 或 DNS）
curl -k https://myapp.example.com
```

### 2.5 查看 Ingress 状态

```bash
# 查看 Ingress
kubectl get ingress

# 查看详细信息
kubectl describe ingress host-based-ingress

# 查看 Ingress Controller 日志
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

---

## 三、Kubernetes 存储

### 3.1 Volume（临时存储）

#### emptyDir —— 临时共享目录

Pod 启动时创建，Pod 删除时数据消失。适合容器间共享临时文件。

> 📦 **类比**：就像一块共享白板。大家可以一起在上面写字，但会议结束后白板就擦干净了。

```yaml
# 09-files/volume-emptydir.yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-data
spec:
  containers:
    - name: writer
      image: busybox
      command: ["sh", "-c", "echo 'Hello from writer' > /data/msg.txt; sleep 3600"]
      volumeMounts:
        - name: shared-vol
          mountPath: /data
    - name: reader
      image: busybox
      command: ["sh", "-c", "cat /data/msg.txt; sleep 3600"]
      volumeMounts:
        - name: shared-vol
          mountPath: /data
  volumes:
    - name: shared-vol
      emptyDir: {}
```

```bash
# 部署
kubectl apply -f 09-files/volume-emptydir.yaml

# 验证 reader 容器能看到 writer 写的数据
kubectl exec shared-data -c reader -- cat /data/msg.txt
# 输出: Hello from writer
```

#### hostPath —— 挂载宿主机目录

把 Node 上的目录挂载到 Pod 中。数据持久，但**绑定了特定 Node**。

> 🏠 **类比**：就像在邻居家里存了一个柜子。只有住在那栋楼的住户（Pod）能方便使用，换了楼就不行了。

```yaml
# 09-files/volume-hostpath.yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-demo
spec:
  containers:
    - name: app
      image: nginx:alpine
      volumeMounts:
        - name: host-data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: host-data
      hostPath:
        path: /tmp/k8s-data
        type: DirectoryOrCreate   # 如果目录不存在就创建
```

```bash
# 部署
kubectl apply -f 09-files/volume-hostpath.yaml

# 在宿主机上写入内容
# 先找到 Pod 所在的 Node
kubectl get pod hostpath-demo -o wide

# 在该 Node 上执行
echo "<h1>Hello from hostPath</h1>" > /tmp/k8s-data/index.html

# 访问 Pod 内的 nginx
kubectl exec hostpath-demo -- cat /usr/share/nginx/html/index.html
```

#### configMap / secret —— 挂载配置和密钥

```yaml
# 09-files/configmap-volume.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
        listen 80;
        server_name localhost;
        location / {
            return 200 "Hello from custom config!";
        }
    }
---
apiVersion: v1
kind: Pod
metadata:
  name: configmap-demo
spec:
  containers:
    - name: nginx
      image: nginx:alpine
      volumeMounts:
        - name: config-vol
          mountPath: /etc/nginx/conf.d
  volumes:
    - name: config-vol
      configMap:
        name: nginx-config
```

```yaml
# 09-files/secret-volume.yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: YWRtaW4=        # base64 编码的 "admin"
  password: cGFzc3dvcmQxMjM=  # base64 编码的 "password123"
---
apiVersion: v1
kind: Pod
metadata:
  name: secret-demo
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "cat /secrets/username && echo '' && sleep 3600"]
      volumeMounts:
        - name: secret-vol
          mountPath: /secrets
          readOnly: true
  volumes:
    - name: secret-vol
      secret:
        secretName: db-secret
```

```bash
# 创建 ConfigMap 和部署
kubectl apply -f 09-files/configmap-volume.yaml
kubectl apply -f 09-files/secret-volume.yaml

# 验证
kubectl exec configmap-demo -- cat /etc/nginx/conf.d/nginx.conf
kubectl exec secret-demo -- cat /secrets/username
```

---

### 3.2 PersistentVolume (PV) —— 集群的「仓库」

#### 什么是 PV？

PV 是集群级别的存储资源，由管理员预先分配，独立于 Pod 的生命周期。

> 🏭 **类比**：PV 就像仓库里的一间库房。管理员把库房建好（分配存储空间），放在那里等着用户来提货使用。

```yaml
# 09-files/pv-demo.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce       # 单节点读写
  hostPath:
    path: /tmp/pv-data
```

#### PV 的访问模式

| 模式 | 简写 | 说明 |
|------|------|------|
| ReadWriteOnce | RWO | 单节点读写 |
| ReadOnlyMany | ROX | 多节点只读 |
| ReadWriteMany | RWX | 多节点读写 |

#### PV 的回收策略

当 PVC 被删除后，PV 中的数据怎么处理？

| 策略 | 行为 |
|------|------|
| **Retain** | 保留数据，需手动清理（默认） |
| **Delete** | 自动删除 PV 和存储资源 |
| **Recycle** | 清空数据（已废弃） |

```yaml
# 回收策略示例
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-retain
spec:
  storageClassName: manual
  persistentVolumeReclaimPolicy: Retain   # 保留数据
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /tmp/pv-retain-data
```

#### PV 的生命周期

```
Available → Bound → Released → (手动回收) → Available
   │          │         │
   │          │         └─ PVC 被删除，PV 释放
   │          └─ PVC 绑定到 PV
   └─ PV 创建后，等待绑定
```

---

### 3.3 PersistentVolumeClaim (PVC) —— 用户的「提货单」

PVC 是用户对存储资源的「申请」。用户不需要关心底层存储细节，只需要说明"我需要多大空间、什么访问模式"。

> 🧾 **类比**：PVC 就像仓库的「提货单」。你在单子上写"我要 5G 空间，读写模式"，仓库管理员（K8s）帮你匹配一间合适的库房（PV）。

```yaml
# 09-files/pvc-demo.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi       # 申请 2G（会匹配 ≥ 2G 的 PV）
```

```bash
# 创建 PV 和 PVC
kubectl apply -f 09-files/pv-demo.yaml
kubectl apply -f 09-files/pvc-demo.yaml

# 查看绑定状态
kubectl get pv
kubectl get pvc

# 输出示例：
# NAME    STATUS   CAPACITY   ACCESS MODES   STORAGECLASS   CLAIM
# my-pv   Bound    5Gi        RWO            manual         default/my-pvc
```

#### 在 Pod 中使用 PVC

```yaml
# 09-files/pvc-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-user
spec:
  containers:
    - name: app
      image: nginx:alpine
      volumeMounts:
        - name: data-vol
          mountPath: /usr/share/nginx/html
  volumes:
    - name: data-vol
      persistentVolumeClaim:
        claimName: my-pvc
```

```bash
kubectl apply -f 09-files/pvc-pod.yaml

# 写入数据
kubectl exec pvc-user -- sh -c 'echo "Persistent data!" > /usr/share/nginx/html/index.html'

# 删除 Pod
kubectl delete pod pvc-user

# 重新创建 Pod
kubectl apply -f 09-files/pvc-pod.yaml

# 数据还在！
kubectl exec pvc-user -- cat /usr/share/nginx/html/index.html
# 输出: Persistent data!
```

---

### 3.4 StorageClass —— 自动创建 PV

手动创建 PV 很麻烦。StorageClass 可以**按需自动创建 PV**，这就是「动态供应」。

> 🏭 **类比**：StorageClass 就像仓库的「自动生产线」。以前管理员要手动建库房（PV），现在只要用户提交提货单（PVC），生产线自动建好一间库房。

```yaml
# 09-files/storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-storage
provisioner: kubernetes.io/no-provisioner   # 本地存储（实际生产用云厂商 provisioner）
volumeBindingMode: WaitForFirstConsumer     # 等到 Pod 调度时才创建
reclaimPolicy: Delete
---
# 使用 StorageClass 的 PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  storageClassName: fast-storage
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
```

常见的 Provisioner：

| 环境 | Provisioner | 说明 |
|------|-------------|------|
| AWS | kubernetes.io/aws-ebs | EBS 卷 |
| GCP | kubernetes.io/gce-pd | 持久盘 |
| 本地 | rancher.io/local-path | 本地路径 |
| NFS | nfs-subdir-external-provisioner | NFS 存储 |

---

## 四、实战

### 实战 1：使用 Ingress 暴露多个服务

部署两个应用，通过 Ingress 根据域名路由。

```yaml
# 09-files/practice-ingress.yaml
# ============ 应用 1：前端 ============
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: nginx:alpine
          ports:
            - containerPort: 80
          volumeMounts:
            - name: html
              mountPath: /usr/share/nginx/html
      initContainers:
        - name: init-frontend
          image: busybox
          command: ["sh", "-c", "echo '<h1>Frontend App</h1>' > /html/index.html"]
          volumeMounts:
            - name: html
              mountPath: /html
      volumes:
        - name: html
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-svc
spec:
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
---
# ============ 应用 2：后端 API ============
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: nginx:alpine
          ports:
            - containerPort: 80
          volumeMounts:
            - name: html
              mountPath: /usr/share/nginx/html
      initContainers:
        - name: init-backend
          image: busybox
          command: ["sh", "-c", "echo '{\"status\":\"ok\",\"service\":\"backend-api\"}' > /html/index.html"]
          volumeMounts:
            - name: html
              mountPath: /html
      volumes:
        - name: html
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 80
---
# ============ Ingress 路由 ============
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-service-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: frontend.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-svc
                port:
                  number: 80
    - host: api.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-svc
                port:
                  number: 80
```

```bash
# 部署所有资源
kubectl apply -f 09-files/practice-ingress.yaml

# 检查状态
kubectl get pods
kubectl get svc
kubectl get ingress

# 获取 Ingress Controller 的 IP/端口
export INGRESS_HOST=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.clusterIP}')

# 测试（在集群内或配置 hosts 后）
curl -H "Host: frontend.local" http://$INGRESS_HOST
# 输出: <h1>Frontend App</h1>

curl -H "Host: api.local" http://$INGRESS_HOST
# 输出: {"status":"ok","service":"backend-api"}
```

### 实战 2：使用 PVC 持久化 MySQL 数据

```yaml
# 09-files/practice-mysql-pvc.yaml
# ============ PVC ============
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
# ============ PV ============
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv
  labels:
    type: local
    app: mysql
spec:
  storageClassName: manual
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /tmp/mysql-data
---
# ============ Secret（数据库密码） ============
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
data:
  mysql-root-password: cm9vdDEyMzQ1    # base64: root12345
---
# ============ MySQL Deployment ============
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          ports:
            - containerPort: 3306
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: mysql-root-password
          volumeMounts:
            - name: mysql-storage
              mountPath: /var/lib/mysql
      volumes:
        - name: mysql-storage
          persistentVolumeClaim:
            claimName: mysql-pvc
---
# ============ MySQL Service ============
apiVersion: v1
kind: Service
metadata:
  name: mysql-svc
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
      targetPort: 3306
  type: ClusterIP
```

```bash
# 部署
kubectl apply -f 09-files/practice-mysql-pvc.yaml

# 等待 Pod 就绪
kubectl wait --for=condition=ready pod -l app=mysql --timeout=120s

# 创建测试数据库
kubectl exec -it deploy/mysql -- mysql -uroot -proot12345 -e "
  CREATE DATABASE testdb;
  USE testdb;
  CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50));
  INSERT INTO users (name) VALUES ('Alice'), ('Bob'), ('Charlie');
  SELECT * FROM users;
"

# 删除 Pod 模拟故障
kubectl delete pod -l app=mysql

# 等待新 Pod 启动
kubectl wait --for=condition=ready pod -l app=mysql --timeout=120s

# 验证数据还在！
kubectl exec -it deploy/mysql -- mysql -uroot -proot12345 -e "SELECT * FROM testdb.users;"
# +----+---------+
# | id | name    |
# +----+---------+
# |  1 | Alice   |
# |  2 | Bob     |
# |  3 | Charlie |
# +----+---------+
```

### 实战 3：使用 ConfigMap 挂载配置文件

部署一个 Redis，通过 ConfigMap 自定义配置。

```yaml
# 09-files/practice-configmap.yaml
# ============ ConfigMap ============
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    maxmemory 128mb
    maxmemory-policy allkeys-lru
    appendonly yes
    appendfsync everysec
    port 6379
    bind 0.0.0.0
    loglevel notice
  # 也可以用键值对方式（作为环境变量）
  REDIS_LOG_LEVEL: "verbose"
---
# ============ Redis Deployment ============
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command: ["redis-server", "/etc/redis/redis.conf"]
          ports:
            - containerPort: 6379
          # 方式 1：挂载整个 ConfigMap 为文件
          volumeMounts:
            - name: redis-config-vol
              mountPath: /etc/redis
          # 方式 2：使用 ConfigMap 中的单个键作为环境变量
          env:
            - name: MY_REDIS_LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: redis-config
                  key: REDIS_LOG_LEVEL
      volumes:
        - name: redis-config-vol
          configMap:
            name: redis-config
---
# ============ Redis Service ============
apiVersion: v1
kind: Service
metadata:
  name: redis-svc
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
```

```bash
# 部署
kubectl apply -f 09-files/practice-configmap.yaml

# 验证配置文件已挂载
kubectl exec deploy/redis -- cat /etc/redis/redis.conf

# 验证环境变量
kubectl exec deploy/redis -- env | grep MY_REDIS_LOG_LEVEL
# MY_REDIS_LOG_LEVEL=verbose

# 验证 Redis 使用了自定义配置
kubectl exec deploy/redis -- redis-cli CONFIG GET maxmemory
# 1) "maxmemory"
# 2) "134217728"    # 128MB

kubectl exec deploy/redis -- redis-cli CONFIG GET appendonly
# 1) "appendonly"
# 2) "yes"
```

```bash
# 清理所有资源
kubectl delete -f 09-files/practice-configmap.yaml
kubectl delete -f 09-files/practice-mysql-pvc.yaml
kubectl delete -f 09-files/practice-ingress.yaml
```

---

## 五、总结速查

```
网络
├── Pod ↔ Pod：CNI 插件直接通信
├── Pod ↔ Service：稳定的虚拟 IP + 负载均衡
└── 外部 → 集群：NodePort / LoadBalancer / Ingress

Ingress
├── Ingress 资源：路由规则（域名 + 路径）
├── Ingress Controller：真正转发流量（Nginx 等）
└── TLS：通过 Secret 配置 HTTPS

存储
├── Volume（临时）
│   ├── emptyDir：Pod 内共享，Pod 删除即丢
│   ├── hostPath：挂载宿主机目录
│   └── ConfigMap / Secret：挂载配置/密钥
├── PV（持久卷）
│   ├── 管理员创建，集群级资源
│   ├── 访问模式：RWO / ROX / RWX
│   └── 回收策略：Retain / Delete
├── PVC（持久卷声明）
│   ├── 用户申请，指定大小和访问模式
│   └── 自动绑定匹配的 PV
└── StorageClass（存储类）
    ├── 定义存储的「规格」
    └── 动态供应：PVC 创建时自动创建 PV
```

> 📌 **记住这个口诀**：
> - 网络靠 Service 稳定访问，Ingress 管外部入口
> - 临时数据用 emptyDir，持久数据找 PV/PVC
> - 别手动建 PV 了，用 StorageClass 动态供应！
