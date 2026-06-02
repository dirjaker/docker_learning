# Docker 常用命令速查表

## 1. 镜像管理

### 构建镜像
```bash
# 基本构建
docker build -t myapp:1.0 .

# 指定 Dockerfile 路径
docker build -t myapp:1.0 -f Dockerfile.prod .

# 无缓存构建
docker build --no-cache -t myapp:1.0 .

# 构建时传入参数
docker build --build-arg VERSION=1.0 -t myapp:1.0 .

# 多平台构建
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:1.0 .
```

### 拉取/推送
```bash
# 拉取镜像
docker pull nginx:1.25
docker pull nginx                  # latest
docker pull nginx@sha256:abc123... # 指定摘要

# 推送镜像
docker tag myapp:1.0 myuser/myapp:1.0
docker push myuser/myapp:1.0

# 登录仓库
docker login                        # Docker Hub
docker login registry.example.com   # 私有仓库
```

### 镜像查看/清理
```bash
# 列出本地镜像
docker images
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# 搜索镜像
docker search nginx

# 查看镜像详情
docker inspect nginx:1.25
docker history nginx:1.25

# 删除镜像
docker rmi myapp:1.0
docker rmi $(docker images -q -f "dangling=true")  # 删除悬空镜像

# 清理所有未使用镜像
docker image prune         # 删除悬空
docker image prune -a      # 删除所有未使用

# 保存/加载镜像（离线传输）
docker save -o myapp.tar myapp:1.0
docker load -i myapp.tar
```

---

## 2. 容器管理

### 生命周期
```bash
# 创建并启动
docker run -d --name web -p 8080:80 nginx
docker run -it --rm ubuntu bash          # 交互模式，退出自动删除
docker run -d --restart unless-stopped nginx  # 自动重启

# 常用 run 参数
#   -d        后台运行
#   -it       交互 + 伪终端
#   --rm      退出后自动删除
#   --name    容器名称
#   -p 8080:80   端口映射 (宿主机:容器)
#   -v /src:/app 挂载卷
#   -e KEY=VAL   环境变量
#   --network    指定网络
#   --memory 512m 内存限制
#   --cpus 1.5    CPU 限制

# 启动/停止/重启
docker start web
docker stop web
docker restart web
docker pause web
docker unpause web

# 删除容器
docker rm web
docker rm -f web                  # 强制删除运行中容器
docker container prune            # 删除所有已停止容器
```

### 查看容器
```bash
# 列出容器
docker ps                         # 运行中
docker ps -a                      # 所有
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看日志
docker logs web
docker logs -f web                # 实时跟踪
docker logs --tail 100 web        # 最后 100 行
docker logs --since 1h web        # 最近 1 小时

# 查看详情
docker inspect web
docker inspect -f '{{.State.Status}}' web

# 查看资源使用
docker stats
docker stats web --no-stream

# 查看端口映射
docker port web

# 查看进程
docker top web
```

### 容器交互
```bash
# 进入运行中容器
docker exec -it web bash
docker exec -it web sh            # Alpine 等无 bash 的镜像
docker exec web cat /etc/nginx/nginx.conf

# 复制文件
docker cp web:/app/logs/app.log ./app.log
docker cp ./config.yml web:/app/config.yml

# 查看容器变化
docker diff web
```

---

## 3. 网络管理

```bash
# 列出网络
docker network ls

# 创建网络
docker network create mynet
docker network create --driver bridge --subnet 172.20.0.0/16 mynet

# 连接/断开
docker network connect mynet web
docker network disconnect mynet web

# 查看网络详情
docker network inspect mynet

# 删除网络
docker network rm mynet
docker network prune              # 删除未使用网络

# 容器间通信（同一自定义网络可用容器名访问）
docker run -d --name redis --network mynet redis
docker run -d --name app --network mynet myapp
# app 容器中可通过 "redis:6379" 访问 redis
```

---

## 4. 存储管理（Volume）

```bash
# 创建 volume
docker volume create mydata

# 列出 volume
docker volume ls

# 查看详情
docker volume inspect mydata

# 使用 volume
docker run -d -v mydata:/app/data nginx
docker run -d --mount source=mydata,target=/app/data nginx

# 绑定挂载（bind mount）
docker run -d -v $(pwd)/html:/usr/share/nginx/html nginx
docker run -d --mount type=bind,source=$(pwd)/html,target=/usr/share/nginx/html nginx

# 只读挂载
docker run -d -v mydata:/app/data:ro nginx

# 删除 volume
docker volume rm mydata
docker volume prune               # 删除未使用 volume
```

---

## 5. 系统管理

```bash
# 查看 Docker 信息
docker info
docker version

# 系统清理（慎用！）
docker system df                  # 查看磁盘占用
docker system prune               # 删除停止的容器 + 未用网络 + 悬空镜像
docker system prune -a            # 删除所有未使用的资源
docker system prune --volumes     # 包括 volume

# 导出/导入容器（非镜像）
docker export web > web.tar
docker import web.tar myweb:1.0

# 查看事件
docker events
docker events --since 1h
```

---

## 6. 常用组合技巧

```bash
# 停止所有容器
docker stop $(docker ps -q)

# 删除所有容器
docker rm -f $(docker ps -aq)

# 删除所有镜像
docker rmi $(docker images -q)

# 查看容器 IP 地址
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web

# 查看容器占用端口
docker inspect -f '{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{println}}{{end}}' web

# 批量删除退出的容器
docker ps -a -f "status=exited" -q | xargs docker rm

# 从运行中容器创建新镜像
docker commit web myweb:modified
```
