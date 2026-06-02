# Kubernetes 常用命令速查表

## 1. 集群与上下文

```bash
# 查看集群信息
kubectl cluster-info
kubectl version --short
kubectl get nodes

# 上下文管理
kubectl config get-contexts                  # 列出上下文
kubectl config use-context my-cluster        # 切换上下文
kubectl config current-context               # 当前上下文

# 查看所有命名空间的资源
kubectl get pods --all-namespaces
kubectl get pods -A                          # 简写
```

---

## 2. 资源管理（CRUD）

### 查看资源
```bash
# 基本查看
kubectl get pods
kubectl get pods -n my-namespace             # 指定命名空间
kubectl get pods -o wide                     # 显示更多信息（IP、节点）
kubectl get pods -o yaml                     # YAML 格式
kubectl get pods -o json                     # JSON 格式

# 过滤和排序
kubectl get pods -l app=web                  # 按标签过滤
kubectl get pods --field-selector status.phase=Running
kubectl get pods --sort-by='.status.startTime'

# 常用资源简写
#   pods → po
#   services → svc
#   deployments → deploy
#   replicasets → rs
#   statefulsets → sts
#   daemonsets → ds
#   configmaps → cm
#   persistentvolumeclaims → pvc
#   namespaces → ns
#   nodes → no
#   ingresses → ing

kubectl get deploy,svc,po                     # 同时查看多种资源
kubectl get all -n my-namespace               # 命名空间下所有资源

# 查看详情
kubectl describe pod web-xxx
kubectl describe svc web
kubectl describe node node-1
```

### 创建资源
```bash
# 从 YAML 创建
kubectl apply -f deployment.yml
kubectl apply -f ./manifests/                 # 整个目录
kubectl apply -f https://example.com/app.yml  # URL

# 快速创建（命令行）
kubectl create deployment nginx --image=nginx:1.25 --replicas=3
kubectl create service clusterip web --tcp=80:8080
kubectl create namespace dev
kubectl create secret generic db-pass --from-literal=password=mysecret
kubectl create configmap app-config --from-file=config.yml

# 快速暴露服务
kubectl expose deployment nginx --port=80 --type=LoadBalancer
```

### 更新资源
```bash
# 修改后重新应用
kubectl apply -f updated-deployment.yml

# 直接编辑（打开编辑器）
kubectl edit deployment web

# 命令行修改
kubectl scale deployment web --replicas=5
kubectl set image deployment/web web=nginx:1.26
kubectl annotate pod web description="my pod"
kubectl label pod web env=production

# 滚动更新
kubectl rollout restart deployment web
kubectl rollout status deployment web        # 查看滚动状态
kubectl rollout history deployment web       # 更新历史
kubectl rollout undo deployment web          # 回滚到上一个版本
kubectl rollout undo deployment web --to-revision=2  # 回滚到指定版本
```

### 删除资源
```bash
kubectl delete pod web-xxx
kubectl delete -f deployment.yml
kubectl delete pods --all                    # 删除所有 Pod
kubectl delete pods -l app=web               # 按标签删除
kubectl delete namespace dev                 # 删除命名空间（及其下所有资源）

# 强制删除卡住的 Pod
kubectl delete pod web-xxx --grace-period=0 --force
```

---

## 3. 调试与排查

### 日志查看
```bash
# 查看 Pod 日志
kubectl logs web-xxx
kubectl logs web-xxx -f                       # 实时跟踪
kubectl logs web-xxx --tail=100               # 最后 100 行
kubectl logs web-xxx --previous               # 上一个容器的日志
kubectl logs web-xxx -c sidecar               # 多容器 Pod 指定容器

# 查看标签匹配的所有 Pod 日志
kubectl logs -l app=web --all-containers

# 查看所有 Pod 日志（慎用）
kubectl logs --all-containers -A --tail=10
```

### 进入容器
```bash
# 交互式 shell
kubectl exec -it web-xxx -- bash
kubectl exec -it web-xxx -- sh               # 无 bash 时
kubectl exec -it web-xxx -c sidecar -- bash  # 多容器 Pod

# 执行单个命令
kubectl exec web-xxx -- cat /etc/nginx/nginx.conf
kubectl exec web-xxx -- env
```

### 文件复制
```bash
# 从 Pod 复制到本地
kubectl cp my-namespace/web-xxx:/app/logs/app.log ./app.log

# 从本地复制到 Pod
kubectl cp ./config.yml my-namespace/web-xxx:/app/config.yml
```

### 资源监控
```bash
# 查看 Pod 资源使用（需要 metrics-server）
kubectl top pods
kubectl top pods -n my-namespace --sort-by=memory
kubectl top nodes
```

### 常见问题排查
```bash
# Pod 一直 Pending
kubectl describe pod web-xxx          # 看 Events
kubectl get events --sort-by=.metadata.creationTimestamp

# Pod CrashLoopBackOff
kubectl logs web-xxx --previous       # 看崩溃前的日志
kubectl describe pod web-xxx          # 看退出码

# 服务无法访问
kubectl get svc web                   # 确认 Service
kubectl get endpoints web             # 确认 Endpoints 是否有地址
kubectl describe svc web              # 看 Selector 是否匹配

# 节点问题
kubectl describe node node-1          # 看 Conditions
kubectl get events --field-selector involvedObject.kind=Node
```

---

## 4. 部署相关

### Deployment
```bash
# 创建 Deployment
kubectl create deployment web --image=nginx:1.25 --replicas=3
kubectl apply -f deployment.yml

# 扩缩容
kubectl scale deployment web --replicas=5

# 自动扩缩容（HPA）
kubectl autoscale deployment web --min=2 --max=10 --cpu-percent=80
kubectl get hpa
kubectl delete hpa web

# 更新镜像
kubectl set image deployment/web web=nginx:1.26

# 查看滚动更新状态
kubectl rollout status deployment web
kubectl rollout history deployment web
kubectl rollout undo deployment web
```

### Service
```bash
# 创建 Service
kubectl expose deployment web --port=80 --type=ClusterIP
kubectl expose deployment web --port=80 --type=NodePort
kubectl expose deployment web --port=80 --type=LoadBalancer

# 查看 Service
kubectl get svc
kubectl describe svc web
kubectl get endpoints web
```

### Ingress
```bash
# 查看 Ingress
kubectl get ingress
kubectl describe ingress web-ingress
```

---

## 5. 配置与密钥

### ConfigMap
```bash
# 从字面值创建
kubectl create configmap app-config --from-literal=APP_ENV=production

# 从文件创建
kubectl create configmap nginx-config --from-file=nginx.conf

# 查看
kubectl get cm
kubectl describe cm app-config
kubectl get cm app-config -o yaml
```

### Secret
```bash
# 创建 Secret
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=s3cr3t

# 从文件创建
kubectl create secret generic tls-secret \
  --from-file=tls.crt=./cert.pem \
  --from-file=tls.key=./key.pem

# 查看（值是 base64 编码的）
kubectl get secrets
kubectl get secret db-secret -o yaml
kubectl get secret db-secret -o jsonpath='{.data.password}' | base64 -d
```

---

## 6. 命名空间管理

```bash
# 创建/查看/删除
kubectl create namespace dev
kubectl get namespaces
kubectl delete namespace dev

# 切换默认命名空间（需安装 kubens）
kubens dev

# 在命名空间间切换上下文
kubectl config set-context --current --namespace=dev
```

---

## 7. 实用技巧

```bash
# 等待 Pod 就绪
kubectl wait --for=condition=ready pod -l app=web --timeout=120s

# 端口转发（本地调试）
kubectl port-forward svc/web 8080:80
kubectl port-forward pod/web-xxx 8080:80

# 快速生成 YAML 模板（dry-run）
kubectl create deployment web --image=nginx --dry-run=client -o yaml
kubectl run test --image=busybox --dry-run=client -o yaml -- sleep 3600
kubectl expose deployment web --port=80 --dry-run=client -o yaml

# JSONPath 查询
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'

# 批量操作
kubectl delete pods -l app=test
kubectl get pods -o name | xargs kubectl delete

# 查看集群资源配额
kubectl get resourcequota -n my-namespace
kubectl get limitrange -n my-namespace
```
