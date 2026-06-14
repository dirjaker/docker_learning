# 08 - Kubernetes 核心资源

> 上一篇我们了解了 Kubernetes 的架构和基本概念。这一篇深入讲解 K8s 中最常用的几种核心资源对象，它们是你日常操作 K8s 的「基本功」。

---

## 目录

1. [Label 和 Selector — 资源的「标签系统"](#1-label-和-selector--资源的标签系统)
2. [Deployment — 管理 Pod 的「工头"](#2-deployment--管理-pod-的工头)
3. [Service — Pod 的「前台接待"](#3-service--pod-的前台接待)
4. [ConfigMap — 配置的「便签本"](#4-configmap--配置的便签本)
5. [Secret — 配置的「保险箱"](#5-secret--配置的保险箱)
6. [实战：完整的 Nginx 部署流程](#6-实战完整的-nginx-部署流程)

---

## 1. Label 和 Selector — 资源的「标签系统」

### 什么是 Label？

**Label（标签）** 是附加在 K8s 资源对象上的键值对，就像给文件贴便利贴。

```
举个例子：
  app: nginx          ← 这是什么应用
  environment: prod   ← 在哪个环境
  version: v1.0       ← 什么版本
```

Label 的特点：
- 每个资源可以有多个 Label
- Label 不要求唯一（多个 Pod 可以有相同的 Label）
- Label 可以随时添加、修改、删除
- Label 本身不做任何事情，它是给 **Selector** 用的

### 为什么需要 Label？

想象你有 100 个 Pod，有些是前端、有些是后端、有些是数据库。你怎么区分它们？靠名字？太麻烦。**Label 就是用来分类和筛选资源的。**

```
┌─────────────────────────────────────────────┐
│  Pod-1  [app=nginx, env=prod]               │
│  Pod-2  [app=nginx, env=prod]               │
│  Pod-3  [app=nginx, env=staging]            │
│  Pod-4  [app=mysql, env=prod]               │
│  Pod-5  [app=redis, env=prod]               │
└─────────────────────────────────────────────┘

想找到所有 prod 环境的 Pod？Selector: env=prod → Pod-1,2,4,5
想找所有 nginx Pod？           Selector: app=nginx → Pod-1,2,3
```

### kubectl label 命令

```bash
# 给节点打标签
kubectl label nodes node1 disktype=ssd

# 给 Pod 打标签
kubectl label pod nginx-xxx version=v2

# 查看标签
kubectl get pods --show-labels

# 按标签筛选
kubectl get pods -l app=nginx
kubectl get pods -l 'app=nginx,env=prod'
kubectl get pods -l 'app in (nginx, redis)'

# 删除标签
kubectl label pod nginx-xxx version-
```

### Selector（选择器）

Selector 是通过 Label 来筛选资源的机制。它是很多 K8s 资源关联其他资源的「桥梁」。

```yaml
# 等值选择器
selector:
  matchLabels:
    app: nginx

# 集合选择器（更灵活）
selector:
  matchExpressions:
    - key: env
      operator: In        # In, NotIn, Exists, DoesNotExist
      values:
        - prod
        - staging
```

> **核心理解：** Label 是「贴标签」，Selector 是「按标签找人」。Deployment 通过 Selector 找到它要管理的 Pod，Service 通过 Selector 找到它要转发流量的 Pod。

---

## 2. Deployment — 管理 Pod 的「工头」

### 什么是 Deployment？

**Deployment** 是最常用的 K8s 资源，它负责管理 Pod 的「生命周期」。

类比理解：
```
你是老板（你写的 YAML）
  └── Deployment 是工头（负责执行你的要求）
        └── ReplicaSet 是小组长（确保人数够）
              └── Pod 是工人（实际干活的）
```

你告诉 Deployment：「我要 3 个 nginx Pod」，Deployment 就会：
1. 创建一个 ReplicaSet
2. ReplicaSet 创建 3 个 Pod
3. 持续监控，如果有 Pod 挂了，自动补一个新的

### Deployment 的声明式管理

你只需要声明「我想要什么状态」，K8s 自动帮你达到那个状态。这就是**声明式管理**。

```
你说：我要 3 个 nginx Pod
K8s：好的（创建 3 个）

某个 Pod 挂了，只剩 2 个
K8s：发现不对，自动补 1 个 → 又回到 3 个

你说：我要 5 个 nginx Pod
K8s：好的（再创建 2 个）→ 变成 5 个
```

### 基础 Deployment YAML

```yaml
# nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3                    # 副本数：我要 3 个 Pod
  selector:
    matchLabels:
      app: nginx                 # 通过这个 Label 找到我管理的 Pod
  template:                      # Pod 模板（长什么样）
    metadata:
      labels:
        app: nginx               # Pod 的 Label，必须和 selector 匹配
    spec:
      containers:
        - name: nginx
          image: nginx:1.24
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "100m"        # 0.1 核 CPU
              memory: "128Mi"    # 128MB 内存
            limits:
              cpu: "250m"
              memory: "256Mi"
```

```bash
# 创建 Deployment
kubectl apply -f nginx-deployment.yaml

# 查看 Deployment
kubectl get deployments
kubectl get deploy nginx-deployment -o wide

# 查看 Deployment 管理的 ReplicaSet
kubectl get rs

# 查看 Pod
kubectl get pods -l app=nginx

# 查看详细信息
kubectl describe deploy nginx-deployment
```

### 扩缩容（Scale）

```bash
# 方法一：命令行直接改
kubectl scale deployment nginx-deployment --replicas=5

# 方法二：编辑 YAML
kubectl edit deployment nginx-deployment
# 修改 replicas: 3 → replicas: 5，保存退出即可

# 方法三：使用 kubectl scale 命令 + 条件
kubectl scale deployment nginx-deployment --replicas=5 --current-replicas=3
```

也可以在 YAML 中加 `replicas: 5` 然后 `kubectl apply -f`。

### 滚动更新（Rolling Update）

当你更新镜像版本时，Deployment 默认使用**滚动更新**策略——逐步替换旧 Pod，而不是一次性全部替换。

```
滚动更新过程（3 个 Pod，从 v1 更新到 v2）：

时间线：
  t1: Pod1(v1) Pod2(v1) Pod3(v1)     ← 初始状态
  t2: Pod1(v2) Pod2(v1) Pod3(v1)     ← 先更新 1 个
  t3: Pod1(v2) Pod2(v2) Pod3(v1)     ← 再更新 1 个
  t4: Pod1(v2) Pod2(v2) Pod3(v2)     ← 全部更新完成

整个过程中始终有 Pod 在提供服务，用户无感知！
```

```yaml
# 在 Deployment spec 中配置滚动更新策略
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 更新时最多比期望多 1 个 Pod
      maxUnavailable: 0   # 更新时不允许有 Pod 不可用（零停机）
```

```bash
# 模拟滚动更新：更新镜像版本
kubectl set image deployment/nginx-deployment nginx=nginx:1.25

# 或者修改 YAML 中的 image 字段后重新 apply
# kubectl apply -f nginx-deployment.yaml

# 观察更新过程
kubectl rollout status deployment/nginx-deployment

# 查看更新历史
kubectl rollout history deployment/nginx-deployment
```

### 回滚（Rollback）

如果新版本有问题，可以快速回滚到上一个版本。

```bash
# 回滚到上一个版本
kubectl rollout undo deployment/nginx-deployment

# 回滚到指定版本
kubectl rollout undo deployment/nginx-deployment --to-revision=2

# 查看历史版本
kubectl rollout history deployment/nginx-deployment

# 查看某个版本的详情
kubectl rollout history deployment/nginx-deployment --revision=3
```

### 其他常用操作

```bash
# 删除 Deployment（会同时删除它管理的 ReplicaSet 和 Pod）
kubectl delete deployment nginx-deployment

# 暂停 Deployment（修改多个配置时很有用，避免多次触发滚动更新）
kubectl rollout pause deployment/nginx-deployment
# ... 做多处修改 ...
kubectl rollout resume deployment/nginx-deployment

# 查看 Deployment 的 YAML（包含系统自动填充的默认值）
kubectl get deploy nginx-deployment -o yaml
```

---

## 3. Service — Pod 的「前台接待」

### 为什么需要 Service？

Pod 有两大问题：
1. **Pod IP 会变** — Pod 重建后 IP 就换了
2. **Pod 需要被访问** — 总得有个入口找到它们

**Service** 就是解决这两个问题的。它提供一个**稳定的访问入口**（固定的 IP 和 DNS），然后把流量转发到后端的 Pod。

```
类比：

  没有 Service 的情况：
  你打电话给小王（Pod IP: 10.1.1.5）→ 小王换了工位 → 打不通了！
  你得重新查号码，再打给小王（Pod IP: 10.1.1.8）→ 太麻烦了

  有 Service 的情况：
  你打公司前台电话（Service IP: 10.96.0.100）→ 前台帮你转接到小王
  小王换了工位？没关系，前台知道最新号码，你还是打前台电话就行
```

### Service 的工作原理

```
┌──────────────┐
│   Client     │
│  (调用方)     │
└──────┬───────┘
       │ 请求发往 Service (稳定的 IP:Port)
       ▼
┌──────────────┐
│   Service    │  ← kube-proxy 维护的转发规则
│ 10.96.0.100  │
└──────┬───────┘
       │ 按负载均衡策略转发
       ├──────────────────┐──────────────────┐
       ▼                  ▼                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Pod 1   │      │  Pod 2   │      │  Pod 3   │
│ 10.1.1.5 │      │ 10.1.1.6 │      │ 10.1.1.7 │
└──────────┘      └──────────┘      └──────────┘
```

### Service 类型

#### ClusterIP（默认类型）

只能在集群内部访问。最常见的类型。

```yaml
# nginx-service-clusterip.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: ClusterIP          # 默认类型，可以不写
  selector:
    app: nginx             # 通过 Label 选择后端 Pod
  ports:
    - protocol: TCP
      port: 80             # Service 暴露的端口
      targetPort: 80       # 转发到 Pod 的端口
```

```bash
kubectl apply -f nginx-service-clusterip.yaml
kubectl get svc nginx-service

# 在集群内部测试（比如用一个临时 Pod）
kubectl run tmp --rm -it --image=busybox -- sh
# 进入后执行：
wget -qO- http://nginx-service
```

#### NodePort

在每个节点上开一个端口（30000-32767），外部可以通过 `节点IP:NodePort` 访问。

```
外部用户
  │
  ▼ 访问 192.168.1.100:30080
┌──────────┐
│  Node    │
│ :30080   │ ← NodePort（每个节点都会开这个端口）
└────┬─────┘
     ▼
┌──────────┐
│ Service  │
│  :80     │
└────┬─────┘
     ▼
┌──────────┐
│   Pod    │
│  :80     │
└──────────┘
```

```yaml
# nginx-service-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80            # Service 端口
      targetPort: 80      # Pod 端口
      nodePort: 30080     # 节点端口（不指定则随机分配）
```

```bash
kubectl apply -f nginx-service-nodeport.yaml
kubectl get svc nginx-nodeport

# 通过任意节点的 IP + NodePort 访问
curl http://<节点IP>:30080
```

#### LoadBalancer

在 NodePort 基础上，还会请求云厂商创建一个外部负载均衡器（如 AWS ELB）。适合在云环境中使用。

```yaml
# nginx-service-lb.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-lb
spec:
  type: LoadBalancer
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

> **注意：** 在裸机/本地集群中使用 LoadBalancer 类型，需要安装 MetalLB 之类的插件才有外部 IP。云厂商（AWS/GKE/AKS）会自动分配。

#### ExternalName

将 Service 映射到一个外部域名，不代理任何 Pod。相当于一个 DNS 别名。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com    # 映射到这个外部域名
```

```
集群内访问 external-db → DNS 解析到 db.example.com
```

### Service 的 DNS

K8s 集群内有内置的 DNS 服务（CoreDNS），Service 会自动注册 DNS 记录。

```
DNS 格式：<service-name>.<namespace>.svc.cluster.local

例如：
  nginx-service.default.svc.cluster.local   ← 完整域名
  nginx-service.default                      ← 省略后缀
  nginx-service                              ← 同 namespace 下可以省略
```

```bash
# 在集群内 Pod 中测试 DNS
kubectl run tmp --rm -it --image=busybox -- sh
nslookup nginx-service
wget -qO- http://nginx-service
```

### Service 常用命令

```bash
# 查看所有 Service
kubectl get svc

# 查看详情
kubectl describe svc nginx-service

# 查看 Endpoints（Service 关联的 Pod IP 列表）
kubectl get endpoints nginx-service

# 删除 Service
kubectl delete svc nginx-service
```

---

## 4. ConfigMap — 配置的「便签本」

### 什么是 ConfigMap？

ConfigMap 用来存储**非机密的**配置数据，以键值对的形式存在。它把配置和镜像分离，这样同一个镜像可以在不同环境（dev/staging/prod）使用不同配置。

```
类比：

  没有 ConfigMap：每个房间装修时就把灯的颜色定死了（硬编码在镜像里）
  有 ConfigMap：  灯的颜色写在一张便签上，不同房间贴不同颜色的便签（配置外置）
```

### 创建 ConfigMap

#### 方法一：命令行创建

```bash
# 从键值对创建
kubectl create configmap app-config \
  --from-literal=APP_ENV=production \
  --from-literal=APP_DEBUG=false

# 从文件创建
echo "server {
  listen 80;
  server_name localhost;
  location / {
    root /usr/share/nginx/html;
    index index.html;
  }
}" > default.conf

kubectl create configmap nginx-config --from-file=default.conf

# 从目录创建（目录下每个文件变成一个 key）
kubectl create configmap config-dir --from-file=./config/

# 查看
kubectl get configmap app-config -o yaml
```

#### 方法二：YAML 创建

```yaml
# app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  APP_DEBUG: "false"
  DATABASE_HOST: "mysql.default.svc.cluster.local"
  DATABASE_PORT: "3306"
  # 也可以存多行内容
  nginx.conf: |
    server {
      listen 80;
      server_name localhost;
      location / {
        root /usr/share/nginx/html;
        index index.html;
      }
    }
```

```bash
kubectl apply -f app-config.yaml
kubectl get configmap app-config -o yaml
```

### 在 Pod 中使用 ConfigMap

#### 方式一：作为环境变量

```yaml
# pod-with-configmap-env.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "echo ENV=$APP_ENV DEBUG=$APP_DEBUG && sleep 3600"]
      envFrom:
        - configMapRef:
            name: app-config        # 导入整个 ConfigMap 的所有 key
      env:
        - name: DATABASE_PORT       # 只导入某一个 key，并重命名
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PORT
```

```bash
kubectl apply -f pod-with-configmap-env.yaml
kubectl logs app-pod
# 输出：ENV=production DEBUG=false
```

#### 方式二：挂载为文件

```yaml
# pod-with-configmap-volume.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-with-config
spec:
  containers:
    - name: nginx
      image: nginx:1.24
      volumeMounts:
        - name: nginx-conf
          mountPath: /etc/nginx/conf.d    # 挂载到这个目录
          readOnly: true
  volumes:
    - name: nginx-conf
      configMap:
        name: app-config
        items:
          - key: nginx.conf
            path: default.conf            # 文件名变为 default.conf
```

```bash
kubectl apply -f pod-with-configmap-volume.yaml
kubectl exec nginx-with-config -- cat /etc/nginx/conf.d/default.conf
```

### 热更新（不重启 Pod 更新配置）

当 ConfigMap 以 Volume 方式挂载时，修改 ConfigMap 后，文件内容会**自动更新**（通常延迟 1-2 分钟）。

```bash
# 修改 ConfigMap
kubectl edit configmap app-config
# 或者
kubectl apply -f updated-app-config.yaml

# 等一会儿，Pod 中的文件内容会自动更新
kubectl exec nginx-with-config -- cat /etc/nginx/conf.d/default.conf
```

> **注意：** 以环境变量方式引用的 ConfigMap 不会自动更新，因为环境变量在 Pod 启动时就注入了，需要重启 Pod。

---

## 5. Secret — 配置的「保险箱」

### 什么是 Secret？

Secret 和 ConfigMap 类似，但专门用来存储**敏感信息**，如密码、Token、证书等。数据以 Base64 编码存储（注意：Base64 不是加密，只是编码）。

```
类比：

  ConfigMap = 贴在墙上的便利贴（谁都能看）
  Secret    = 放在保险箱里的纸条（有基本保护，但仍需小心）
```

### 创建 Secret

```bash
# 方法一：命令行（推荐，密码不会留在 YAML 文件中）
kubectl create secret generic db-secret \
  --from-literal=DB_USER=admin \
  --from-literal=DB_PASSWORD=MyS3cretP@ss

# 方法二：从文件创建
kubectl create secret generic tls-secret \
  --from-file=tls.crt=./server.crt \
  --from-file=tls.key=./server.key
```

```yaml
# 方法三：YAML（data 字段的值需要 Base64 编码）
# 先编码：echo -n 'MyS3cretP@ss' | base64
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  DB_USER: YWRtaW4=            # echo -n 'admin' | base64
  DB_PASSWORD: TXlTM2NyZXRQQHNz  # echo -n 'MyS3cretP@ss' | base64
```

```bash
kubectl get secret db-secret -o yaml
# 注意：显示的是 Base64 编码后的值
# 解码查看：kubectl get secret db-secret -o jsonpath='{.data.DB_PASSWORD}' | base64 -d
```

### 在 Pod 中使用 Secret

和 ConfigMap 几乎一样，也是环境变量和挂载文件两种方式。

```yaml
# pod-with-secret.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-secret
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "echo User=$DB_USER && sleep 3600"]
      envFrom:
        - secretRef:
            name: db-secret       # 从 Secret 导入所有 key 作为环境变量
```

```bash
kubectl apply -f pod-with-secret.yaml
kubectl logs app-with-secret
# 输出：User=admin
```

### Secret vs ConfigMap

| 特性 | ConfigMap | Secret |
|------|-----------|--------|
| 用途 | 存储非敏感配置 | 存储敏感信息 |
| 数据编码 | 明文 | Base64 编码 |
| 典型内容 | 配置文件、环境变量 | 密码、Token、证书 |
| 挂载方式 | 环境变量 / Volume | 环境变量 / Volume |
| 使用限制 | 无 | 可以配置 RBAC 权限控制 |

> **最佳实践：** 生产环境中建议配合 RBAC 控制 Secret 的访问权限，或使用外部密钥管理工具（如 HashiCorp Vault、AWS Secrets Manager）。

---

## 6. 实战：完整的 Nginx 部署流程

把前面学的所有内容串起来，完成一个完整的部署。

### 第一步：创建 ConfigMap（自定义 Nginx 配置）

```yaml
# nginx-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-custom-config
data:
  default.conf: |
    server {
      listen 80;
      server_name localhost;

      location / {
        root /usr/share/nginx/html;
        index index.html;
      }

      location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
      }
    }
  index.html: |
    <!DOCTYPE html>
    <html>
    <head><title>K8s Nginx Demo</title></head>
    <body>
      <h1>Hello from Kubernetes!</h1>
      <p>Pod Name: $(HOSTNAME)</p>
      <p>Version: v1.0</p>
    </body>
    </html>
```

```bash
kubectl apply -f nginx-configmap.yaml
```

### 第二步：创建 Deployment

```yaml
# nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
  labels:
    app: nginx
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: nginx
        version: v1
    spec:
      containers:
        - name: nginx
          image: nginx:1.24
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "200m"
              memory: "256Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 3
            periodSeconds: 5
          volumeMounts:
            - name: nginx-conf
              mountPath: /etc/nginx/conf.d
            - name: html-content
              mountPath: /usr/share/nginx/html
      volumes:
        - name: nginx-conf
          configMap:
            name: nginx-custom-config
            items:
              - key: default.conf
                path: default.conf
        - name: html-content
          configMap:
            name: nginx-custom-config
            items:
              - key: index.html
                path: index.html
```

```bash
kubectl apply -f nginx-deployment.yaml

# 检查状态
kubectl get deploy nginx-app
kubectl get pods -l app=nginx
```

### 第三步：创建 Service

```yaml
# nginx-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-svc
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
      nodePort: 30080
```

```bash
kubectl apply -f nginx-service.yaml

# 验证
kubectl get svc nginx-svc

# 访问测试
curl http://<节点IP>:30080
curl http://<节点IP>:30080/health
```

### 第四步：滚动更新

```bash
# 更新镜像到 1.25
kubectl set image deployment/nginx-app nginx=nginx:1.25

# 查看更新过程
kubectl rollout status deployment/nginx-app

# 确认更新
kubectl get deploy nginx-app -o wide
```

### 第五步：回滚（如果新版本有问题）

```bash
# 发现 1.25 有问题，回滚到上一个版本
kubectl rollout undo deployment/nginx-app

# 确认回滚成功
kubectl get deploy nginx-app -o wide
# 镜像应该变回 nginx:1.24

# 查看更新历史
kubectl rollout history deployment/nginx-app
```

### 第六步：扩缩容

```bash
# 扩容到 5 个副本
kubectl scale deployment nginx-app --replicas=5

# 确认
kubectl get pods -l app=nginx
# 应该有 5 个 Pod

# 缩容到 2 个副本
kubectl scale deployment nginx-app --replicas=2
```

### 第七步：清理

```bash
kubectl delete -f nginx-service.yaml
kubectl delete -f nginx-deployment.yaml
kubectl delete -f nginx-configmap.yaml
```

---

## 总结

```
┌─────────────────────────────────────────────────────┐
│                  K8s 核心资源关系图                    │
│                                                     │
│  你（YAML/命令）                                      │
│    │                                                │
│    ▼                                                │
│  Deployment ──selector:app=nginx──┐                 │
│    │                              │                 │
│    │ 创建/管理                     │ 选择             │
│    ▼                              ▼                 │
│  ReplicaSet                   Service               │
│    │                           (ClusterIP/NodePort) │
│    │ 创建/管理                     │                  │
│    ▼                              │ 转发流量          │
│  Pod ◄───────────────────────────┘                  │
│    │                                                │
│    │ 挂载配置                                        │
│    ▼                                                │
│  ConfigMap / Secret                                 │
└─────────────────────────────────────────────────────┘
```

| 资源 | 作用 | 类比 |
|------|------|------|
| Label/Selector | 标记和筛选资源 | 便利贴 + 按标签找人 |
| Deployment | 管理 Pod 副本、滚动更新、回滚 | 工头 |
| Service | 提供稳定的访问入口和负载均衡 | 前台接待 |
| ConfigMap | 存储非敏感配置 | 便签本 |
| Secret | 存储敏感信息 | 保险箱 |

**下一篇：** 我们将学习 Ingress（入口控制器）、Volume（存储卷）、Namespace（命名空间）等更多 K8s 资源。
