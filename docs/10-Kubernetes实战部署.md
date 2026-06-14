# 第十篇：Kubernetes 实战部署

> 本篇将通过一个完整的实战项目，带你从零部署一个包含前端、后端、数据库和缓存的全栈应用到 Kubernetes 集群。

## 目录

- [一、项目架构概览](#一项目架构概览)
- [二、准备应用代码和 Dockerfile](#二准备应用代码和-dockerfile)
- [三、创建 Namespace](#三创建-namespace)
- [四、创建 ConfigMap 和 Secret](#四创建-configmap-和-secret)
- [五、部署 PostgreSQL](#五部署-postgresql)
- [六、部署 Redis](#六部署-redis)
- [七、部署后端 API](#七部署后端-api)
- [八、部署前端](#八部署前端)
- [九、配置 Ingress](#九配置-ingress)
- [十、验证和调试](#十验证和调试)
- [十一、K8s 运维常用操作](#十一k8s-运维常用操作)

---

## 一、项目架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    Ingress (nginx)                       │
│                   /           /api                       │
├───────────────────┴───────────┴─────────────────────────┤
│                                                         │
│  ┌──────────────┐              ┌──────────────────┐     │
│  │   Frontend    │   ──────>   │    Backend API    │     │
│  │  (React/Nginx)│              │   (Python Flask)  │     │
│  │  :80          │              │   :5000           │     │
│  └──────────────┘              └────────┬─────────┘     │
│                                         │               │
│                              ┌──────────┴──────────┐    │
│                              │                     │    │
│                     ┌────────▼───────┐  ┌──────────▼──┐ │
│                     │  PostgreSQL     │  │    Redis     │ │
│                     │  :5432          │  │    :6379     │ │
│                     └────────────────┘  └─────────────┘ │
│                                                         │
│              Namespace: myapp                           │
└─────────────────────────────────────────────────────────┘
```

**技术栈：**

| 组件 | 技术 | 端口 |
|------|------|------|
| 前端 | React + Nginx | 80 |
| 后端 | Python Flask | 5000 |
| 数据库 | PostgreSQL | 5432 |
| 缓存 | Redis | 6379 |

---

## 二、准备应用代码和 Dockerfile

### 2.1 后端 Flask 应用

创建项目目录：

```bash
mkdir -p /tmp/myapp/{backend,frontend}
```

**后端代码** — `/tmp/myapp/backend/app.py`：

```python
import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import redis

app = Flask(__name__)
CORS(app)

# 数据库连接配置
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'myapp'),
    'user': os.environ.get('DB_USER', 'myapp'),
    'password': os.environ.get('DB_PASSWORD', 'myapp123')
}

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))


def get_db():
    """获取数据库连接"""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def get_redis():
    """获取 Redis 连接"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def init_db():
    """初始化数据库表"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")


@app.route('/api/health')
def health():
    """健康检查接口"""
    status = {'status': 'ok', 'service': 'backend'}

    # 检查数据库
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        status['database'] = 'connected'
    except Exception as e:
        status['database'] = f'error: {str(e)}'
        status['status'] = 'degraded'

    # 检查 Redis
    try:
        r = get_redis()
        r.ping()
        status['cache'] = 'connected'
    except Exception as e:
        status['cache'] = f'error: {str(e)}'
        status['status'] = 'degraded'

    return jsonify(status)


@app.route('/api/todos', methods=['GET'])
def get_todos():
    """获取所有待办事项（带 Redis 缓存）"""
    r = get_redis()

    # 尝试从缓存获取
    cached = r.get('todos:all')
    if cached:
        return jsonify({'source': 'cache', 'data': json.loads(cached)})

    # 从数据库获取
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, title, completed, created_at FROM todos ORDER BY id DESC')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    todos = [
        {'id': r[0], 'title': r[1], 'completed': r[2], 'created_at': str(r[3])}
        for r in rows
    ]

    # 写入缓存，60 秒过期
    r.setex('todos:all', 60, json.dumps(todos))

    return jsonify({'source': 'database', 'data': todos})


@app.route('/api/todos', methods=['POST'])
def create_todo():
    """创建待办事项"""
    data = request.get_json()
    title = data.get('title', '').strip()

    if not title:
        return jsonify({'error': '标题不能为空'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO todos (title) VALUES (%s) RETURNING id', (title,))
    todo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # 清除缓存
    r = get_redis()
    r.delete('todos:all')

    return jsonify({'id': todo_id, 'title': title, 'completed': False}), 201


@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """删除待办事项"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM todos WHERE id = %s', (todo_id,))
    conn.commit()
    cur.close()
    conn.close()

    # 清除缓存
    r = get_redis()
    r.delete('todos:all')

    return jsonify({'message': '已删除'})


@app.route('/api/info')
def info():
    """返回服务信息（用于演示负载均衡）"""
    import socket
    return jsonify({
        'hostname': socket.gethostname(),
        'pod_ip': socket.gethostbyname(socket.gethostname()),
        'service': 'backend-api',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**后端依赖** — `/tmp/myapp/backend/requirements.txt`：

```
flask==3.0.0
flask-cors==4.0.0
psycopg2-binary==2.9.9
redis==5.0.1
gunicorn==21.2.0
```

**后端 Dockerfile** — `/tmp/myapp/backend/Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

### 2.2 前端 React 应用

**前端代码** — `/tmp/myapp/frontend/src/App.js`：

```jsx
import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = '/api';

function App() {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');
  const [health, setHealth] = useState(null);
  const [info, setInfo] = useState(null);

  const fetchTodos = async () => {
    try {
      const res = await fetch(`${API_BASE}/todos`);
      const data = await res.json();
      setTodos(data.data || []);
    } catch (err) {
      console.error('获取待办失败:', err);
    }
  };

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      setHealth(await res.json());
      const res2 = await fetch(`${API_BASE}/info`);
      setInfo(await res2.json());
    } catch (err) {
      setHealth({ status: 'error', message: err.message });
    }
  };

  useEffect(() => {
    fetchTodos();
    checkHealth();
  }, []);

  const addTodo = async (e) => {
    e.preventDefault();
    if (!newTodo.trim()) return;
    await fetch(`${API_BASE}/todos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTodo })
    });
    setNewTodo('');
    fetchTodos();
  };

  const deleteTodo = async (id) => {
    await fetch(`${API_BASE}/todos/${id}`, { method: 'DELETE' });
    fetchTodos();
  };

  return (
    <div className="App">
      <h1>🐳 K8s 全栈应用</h1>

      <div className="status-panel">
        <h3>服务状态</h3>
        <p>API: <span className={health?.status === 'ok' ? 'ok' : 'error'}>
          {health?.status || 'checking...'}
        </span></p>
        <p>数据库: {health?.database || '-'}</p>
        <p>缓存: {health?.cache || '-'}</p>
        {info && <p>Pod: {info.hostname} ({info.pod_ip})</p>}
      </div>

      <form onSubmit={addTodo} className="add-form">
        <input
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          placeholder="添加待办事项..."
        />
        <button type="submit">添加</button>
      </form>

      <ul className="todo-list">
        {todos.map(todo => (
          <li key={todo.id}>
            <span>{todo.title}</span>
            <button onClick={() => deleteTodo(todo.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
```

**前端 Dockerfile** — `/tmp/myapp/frontend/Dockerfile`：

```dockerfile
# 构建阶段
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Nginx 配置** — `/tmp/myapp/frontend/nginx.conf`：

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend-api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 2.3 构建并推送镜像

```bash
# 构建后端镜像
cd /tmp/myapp/backend
docker build -t myapp-backend:v1 .
# 如果使用远程仓库，需要推送
# docker tag myapp-backend:v1 your-registry/myapp-backend:v1
# docker push your-registry/myapp-backend:v1

# 构建前端镜像
cd /tmp/myapp/frontend
docker build -t myapp-frontend:v1 .
# docker tag myapp-frontend:v1 your-registry/myapp-frontend:v1
# docker push your-registry/myapp-frontend:v1
```

> **提示：** 如果使用 Minikube，可以用 `eval $(minikube docker-env)` 让 Minikube 直接访问本地镜像，无需推送。

---

## 三、创建 Namespace

将所有资源放在独立的命名空间中，便于管理和隔离。

**创建 YAML 文件** — `k8s/00-namespace.yaml`：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
  labels:
    app: myapp
    env: dev
```

**执行命令：**

```bash
# 创建所有 K8s 配置文件目录
mkdir -p /tmp/myapp/k8s

# 应用配置
kubectl apply -f k8s/00-namespace.yaml

# 验证
kubectl get namespace myapp
```

**预期输出：**

```
NAME    STATUS   AGE
myapp   Active   5s
```

---

## 四、创建 ConfigMap 和 Secret

### 4.1 ConfigMap — 应用配置

**YAML 文件** — `k8s/01-configmap.yaml`：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: myapp
data:
  # 后端配置
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "myapp"
  DB_USER: "myapp"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  FLASK_ENV: "production"
  # 前端 Nginx 配置也可以放在这里
  nginx.conf: |
    server {
        listen 80;
        server_name localhost;
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
        location /api/ {
            proxy_pass http://backend-api:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
```

### 4.2 Secret — 敏感信息

**YAML 文件** — `k8s/02-secret.yaml`：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
  namespace: myapp
type: Opaque
data:
  # echo -n 'myapp123' | base64
  DB_PASSWORD: bXlhcHAxMjM=
  # echo -n '' | base64  (Redis 无密码，留空)
  REDIS_PASSWORD: ""
```

> **注意：** Secret 中的值必须是 Base64 编码。使用 `echo -n 'your-password' | base64` 生成。

**执行命令：**

```bash
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml

# 验证
kubectl get configmap -n myapp
kubectl get secret -n myapp

# 查看 ConfigMap 内容
kubectl describe configmap app-config -n myapp

# 查看 Secret（解码）
kubectl get secret app-secret -n myapp -o jsonpath='{.data.DB_PASSWORD}' | base64 -d
```

---

## 五、部署 PostgreSQL

**YAML 文件** — `k8s/03-postgres.yaml`：

```yaml
# ---------- 持久化存储 ----------
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: myapp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  # storageClassName: standard  # 根据集群环境取消注释

---
# ---------- Deployment ----------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: myapp
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  strategy:
    type: Recreate          # 数据库不适合滚动更新
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_NAME
            - name: POSTGRES_USER
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secret
                  key: DB_PASSWORD
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "myapp"]
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "myapp"]
            initialDelaySeconds: 15
            periodSeconds: 20
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc

---
# ---------- Service ----------
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: myapp
  labels:
    app: postgres
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

**执行命令：**

```bash
kubectl apply -f k8s/03-postgres.yaml

# 等待 Pod 启动
kubectl get pods -n myapp -w

# 验证数据库
kubectl exec -it deploy/postgres -n myapp -- psql -U myapp -d myapp -c "\dt"
```

**预期输出：**

```
NAME                       READY   STATUS    RESTARTS   AGE
postgres-7b8c9d5f4-x2k9j  1/1     Running   0          30s
```

---

## 六、部署 Redis

**YAML 文件** — `k8s/04-redis.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: myapp
  labels:
    app: redis
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
          ports:
            - containerPort: 6379
          command: ["redis-server", "--appendonly", "yes"]
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 10
            periodSeconds: 20

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: myapp
  labels:
    app: redis
spec:
  type: ClusterIP
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
```

**执行命令：**

```bash
kubectl apply -f k8s/04-redis.yaml

# 验证
kubectl get pods -n myapp -l app=redis

# 测试 Redis 连接
kubectl exec -it deploy/redis -n myapp -- redis-cli ping
```

**预期输出：**

```
PONG
```

---

## 七、部署后端 API

**YAML 文件** — `k8s/05-backend.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: myapp
  labels:
    app: backend
spec:
  replicas: 2           # 2 个副本，演示负载均衡
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
          image: myapp-backend:v1
          imagePullPolicy: IfNotPresent   # 本地镜像用 IfNotPresent
          ports:
            - containerPort: 5000
          env:
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_HOST
            - name: DB_PORT
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_PORT
            - name: DB_NAME
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_NAME
            - name: DB_USER
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DB_USER
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secret
                  key: DB_PASSWORD
            - name: REDIS_HOST
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: REDIS_HOST
            - name: REDIS_PORT
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: REDIS_PORT
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          readinessProbe:
            httpGet:
              path: /api/health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /api/health
              port: 5000
            initialDelaySeconds: 15
            periodSeconds: 20

---
apiVersion: v1
kind: Service
metadata:
  name: backend-api
  namespace: myapp
  labels:
    app: backend
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - port: 5000
      targetPort: 5000
```

**执行命令：**

```bash
kubectl apply -f k8s/05-backend.yaml

# 等待 Pod 就绪
kubectl get pods -n myapp -l app=backend -w

# 查看后端日志
kubectl logs -n myapp -l app=backend --tail=20

# 测试 API（通过 Service）
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never \
  -n myapp -- curl http://backend-api:5000/api/health
```

**预期输出：**

```json
{"cache":"connected","database":"connected","service":"backend","status":"ok"}
```

---

## 八、部署前端

**YAML 文件** — `k8s/06-frontend.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: myapp
  labels:
    app: frontend
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
          image: myapp-frontend:v1
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: myapp
  labels:
    app: frontend
spec:
  type: ClusterIP
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
```

**执行命令：**

```bash
kubectl apply -f k8s/06-frontend.yaml

# 等待就绪
kubectl get pods -n myapp -l app=frontend -w
```

---

## 九、配置 Ingress

**YAML 文件** — `k8s/07-ingress.yaml`：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: myapp
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx    # 使用 nginx ingress controller
  rules:
    - host: myapp.local      # 本地测试用域名
      http:
        paths:
          # API 请求路由到后端
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend-api
                port:
                  number: 5000
          # 其他请求路由到前端
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

**执行命令：**

```bash
# 确保 Ingress Controller 已安装
# Minikube 用户：
minikube addons enable ingress

# 其他集群：
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/cloud/deploy.yaml

kubectl apply -f k8s/07-ingress.yaml

# 查看 Ingress
kubectl get ingress -n myapp
```

**配置本地 hosts（用于测试）：**

```bash
# 获取 Ingress Controller 的 IP
# Minikube:
echo "$(minikube ip) myapp.local" | sudo tee -a /etc/hosts

# 或者用 NodePort 方式访问（如果 Ingress 不可用）：
# minikube service frontend-service -n myapp --url
```

---

## 十、验证和调试

### 10.1 完整部署检查

```bash
# 查看所有资源
kubectl get all -n myapp
```

**预期输出：**

```
NAME                            READY   STATUS    RESTARTS   AGE
pod/backend-api-xxx-abc         1/1     Running   0          5m
pod/backend-api-xxx-def         1/1     Running   0          5m
pod/frontend-xxx-ghi            1/1     Running   0          3m
pod/frontend-xxx-jkl            1/1     Running   0          3m
pod/postgres-xxx-mno            1/1     Running   0          10m
pod/redis-xxx-pqr               1/1     Running   0          8m

NAME                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/backend-api        ClusterIP   10.96.xxx.xxx   <none>        5000/TCP   5m
service/frontend-service   ClusterIP   10.96.xxx.xxx   <none>        80/TCP     3m
service/postgres-service   ClusterIP   10.96.xxx.xxx   <none>        5432/TCP   10m
service/redis-service      ClusterIP   10.96.xxx.xxx   <none>        6379/TCP   8m

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/backend    2/2     2            2           5m
deployment.apps/frontend   2/2     2            2           3m
deployment.apps/postgres   1/1     1            1           10m
deployment.apps/redis      1/1     1            1           8m
```

### 10.2 测试应用功能

```bash
# 测试后端健康检查
curl http://myapp.local/api/health

# 测试创建待办
curl -X POST http://myapp.local/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "学习 Kubernetes"}'

# 查看待办列表
curl http://myapp.local/api/todos

# 测试负载均衡（多次调用看 hostname 变化）
for i in $(seq 1 5); do curl http://myapp.local/api/info; echo; done

# 访问前端页面
curl http://myapp.local/
```

### 10.3 常见故障排查

#### Pod 处于 Pending 状态

```bash
# 查看事件
kubectl describe pod <pod-name> -n myapp

# 常见原因：
# 1. 资源不足 → 查看 Events 中的 "Insufficient cpu/memory"
# 2. PVC 未绑定 → kubectl get pvc -n myapp
# 3. 镜像拉取失败 → kubectl describe pod 查看 Events
```

#### Pod 处于 CrashLoopBackOff

```bash
# 查看日志
kubectl logs <pod-name> -n myapp
kubectl logs <pod-name> -n myapp --previous   # 查看上一次崩溃的日志

# 常见原因：
# 1. 环境变量配置错误
# 2. 数据库连接失败
# 3. 应用代码错误
```

#### ImagePullBackOff

```bash
# 查看详细信息
kubectl describe pod <pod-name> -n myapp | grep -A 5 "Events"

# 常见原因：
# 1. 镜像名/标签错误
# 2. 私有仓库需要 imagePullSecrets
# 3. 网络问题

# 如果是本地镜像，确保 imagePullPolicy 设为 IfNotPresent
# 如果使用 Minikube：
eval $(minikube docker-env)
docker build -t myapp-backend:v1 .
```

#### 服务间通信失败

```bash
# 在后端 Pod 中测试数据库连接
kubectl exec -it deploy/backend-api -n myapp -- python -c "
import psycopg2
conn = psycopg2.connect(host='postgres-service', port=5432, dbname='myapp', user='myapp', password='myapp123')
print('数据库连接成功')
"

# 在后端 Pod 中测试 Redis 连接
kubectl exec -it deploy/backend-api -n myapp -- python -c "
import redis
r = redis.Redis(host='redis-service', port=6379)
print(r.ping())
"

# 检查 Service Endpoints
kubectl get endpoints -n myapp
# 确保每个 Service 都有对应的 Endpoints 地址
```

#### DNS 解析问题

```bash
# 在 Pod 中测试 DNS
kubectl run dns-test --image=busybox --rm -it --restart=Never \
  -n myapp -- nslookup backend-api

# 期望输出包含 backend-api.myapp.svc.cluster.local 的解析结果
```

---

## 十一、K8s 运维常用操作

### 11.1 查看资源状态

```bash
# 查看所有资源
kubectl get all -n myapp

# 查看 Deployment 详情
kubectl describe deployment backend-api -n myapp

# 查看 Pod 详细信息
kubectl describe pod <pod-name> -n myapp

# 查看事件（按时间排序）
kubectl get events -n myapp --sort-by='.lastTimestamp'

# 查看资源使用情况（需要 metrics-server）
kubectl top pods -n myapp
kubectl top nodes

# 查看 Service 的 Endpoints
kubectl get endpoints backend-api -n myapp

# 查看 Ingress
kubectl describe ingress myapp-ingress -n myapp
```

### 11.2 查看日志

```bash
# 查看单个 Pod 日志
kubectl logs <pod-name> -n myapp

# 实时跟踪日志
kubectl logs -f <pod-name> -n myapp

# 查看最近 100 行
kubectl logs --tail=100 <pod-name> -n myapp

# 查看指定时间段日志
kubectl logs --since=1h <pod-name> -n myapp

# 查看 Deployment 下所有 Pod 日志
kubectl logs -l app=backend -n myapp

# 多容器 Pod 指定容器
kubectl logs <pod-name> -c <container-name> -n myapp

# 查看上一个崩溃容器的日志
kubectl logs --previous <pod-name> -n myapp
```

### 11.3 进入 Pod 调试

```bash
# 进入 Pod 的 shell
kubectl exec -it <pod-name> -n myapp -- /bin/sh

# 在 Pod 中执行单条命令
kubectl exec <pod-name> -n myapp -- env
kubectl exec <pod-name> -n myapp -- cat /etc/resolv.conf

# 使用临时容器调试（K8s 1.23+）
kubectl debug -it <pod-name> -n myapp --image=busybox

# 创建一个临时 Pod 用于网络测试
kubectl run debug --image=busybox --rm -it --restart=Never \
  -n myapp -- wget -qO- http://backend-api:5000/api/health
```

### 11.4 扩缩容

```bash
# 手动扩容
kubectl scale deployment backend-api -n myapp --replicas=4

# 手动缩容
kubectl scale deployment backend-api -n myapp --replicas=2

# 查看当前副本数
kubectl get deployment backend-api -n myapp

# 配置自动扩缩容（需要 metrics-server）
kubectl autoscale deployment backend-api -n myapp \
  --min=2 --max=5 --cpu-percent=70

# 查看 HPA 状态
kubectl get hpa -n myapp
```

### 11.5 滚动更新

```bash
# 更新镜像版本
kubectl set image deployment/backend-api backend=myapp-backend:v2 -n myapp

# 查看更新状态
kubectl rollout status deployment/backend-api -n myapp

# 查看更新历史
kubectl rollout history deployment/backend-api -n myapp

# 查看某次修订的详情
kubectl rollout history deployment/backend-api -n myapp --revision=2
```

**滚动更新策略配置（写在 Deployment spec 中）：**

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 最多多出 1 个 Pod
      maxUnavailable: 0   # 更新过程中不允许有不可用的 Pod
  minReadySeconds: 10    # Pod 就绪后等待 10 秒再继续更新
```

### 11.6 回滚

```bash
# 回滚到上一个版本
kubectl rollout undo deployment/backend-api -n myapp

# 回滚到指定版本
kubectl rollout undo deployment/backend-api -n myapp --to-revision=1

# 回滚前先查看历史
kubectl rollout history deployment/backend-api -n myapp
```

### 11.7 资源清理

```bash
# 删除单个资源
kubectl delete service backend-api -n myapp

# 删除 YAML 文件中定义的所有资源
kubectl delete -f k8s/05-backend.yaml

# 删除整个 Namespace（删除所有资源）
kubectl delete namespace myapp

# 删除所有 YAML 定义的资源（按创建相反顺序）
kubectl delete -f k8s/07-ingress.yaml
kubectl delete -f k8s/06-frontend.yaml
kubectl delete -f k8s/05-backend.yaml
kubectl delete -f k8s/04-redis.yaml
kubectl delete -f k8s/03-postgres.yaml
kubectl delete -f k8s/02-secret.yaml
kubectl delete -f k8s/01-configmap.yaml
kubectl delete -f k8s/00-namespace.yaml

# 或者一次性删除整个 k8s 目录（推荐）
kubectl delete -f k8s/ --recursive

# 强制删除卡住的 Pod
kubectl delete pod <pod-name> -n myapp --grace-period=0 --force

# 删除所有已完成的 Pod
kubectl delete pods --field-selector status.phase=Succeeded -n myapp
```

### 11.8 一键部署与清理脚本

**部署脚本** — `k8s/deploy.sh`：

```bash
#!/bin/bash
set -e

NAMESPACE="myapp"
K8S_DIR="$(dirname "$0")"

echo "🚀 开始部署应用到 Kubernetes..."

# 构建镜像（使用 Minikube Docker 环境）
echo "📦 构建镜像..."
if command -v minikube &> /dev/null; then
    eval $(minikube docker-env)
fi

cd "$(dirname "$K8S_DIR")/backend"
docker build -t myapp-backend:v1 .

cd "$(dirname "$K8S_DIR")/frontend"
docker build -t myapp-frontend:v1 .

cd "$K8S_DIR"

# 按顺序部署
echo "📋 创建 Namespace 和配置..."
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-configmap.yaml
kubectl apply -f 02-secret.yaml

echo "🗄️  部署 PostgreSQL..."
kubectl apply -f 03-postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=120s

echo "⚡ 部署 Redis..."
kubectl apply -f 04-redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=60s

echo "🔧 部署后端 API..."
kubectl apply -f 05-backend.yaml
kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=120s

echo "🌐 部署前端..."
kubectl apply -f 06-frontend.yaml
kubectl wait --for=condition=ready pod -l app=frontend -n $NAMESPACE --timeout=60s

echo "🌍 配置 Ingress..."
kubectl apply -f 07-ingress.yaml

echo ""
echo "✅ 部署完成！"
echo ""
kubectl get all -n $NAMESPACE
```

**清理脚本** — `k8s/cleanup.sh`：

```bash
#!/bin/bash
set -e

NAMESPACE="myapp"
K8S_DIR="$(dirname "$0")"

echo "🧹 清理 Kubernetes 资源..."
kubectl delete namespace $NAMESPACE --wait=true
echo "✅ 清理完成！"
```

```bash
# 设置执行权限
chmod +x k8s/deploy.sh k8s/cleanup.sh

# 一键部署
./k8s/deploy.sh

# 一键清理
./k8s/cleanup.sh
```

---

## 文件清单

```
myapp/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── App.js
│   ├── nginx.conf
│   └── Dockerfile
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-configmap.yaml
    ├── 02-secret.yaml
    ├── 03-postgres.yaml
    ├── 04-redis.yaml
    ├── 05-backend.yaml
    ├── 06-frontend.yaml
    ├── 07-ingress.yaml
    ├── deploy.sh
    └── cleanup.sh
```

---

## 小结

| 知识点 | 要点 |
|--------|------|
| Namespace | 资源隔离，便于管理 |
| ConfigMap/Secret | 配置与密钥分离管理 |
| Deployment | 无状态应用部署，支持滚动更新和回滚 |
| Service | 服务发现与负载均衡（ClusterIP） |
| PVC | 持久化存储 |
| Ingress | HTTP/HTTPS 路由 |
| Probes | 健康检查（readiness/liveness） |
| Resources | 资源请求与限制 |
| 扩缩容 | 手动 scale 和自动 HPA |
| 运维操作 | 日志、调试、更新、回滚、清理 |

> **下一步：** 可以继续学习 Helm 包管理器来简化 K8s 应用的部署和管理，或学习 GitOps 工具如 ArgoCD 实现持续交付。
