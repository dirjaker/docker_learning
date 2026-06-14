# Docker 存储

## 1. 为什么需要 Docker 存储？

### 1.1 容器是临时的

Docker 容器的生命周期是短暂的——删除容器后，容器内部的所有数据都会消失。这是容器设计的基本特性。

```bash
# 演示：容器数据丢失
docker run --name test-storage -it ubuntu bash

# 在容器内创建一个文件
echo "Hello Docker" > /tmp/hello.txt
cat /tmp/hello.txt

# 退出并删除容器
exit
docker rm test-storage

# 重新启动同镜像的容器，数据已消失
docker run --name test-storage2 -it ubuntu bash
cat /tmp/hello.txt   # 报错：文件不存在
exit
docker rm test-storage2
```

**核心问题**：数据库的数据、应用的日志、用户上传的文件……这些都不能随容器一起消失。

### 1.2 容器层 vs 镜像层

Docker 使用**分层存储**架构：

```
┌──────────────────────────┐
│     容器层（可写层）       │  ← 容器运行时的修改都在这里（Copy-on-Write）
├──────────────────────────┤
│     镜像层 3（应用代码）   │  ← 只读
├──────────────────────────┤
│     镜像层 2（依赖安装）   │  ← 只读
├──────────────────────────┤
│     镜像层 1（基础镜像）   │  ← 只读
└──────────────────────────┘
```

- **镜像层**：只读，所有基于同一镜像的容器共享
- **容器层**：可写，容器删除后该层数据丢失

这就是为什么你需要外部存储来持久化数据。

---

## 2. 三种存储方式

Docker 提供三种主要的数据挂载方式：

| 方式 | 数据存储位置 | 推荐场景 |
|------|------------|---------|
| **Volumes** | Docker 管理的目录（`/var/lib/docker/volumes/`） | 持久化数据（推荐） |
| **Bind Mounts** | 宿主机任意目录 | 开发环境、配置文件 |
| **tmpfs Mounts** | 内存中 | 临时敏感数据 |

---

### 2.1 Volumes（推荐）

#### 什么是 Volume？

Volume 是 Docker 管理的存储卷，数据保存在宿主机的 `/var/lib/docker/volumes/` 目录下，独立于容器的生命周期。

```
宿主机                              容器
/var/lib/docker/volumes/            /data
  └── mydata/                       └── (挂载点)
       └── _data/
            └── your-files...  ←→   └── your-files...
```

#### Volume 管理命令

```bash
# 创建 Volume
docker volume create mydata

# 查看所有 Volume
docker volume ls

# 查看 Volume 详情
docker volume inspect mydata

# 删除指定 Volume
docker volume rm mydata

# 删除所有未使用的 Volume（慎用！）
docker volume prune
```

**`docker volume inspect` 输出示例：**

```json
[
    {
        "CreatedAt": "2024-01-01T00:00:00+08:00",
        "Driver": "local",
        "Labels": {},
        "Mountpoint": "/var/lib/docker/volumes/mydata/_data",
        "Name": "mydata",
        "Options": {},
        "Scope": "local"
    }
]
```

#### 命名卷 vs 匿名卷

```bash
# 命名卷：有明确名字，方便管理
docker run -d --name app1 -v mydata:/data nginx

# 匿名卷：没有名字，Docker 自动生成随机 ID
docker run -d --name app2 -v /data nginx

# 查看区别
docker volume ls
# DRIVER    VOLUME NAME
# local     mydata                    ← 命名卷，名字清晰
# local     a1b2c3d4e5f6...          ← 匿名卷，难以辨认
```

**踩坑经验**：匿名卷在容器删除后很难清理，建议始终使用命名卷。

#### Volume 的实际使用

```bash
# 1. 创建 Volume 并使用
docker volume create web-content

# 2. 启动 Nginx 并挂载
docker run -d \
  --name nginx-with-vol \
  -p 8080:80 \
  -v web-content:/usr/share/nginx/html \
  nginx

# 3. 向 Volume 中写入内容
docker exec nginx-with-vol bash -c 'echo "<h1>Hello from Volume!</h1>" > /usr/share/nginx/html/index.html'

# 4. 访问测试
curl http://localhost:8080

# 5. 删除容器，Volume 数据依然存在
docker rm -f nginx-with-vol

# 6. 用新容器挂载同一 Volume，数据还在
docker run -d \
  --name nginx-new \
  -p 8081:80 \
  -v web-content:/usr/share/nginx/html \
  nginx

curl http://localhost:8081   # 仍然输出 "Hello from Volume!"

# 清理
docker rm -f nginx-new
docker volume rm web-content
```

---

### 2.2 Bind Mounts

#### 什么是 Bind Mount？

Bind Mount 将宿主机上的**任意目录**直接挂载到容器中。容器和宿主机看到的是同一份文件。

```
宿主机                              容器
/home/user/project/                 /app
  ├── app.py        ←─────────→      ├── app.py
  └── config.yml                    └── config.yml
```

#### 基本用法

```bash
# 语法：-v /宿主机路径:/容器路径
# 或使用 --mount（更明确的写法）

# 方式一：-v 简写
docker run -d \
  --name bind-demo \
  -v /home/dirjaker/mydata:/data \
  nginx

# 方式二：--mount（推荐用于生产环境，语法更清晰）
docker run -d \
  --name bind-demo2 \
  --mount type=bind,source=/home/dirjaker/mydata,target=/data \
  nginx
```

#### 在宿主机和容器间共享文件

```bash
# 1. 在宿主机创建测试目录
mkdir -p /tmp/bind-test
echo "From Host" > /tmp/bind-test/host.txt

# 2. 启动容器挂载该目录
docker run --rm -it -v /tmp/bind-test:/shared ubuntu bash

# 3. 在容器中查看（能看到宿主机的文件）
cat /shared/host.txt      # 输出：From Host

# 4. 在容器中创建文件
echo "From Container" > /shared/container.txt
exit

# 5. 回到宿主机查看（能看到容器创建的文件）
cat /tmp/bind-test/container.txt   # 输出：From Container
```

#### Bind Mount vs Volume 对比

| 特性 | Volume | Bind Mount |
|------|--------|------------|
| 管理方 | Docker 管理 | 用户自己管理 |
| 存储位置 | `/var/lib/docker/volumes/` | 宿主机任意路径 |
| 可移植性 | 高（Docker 统一管理） | 低（依赖路径） |
| 预填充 | 可从容器中预填充 | 宿主机必须先存在 |
| 适用场景 | 数据库数据、应用数据 | 开发环境、配置文件 |

#### 权限问题（常见坑！）

```bash
# 问题：容器以 root 运行，在宿主机创建的文件属主是 root
mkdir -p /tmp/perm-test
docker run --rm -v /tmp/perm-test:/data ubuntu bash -c 'touch /data/file1'
ls -la /tmp/perm-test/
# -rw-r--r-- 1 root root 0 ... file1   ← root 所有！宿主机用户可能无法编辑

# 解决方案一：指定容器内用户（-u）
docker run --rm -u $(id -u):$(id -g) -v /tmp/perm-test:/data ubuntu bash -c 'touch /data/file2'
ls -la /tmp/perm-test/
# -rw-r--r-- 1 dirjaker dirjaker 0 ... file2   ← 宿主机用户

# 解决方案二：容器内应用支持自动 chown（很多官方镜像支持 PUID/PGID 环境变量）

# 问题二：SELinux 系统上的权限拒绝
# 在 RHEL/CentOS 上可能需要加 :z 或 :Z 标签
docker run --rm -v /tmp/perm-test:/data:z ubuntu bash -c 'touch /data/file3'
# :z  → 私有标签，仅当前容器可访问
# :Z  → 私有标签，更严格
```

---

### 2.3 tmpfs Mounts

#### 什么是 tmpfs？

tmpfs 将数据存储在**宿主机的内存**中，不会写入磁盘。容器停止后数据即消失。

```
宿主机内存
  └── tmpfs 空间  ←──→  容器 /secrets
     (不落盘)
```

#### 基本用法

```bash
# 只有 --tmpfs 和 --mount 两种方式，不支持 -v
docker run -d \
  --name tmpfs-demo \
  --tmpfs /app/tmp \
  nginx

# 使用 --mount 更明确
docker run -d \
  --name tmpfs-demo2 \
  --mount type=tmpfs,target=/app/tmp,tmpfs-size=100m,tmpfs-mode=1770 \
  nginx

# 验证：进入容器写入数据
docker exec tmpfs-demo bash -c 'echo "temporary" > /app/tmp/data.txt && cat /app/tmp/data.txt'
```

#### 适用场景

- **敏感数据**：密钥、Token 等不想落盘的数据
- **临时缓存**：高频读写的临时文件
- **性能要求高**：内存读写远快于磁盘

```bash
# 实际示例：将敏感的 API key 放在内存中
docker run -d \
  --name secret-app \
  --mount type=tmpfs,target=/run/secrets \
  myapp

# 在容器启动脚本中写入密钥到 /run/secrets/api_key
# 容器停止后，密钥自动从内存中消失
```

> **注意**：tmpfs 仅在 Linux 上有效，Docker Desktop (Mac/Windows) 中受限。

---

## 3. Volume 高级用法

### 3.1 只读挂载 `:ro`

```bash
# 方式一：-v 加 :ro
docker run -d \
  --name readonly-demo \
  -v myconfig:/etc/app/config:ro \
  nginx

# 方式二：--mount 加 readonly
docker run -d \
  --name readonly-demo2 \
  --mount type=volume,source=myconfig,target=/etc/app/config,readonly \
  nginx

# 测试：容器内无法写入
docker exec readonly-demo bash -c 'echo "test" > /etc/app/config/new.txt'
# 报错：Read-only file system

# 常见场景：配置文件只读挂载，防止应用误改
docker run -d \
  --name nginx-readonly \
  -v /home/dirjaker/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /home/dirjaker/html:/usr/share/nginx/html:ro \
  nginx
```

### 3.2 Volume 驱动

Docker 默认使用 `local` 驱动，也支持第三方存储驱动。

```bash
# 查看可用的 Volume 驱动
docker info | grep -i "volume drivers"

# 使用特定驱动创建 Volume（以 local 驱动为例）
docker volume create --driver local myvol

# 指定驱动选项
# local 驱动支持 tmpfs、NFS、设备映射等
docker volume create --driver local \
  --opt type=tmpfs \
  --opt device=tmpfs \
  --opt o=size=100m,uid=1000 \
  mytmpvol

# 安装第三方 Volume 揱件（如 Rex-Ray 支持 AWS EBS、Ceph 等）
# docker plugin install rexray/ebs
# docker volume create --driver rexray/ebs --opt size=10 cloud-vol
```

### 3.3 NFS Volume

将 NFS 共享挂载为 Docker Volume，实现多主机数据共享。

```bash
# 创建 NFS Volume（需要宿主机已安装 nfs-utils / nfs-common）
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.100,rw,nfsvers=4 \
  --opt device=:/exported/path \
  nfs-vol

# 使用 NFS Volume
docker run -d \
  --name nfs-app \
  -v nfs-vol:/data \
  nginx

# 查看 NFS Volume 详情
docker volume inspect nfs-vol
```

### 3.4 数据备份和恢复

#### 备份 Volume 数据

```bash
# 创建要备份的 Volume
docker volume create important-data
docker run --rm -v important-data:/data ubuntu bash -c \
  'echo "important data" > /data/config.txt'

# 备份方法：启动临时容器，将 Volume 数据打包到宿主机
docker run --rm \
  -v important-data:/source:ro \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/important-data-backup.tar.gz -C /source .

# 验证备份文件
ls -lh important-data-backup.tar.gz
tar tzf important-data-backup.tar.gz
```

#### 恢复 Volume 数据

```bash
# 创建新的 Volume
docker volume create restored-data

# 从备份恢复
docker run --rm \
  -v restored-data:/dest \
  -v $(pwd):/backup:ro \
  ubuntu bash -c 'tar xzf /backup/important-data-backup.tar.gz -C /dest'

# 验证恢复的数据
docker run --rm -v restored-data:/data ubuntu cat /data/config.txt
# 输出：important data
```

#### 两个 Volume 之间迁移数据

```bash
# 直接用临时容器在两个 Volume 间复制
docker run --rm \
  -v important-data:/source:ro \
  -v restored-data:/dest \
  ubuntu bash -c 'cp -a /source/. /dest/'
```

---

## 4. 实战案例

### 4.1 MySQL 数据持久化

```bash
# ❌ 错误做法：不挂载 Volume，数据会丢失
docker run -d --name mysql-bad -e MYSQL_ROOT_PASSWORD=123456 mysql:8

# 删除容器后数据全没了
docker rm -f mysql-bad

# ✅ 正确做法：使用命名卷持久化
docker volume create mysql-data
docker volume create mysql-config

docker run -d \
  --name mysql-prod \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=MyStr0ngP@ss \
  -e MYSQL_DATABASE=myapp \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=app123 \
  -v mysql-data:/var/lib/mysql \
  -v mysql-config:/etc/mysql/conf.d \
  --restart unless-stopped \
  mysql:8

# 写入测试数据
docker exec -it mysql-prod mysql -u root -pMyStr0ngP@ss -e \
  "USE myapp; CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50)); INSERT INTO users (name) VALUES ('Alice'), ('Bob');"

# 删除容器
docker rm -f mysql-prod

# 重新创建，数据还在！
docker run -d \
  --name mysql-prod-new \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=MyStr0ngP@ss \
  -v mysql-data:/var/lib/mysql \
  -v mysql-config:/etc/mysql/conf.d \
  --restart unless-stopped \
  mysql:8

# 验证数据完整
docker exec -it mysql-prod-new mysql -u root -pMyStr0ngP@ss -e \
  "USE myapp; SELECT * FROM users;"
# +----+-------+
# | id | name  |
# +----+-------+
# |  1 | Alice |
# |  2 | Bob   |
# +----+-------+
```

**MySQL 挂载自定义配置文件（Bind Mount）：**

```bash
# 在宿主机创建自定义配置
mkdir -p /tmp/mysql-conf
cat > /tmp/mysql-conf/custom.cnf << 'EOF'
[mysqld]
max_connections = 500
innodb_buffer_pool_size = 1G
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[client]
default-character-set = utf8mb4
EOF

# 挂载自定义配置启动
docker run -d \
  --name mysql-custom \
  -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -v mysql-data2:/var/lib/mysql \
  -v /tmp/mysql-conf/custom.cnf:/etc/mysql/conf.d/custom.cnf:ro \
  mysql:8
```

### 4.2 Redis 数据持久化

```bash
# 创建 Redis 数据 Volume
docker volume create redis-data

# 方式一：使用 RDB 持久化（默认）
docker run -d \
  --name redis-rdb \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7 redis-server --appendonly no --save 60 1000

# --save 60 1000 表示：60 秒内至少 1000 次写入就触发 RDB 快照

# 方式二：使用 AOF 持久化（更安全，推荐生产使用）
docker volume create redis-aof-data

docker run -d \
  --name redis-aof \
  -p 6380:6379 \
  -v redis-aof-data:/data \
  redis:7 redis-server --appendonly yes --appendfsync everysec

# --appendfsync everysec：每秒同步一次 AOF 文件（兼顾性能和安全）

# 测试：写入数据后删除容器
docker exec redis-aof redis-cli SET mykey "持久化测试"
docker exec redis-aof redis-cli GET mykey

docker rm -f redis-aof

# 重新启动，数据还在
docker run -d \
  --name redis-aof-new \
  -p 6380:6379 \
  -v redis-aof-data:/data \
  redis:7 redis-server --appendonly yes

docker exec redis-aof-new redis-cli GET mykey
# "持久化测试"
```

**Redis 使用自定义配置文件：**

```bash
mkdir -p /tmp/redis-conf
cat > /tmp/redis-conf/redis.conf << 'EOF'
bind 0.0.0.0
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
requirepass MyRedisPass123
EOF

docker run -d \
  --name redis-custom \
  -p 6381:6379 \
  -v redis-custom-data:/data \
  -v /tmp/redis-conf/redis.conf:/usr/local/etc/redis/redis.conf:ro \
  redis:7 redis-server /usr/local/etc/redis/redis.conf
```

### 4.3 日志文件挂载

```bash
# 创建日志目录
mkdir -p /tmp/app-logs

# 方式一：Bind Mount 挂载日志目录（推荐，方便宿主机查看和轮转）
docker run -d \
  --name app-with-logs \
  -v /tmp/app-logs:/var/log/app \
  nginx

# 容器内应用将日志写到 /var/log/app/ 目录
docker exec app-with-logs bash -c \
  'echo "[$(date)] App started" >> /var/log/app/app.log && \
   echo "[$(date)] Request processed" >> /var/log/app/app.log'

# 宿主机直接查看日志
cat /tmp/app-logs/app.log

# 方式二：使用 Docker 日志驱动 + Volume
# 适合需要集中收集日志的场景

# 查看容器日志（Docker 默认日志）
docker logs app-with-logs

# 设置日志轮转（防止日志文件无限增长）
docker run -d \
  --name app-log-rotate \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -v /tmp/app-logs:/var/log/app \
  nginx
# max-size=10m：单个日志文件最大 10MB
# max-file=3：最多保留 3 个日志文件（总共最大 30MB）
```

**Nginx 日志分离实战：**

```bash
mkdir -p /tmp/nginx-logs

docker run -d \
  --name nginx-logs \
  -p 8080:80 \
  -v /tmp/nginx-logs:/var/log/nginx \
  nginx

# 生成一些访问日志
for i in $(seq 1 10); do curl -s http://localhost:8080 > /dev/null; done

# 在宿主机查看日志
tail -5 /tmp/nginx-logs/access.log
cat /tmp/nginx-logs/error.log
```

### 4.4 配置文件挂载

```bash
# Nginx 配置文件挂载
mkdir -p /tmp/nginx-conf /tmp/nginx-html

# 创建自定义 nginx.conf
cat > /tmp/nginx-conf/nginx.conf << 'EOF'
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
        
        location /api {
            return 200 '{"status": "ok"}';
            add_header Content-Type application/json;
        }
    }
}
EOF

# 创建自定义首页
cat > /tmp/nginx-html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Docker Nginx</title></head>
<body>
    <h1>Custom Nginx with Volume Mounts!</h1>
    <p>Config and HTML are mounted from host.</p>
</body>
</html>
EOF

# 启动 Nginx（配置只读，HTML 只读）
docker run -d \
  --name nginx-custom \
  -p 8080:80 \
  -v /tmp/nginx-conf/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /tmp/nginx-html:/usr/share/nginx/html:ro \
  nginx

# 测试
curl http://localhost:8080        # 自定义首页
curl http://localhost:8080/api    # {"status": "ok"}

# 修改 HTML 无需重建容器！
echo '<h1>Updated!</h1>' >> /tmp/nginx-html/index.html
curl http://localhost:8080   # 立即生效
```

**多环境配置切换：**

```bash
# 创建不同环境的配置目录
mkdir -p /tmp/configs/{dev,staging,prod}

echo 'server { listen 80; }' > /tmp/configs/dev/app.conf
echo 'server { listen 80; server_name staging.example.com; }' > /tmp/configs/staging/app.conf
echo 'server { listen 443 ssl; server_name prod.example.com; }' > /tmp/configs/prod/app.conf

# 根据环境切换
ENV=dev
docker run -d \
  --name app-${ENV} \
  -v /tmp/configs/${ENV}:/etc/app/config:ro \
  myapp
```

---

## 5. 常见问题和踩坑经验

### 5.1 权限被拒绝（Permission Denied）

```bash
# 症状：容器无法写入挂载的目录
docker run --rm -v /tmp/test:/data ubuntu touch /data/test.txt
# touch: cannot touch '/data/test.txt': Permission denied

# 原因：宿主机目录权限不足，或 SELinux 限制

# 解决方案 1：修改宿主机目录权限
chmod 777 /tmp/test    # 开发环境可以，生产环境不推荐

# 解决方案 2：指定容器用户为宿主机用户
docker run --rm -u $(id -u):$(id -g) -v /tmp/test:/data ubuntu touch /data/test.txt

# 解决方案 3：SELinux 添加标签
docker run --rm -v /tmp/test:/data:z ubuntu touch /data/test.txt
```

### 5.2 Volume 无法删除（被占用）

```bash
# 症状
docker volume rm mydata
# Error response from daemon: unable to remove volume: volume is in use

# 查看哪个容器在使用
docker ps -a --filter volume=mydata

# 或查看 Volume 详情
docker volume inspect mydata --format '{{.Mountpoint}}'
# 然后查找占用进程
grep -r "mydata" /proc/*/mounts 2>/dev/null

# 解决：先停止并删除相关容器
docker rm -f $(docker ps -aq --filter volume=mydata)
docker volume rm mydata
```

### 5.3 Bind Mount 宿主机目录不存在

```bash
# 症状：Docker 会自动创建目录（不是文件！）
docker run --rm -v /tmp/newdir:/data ubuntu ls /data
# 如果宿主机上 /tmp/newdir 不存在，Docker 会创建一个目录

# 常见坑：挂载文件时路径不存在
docker run --rm -v /tmp/config.yml:/etc/app/config.yml nginx
# 如果 /tmp/config.yml 不存在，Docker 会创建一个同名的**目录**！

# 解决：确保文件先存在
touch /tmp/config.yml
docker run --rm -v /tmp/config.yml:/etc/app/config.yml nginx
```

### 5.4 数据库容器停止后数据损坏

```bash
# 症状：MySQL/PostgreSQL 强制停止后无法启动

# 原因：数据库需要正常关闭流程来刷写数据

# 解决：始终使用 docker stop（优雅关闭），不要用 docker kill
docker stop mysql-prod     # 发送 SIGTERM，等待 10 秒后再 SIGKILL
docker stop -t 30 mysql-prod  # 等待 30 秒再强制停止

# 设置容器重启策略，避免手动干预
docker run -d \
  --name mysql-prod \
  --restart unless-stopped \
  -v mysql-data:/var/lib/mysql \
  mysql:8
```

### 5.5 开发环境 vs 生产环境的存储选择

```bash
# 开发环境：Bind Mount（方便实时修改代码）
docker run -d \
  --name dev-app \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/config.yml:/app/config.yml \
  -p 3000:3000 \
  myapp:dev

# 生产环境：Volume（更安全、性能更好）
docker volume create app-data
docker run -d \
  --name prod-app \
  -v app-data:/app/data \
  -p 3000:3000 \
  myapp:prod
```

---

## 6. 总结

| 场景 | 推荐方式 | 示例 |
|------|---------|------|
| 数据库数据 | Volume（命名卷） | `-v mysql-data:/var/lib/mysql` |
| 应用日志 | Bind Mount | `-v /var/log/app:/app/logs` |
| 配置文件 | Bind Mount（只读） | `-v ./config.yml:/app/config.yml:ro` |
| 开发代码 | Bind Mount | `-v $(pwd)/src:/app/src` |
| 敏感临时数据 | tmpfs | `--mount type=tmpfs,target=/secrets` |
| 多主机共享 | NFS Volume | `--opt type=nfs` |

**一句话原则**：
- 需要持久化保存的数据 → **Volume**
- 需要和宿主机双向同步的文件 → **Bind Mount**
- 不想落盘的敏感/临时数据 → **tmpfs**
