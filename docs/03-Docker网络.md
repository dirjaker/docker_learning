# 03 - Docker 网络

> 容器不会"自动连通"，理解 Docker 网络是搞懂容器通信的关键。

---

## 目录

- [为什么需要 Docker 网络？](#为什么需要-docker-网络)
- [网络驱动类型](#网络驱动类型)
  - [bridge（默认）](#bridge默认)
  - [host](#host)
  - [none](#none)
  - [overlay](#overlay)
  - [macvlan](#macvlan)
- [自定义网络](#自定义网络)
- [DNS 和服务发现](#dns-和服务发现)
- [端口映射详解](#端口映射详解)
- [实战](#实战)
- [常见问题与踩坑](#常见问题与踩坑)

---

## 为什么需要 Docker 网络？

### 类比理解

把 Docker 想象成一个**小区**：

- **宿主机** = 小区的大门（对外通信）
- **容器** = 小区里的住户（每户有自己的房间号 IP）
- **Docker 网络** = 小区内部的道路系统

没有网络，容器就像被关在没有门的房间里——**能存在，但无法和外界交流**。

### 三类通信需求

```
┌──────────────┐
│  外部网络     │  ← 容器要访问互联网（拉镜像、调用外部 API）
└──────┬───────┘
       │
┌──────┴───────┐
│   宿主机      │  ← 容器要访问宿主机上的服务（数据库、配置文件）
└──────┬───────┘
       │
┌──────┴───────┐
│   容器之间    │  ← Web 容器要连数据库容器、微服务之间互调
└──────────────┘
```

**如果不去理解网络，你会踩无数坑**：容器互相 ping 不通、端口映射不生效、DNS 解析失败……

---

## 网络驱动类型

Docker 提供 5 种网络驱动，先看全貌：

| 驱动 | 隔离性 | 性能 | 适用场景 |
|------|--------|------|----------|
| `bridge` | 中 | 中 | **单机**多容器通信（最常用） |
| `host` | 无 | 高 | 对性能要求极高的场景 |
| `none` | 完全 | 无 | 安全敏感、不需要网络的容器 |
| `overlay` | 高 | 中 | **跨主机**容器通信（Swarm/K8s） |
| `macvlan` | 高 | 高 | 容器需要独立 MAC 地址接入物理网络 |

查看当前所有网络：

```bash
docker network ls
```

```
NETWORK ID     NAME      DRIVER    SCOPE
a1b2c3d4e5f6   bridge    bridge    local
f6e5d4c3b2a1   host      host      local
1a2b3c4d5e6f   none      null      local
```

---

### bridge（默认）

#### 什么是 bridge 网络？

**类比**：bridge 就像一个**虚拟交换机**。每个容器都用网线（虚拟网卡）插到这个交换机上，交换机再通过 NAT 连到外面。

```
┌─────────────────────────────────────────┐
│  宿主机                                  │
│                                          │
│  ┌───────┐  ┌───────┐  ┌───────┐        │
│  │容器 A  │  │容器 B  │  │容器 C  │        │
│  │172.17  │  │172.17  │  │172.17  │        │
│  │.0.2   │  │.0.3   │  │.0.4   │        │
│  └───┬───┘  └───┬───┘  └───┬───┘        │
│      │          │          │             │
│  ┌───┴──────────┴──────────┴───┐        │
│  │    docker0 (虚拟网桥/交换机)   │        │
│  └──────────────┬──────────────┘        │
│                 │ NAT                    │
│            ┌────┴────┐                   │
│            │ eth0    │ ← 宿主机物理网卡   │
│            └─────────┘                   │
└─────────────────────────────────────────┘
```

#### 容器如何获得 IP？

Docker 在安装时会创建一个 `docker0` 虚拟网桥，默认网段是 `172.17.0.0/16`。每启动一个容器，Docker 自动从这个网段分配一个 IP。

```bash
# 查看 docker0 网桥信息
ip addr show docker0
```

```
4: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
```

```bash
# 启动一个容器，查看它的 IP
docker run --rm alpine ip addr show eth0
```

```
25: eth0@if26: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
```

> **注意**：容器的 IP 是动态分配的，**不要依赖 IP 地址做通信**，后面会讲 DNS 方案。

#### 容器之间如何互相访问？

在同一 bridge 网络下，容器可以用 **IP 地址**直接通信：

```bash
# 终端 1：启动容器 A，运行一个 HTTP 服务
docker run -d --name container_a nginx

# 终端 2：启动容器 B，用 curl 访问容器 A
docker run --rm curlimages/curl curl -s http://172.17.0.2:80 | head -5
```

```html
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
</head>
```

**能通！** 但用 IP 地址不靠谱（IP 会变），更好的方式是用容器名（后面 DNS 章节讲）。

#### 端口映射 -p 的原理

容器有自己的 IP（如 `172.17.0.2`），但外部用户访问不到这个内网 IP。**端口映射 = 在宿主机上开一个"传话窗口"**。

```bash
# -p 宿主机端口:容器端口
docker run -d --name web -p 8080:80 nginx
```

```
# 访问逻辑：
# 用户 → 宿主机:8080 → NAT转发 → 容器:80 (nginx)
```

```bash
# 查看端口映射
docker port web
```

```
80/tcp -> 0.0.0.0:8080
```

```bash
# 验证
curl http://localhost:8080
```

> **原理**：Docker 通过 `iptables` 的 DNAT 规则，把发到宿主机 8080 端口的流量转发到容器的 80 端口。

---

### host

#### 什么是 host 网络？

**类比**：容器不再有自己的"房间"，而是**直接住在客厅**——和宿主机共享网络栈。

```bash
docker run --rm --network host alpine ip addr show
```

> 输出的是**宿主机**的全部网卡信息，容器没有自己的 IP。

#### 和 bridge 的区别

| 对比项 | bridge | host |
|--------|--------|------|
| 网络隔离 | ✅ 容器有独立 IP | ❌ 共享宿主机 IP |
| 端口映射 | 需要 `-p` | **不需要**，直接监听宿主机端口 |
| 性能 | 有 NAT 开销 | 接近原生性能 |
| 冲突风险 | 低 | 高（端口可能冲突） |

```bash
# host 模式下，nginx 直接监听宿主机 80 端口
docker run -d --network host nginx

# 不需要 -p，直接访问
curl http://localhost:80
```

#### 适用场景

- 对网络性能要求极高（如高频交易、实时游戏服务器）
- 需要监听大量端口（省去逐个 `-p` 映射的麻烦）
- **注意**：同一宿主机上，同一端口只能被一个 host 模式容器使用

---

### none

#### 什么是 none 网络？

**类比**：容器被关进一个**完全没有门窗的房间**——有网卡，但不连任何网络。

```bash
docker run --rm --network none alpine ip addr show
```

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
```

只有 `lo`（回环网卡），没有任何外部网络连接。

#### 适用场景

- 安全敏感的计算任务（只需 CPU，不需网络）
- 密码生成、离线数据处理
- 作为基础，手动配置网络（高级用法）

---

### overlay

#### 什么是 overlay 网络？

**类比**：bridge 是小区内部道路，overlay 是**连接多个小区的高架桥**。它让不同宿主机上的容器能够直接通信。

```
┌──────────────────┐         ┌──────────────────┐
│  宿主机 A         │         │  宿主机 B         │
│  ┌──────┐        │         │        ┌──────┐  │
│  │容器1  │        │  VXLAN  │        │容器3  │  │
│  └──┬───┘        │  隧道   │        └──┬───┘  │
│  ┌──┴───┐        │◄════════►│        ┌──┴───┐  │
│  │overlay│       │         │       │overlay│  │
│  │网络    │       │         │       │网络    │  │
│  └──────┘        │         │        └──────┘  │
└──────────────────┘         └──────────────────┘
```

#### 适用场景

- **Docker Swarm** 集群中跨主机的容器通信
- **Kubernetes** 中的 Pod 网络（虽然 K8s 通常用 CNI 插件）
- 微服务部署在多台机器上，需要互相访问

```bash
# 创建 overlay 网络（需要 Swarm 模式）
docker swarm init
docker network create -d overlay my_overlay
```

> ⚠️ overlay 网络需要 Docker Swarm 或外部 KV 存储（如 Consul）支持，单机开发中很少用到。

---

### macvlan

#### 什么是 macvlan 网络？

**类比**：每个容器获得一个**真正的 MAC 地址**，就像直接插在物理交换机上。对于外部网络来说，容器看起来就是一台独立的物理机器。

```bash
# 创建 macvlan 网络（需要指定物理网卡和子网）
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  my_macvlan
```

```bash
# 启动容器，它会获得 192.168.1.x 的 IP
docker run --rm --network my_macvlan --ip 192.168.1.100 alpine \
  ping -c 2 192.168.1.1
```

```
PING 192.168.1.1 (192.168.1.1): 56 data bytes
64 bytes from 192.168.1.1: seq=0 ttl=64 time=0.123 ms
64 bytes from 192.168.1.1: seq=1 ttl=64 time=0.098 ms
```

#### 适用场景

- 遗留系统迁移（应用期望有独立 IP）
- 需要从局域网直接访问容器（不经过 NAT）
- 网络设备模拟

> ⚠️ **限制**：宿主机和 macvlan 容器之间默认**无法直接通信**（需要额外配置）。

---

## 自定义网络

### 为什么不用默认 bridge？

默认 bridge 有**两个致命问题**：

1. **不能用容器名通信**（只能用 IP，IP 会变）
2. **所有容器都在同一个网络**（无法隔离）

自定义网络解决了这两个问题。

### 创建自定义网络

```bash
# 创建自定义 bridge 网络
docker network create my_network
```

```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

```bash
# 查看所有网络，多了 my_network
docker network ls
```

```
NETWORK ID     NAME         DRIVER    SCOPE
a1b2c3d4e5f6   bridge       bridge    local
f6e5d4c3b2a1   host         host      local
1a2b3c4d5e6f   none         null      local
d4e5f6a7b8c9   my_network   bridge    local
```

### 查看网络详情

```bash
docker network inspect my_network
```

```json
[
    {
        "Name": "my_network",
        "Driver": "bridge",
        "IPAM": {
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Containers": {}
    }
]
```

### 把容器接入自定义网络

```bash
# 方式 1：启动时指定网络
docker run -d --name app --network my_network nginx

# 方式 2：把已运行的容器接入网络
docker network connect my_network existing_container

# 断开网络
docker network disconnect my_network existing_container
```

### 自定义网络 vs 默认 bridge

| 特性 | 默认 bridge | 自定义 bridge |
|------|------------|--------------|
| DNS 解析容器名 | ❌ 不支持 | ✅ 支持 |
| 自动连接 | ✅ 默认连入 | 需手动指定 |
| 网络隔离 | ❌ 所有容器共享 | ✅ 按需隔离 |
| 自定义子网 | ❌ 固定 172.17.0.0/16 | ✅ 可自定义 |
| 自定义网关 | ❌ | ✅ |

**结论：生产环境始终使用自定义网络。**

---

## DNS 和服务发现

### 容器名作为主机名

在**自定义网络**中，Docker 内置 DNS 服务器会把容器名解析为 IP：

```bash
# 创建网络
docker network create app_net

# 启动两个容器
docker run -d --name database --network app_net postgres:15-alpine
docker run -d --name backend --network app_net nginx

# 在 backend 容器中，用容器名访问 database
docker exec backend ping -c 2 database
```

```
PING database (172.19.0.2): 56 data bytes
64 bytes from 172.19.0.2: seq=0 ttl=64 time=0.089 ms
64 bytes from 172.19.0.2: seq=1 ttl=64 time=0.076 ms
```

> **关键**：这在默认 bridge 网络中**不生效**！只有自定义网络才有 DNS 服务发现。

### 自定义 DNS

```bash
docker run --rm --dns 8.8.8.8 --dns 114.114.114.114 alpine \
  nslookup baidu.com
```

```
Server:    8.8.8.8
Address 1: 8.8.8.8

Name:      baidu.com
Address 1: 39.156.66.10
```

也可以在 `/etc/docker/daemon.json` 中全局配置：

```json
{
    "dns": ["8.8.8.8", "114.114.114.114"]
}
```

### --link（已废弃）

```bash
# ❌ 已废弃，不要使用
docker run --link database:db ...
```

`--link` 是早期方案，只在默认 bridge 网络下提供简单的名称解析。**已被自定义网络 + 内置 DNS 完全替代**。

---

## 端口映射详解

### 基本格式

```bash
# TCP（默认）
-p 宿主机端口:容器端口

# 指定协议
-p 宿主机端口:容器端口/udp
-p 宿主机端口:容器端口/tcp

# 映射到指定 IP
-p 127.0.0.1:8080:80       # 只允许本机访问
-p 192.168.1.100:8080:80   # 只允许指定网卡访问

# 随机分配宿主机端口
-p 80                       # Docker 随机选一个端口映射到容器 80
```

### 示例

```bash
# 同时映射 TCP 和 UDP
docker run -d -p 5353:53/tcp -p 5353:53/udp my_dns_server

# 映射多个端口
docker run -d -p 8080:80 -p 8443:443 nginx
```

### 端口冲突排查

```bash
# 启动时报错
docker run -d -p 8080:80 nginx
docker run -d -p 8080:80 nginx   # 再来一个！
```

```
docker: Error response from daemon: driver failed programming external
connectivity on endpoint ... Bind for 0.0.0.0:8080 failed: port is already allocated.
```

排查步骤：

```bash
# 1. 看看谁占了 8080
sudo ss -tlnp | grep 8080
```

```
LISTEN  0  4096  *:8080  *:*  users:(("docker-proxy",pid=12345,fd=4))
```

```bash
# 2. 查看哪些容器映射了该端口
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep 8080
```

```
laughing_tesla    0.0.0.0:8080->80/tcp
```

```bash
# 3. 停掉占用端口的容器，或换一个端口
docker stop laughing_tesla
```

---

## 实战

### 实战 1：创建自定义网络 + 多容器通信

**场景**：一个 Web 应用 + Redis 缓存 + PostgreSQL 数据库

```bash
# 第 1 步：创建自定义网络
docker network create app_network
```

```
f1a2b3c4d5e6...
```

```bash
# 第 2 步：启动 PostgreSQL
docker run -d \
  --name postgres \
  --network app_network \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=myapp \
  postgres:15-alpine
```

```bash
# 第 3 步：启动 Redis
docker run -d \
  --name redis \
  --network app_network \
  redis:7-alpine
```

```bash
# 第 4 步：启动应用（用容器名连接数据库和 Redis）
docker run -d \
  --name app \
  --network app_network \
  -p 8080:80 \
  -e DATABASE_URL="postgresql://postgres:mypassword@postgres:5432/myapp" \
  -e REDIS_URL="redis://redis:6379" \
  my_app:latest
```

> **注意连接字符串中的 `postgres` 和 `redis`**——这是容器名，自定义网络的 DNS 会自动解析为容器 IP。

```bash
# 第 5 步：验证连通性
docker exec app ping -c 2 postgres
docker exec app ping -c 2 redis
```

```
PING postgres (172.20.0.2): 56 data bytes
64 bytes from 172.20.0.2: seq=0 ttl=64 time=0.091 ms

PING redis (172.20.0.3): 56 data bytes
64 bytes from 172.20.0.3: seq=0 ttl=64 time=0.078 ms
```

```bash
# 第 6 步：查看网络中的所有容器
docker network inspect app_network --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
```

```
postgres 172.20.0.2/16
redis 172.20.0.3/16
app 172.20.0.4/16
```

### 实战 2：网络隔离

**场景**：前端只能访问后端，不能直接访问数据库

```bash
# 创建两个网络
docker network create frontend_net
docker network create backend_net

# 数据库：只在 backend_net
docker run -d --name db --network backend_net \
  -e POSTGRES_PASSWORD=secret \
  postgres:15-alpine

# 后端：同时在两个网络
docker run -d --name api --network backend_net nginx
docker network connect frontend_net api

# 前端：只在 frontend_net
docker run -d --name web --network frontend_net -p 8080:80 nginx
```

验证隔离效果：

```bash
# ✅ 前端能访问后端（同一网络）
docker exec web ping -c 1 api
```

```
PING api (172.21.0.2): 56 data bytes
64 bytes from 172.21.0.2: seq=0 ttl=64 time=0.082 ms
```

```bash
# ❌ 前端不能访问数据库（不同网络）
docker exec web ping -c 1 db
```

```
ping: bad address 'db'
```

```bash
# ✅ 后端能访问数据库（同一网络）
docker exec api ping -c 1 db
```

```
PING db (172.22.0.2): 56 data bytes
64 bytes from 172.22.0.2: seq=0 ttl=64 time=0.074 ms
```

网络拓扑：

```
frontend_net          backend_net
┌──────────────┐      ┌──────────────┐
│              │      │              │
│  ┌──────┐   │      │   ┌──────┐   │
│  │ web  │   │      │   │  db  │   │
│  └──────┘   │      │   └──────┘   │
│       ↑     │      │     ↑        │
│  ┌────┴───┐ │      │ ┌──┴─────┐   │
│  │  api   │─┼──────┼─│  api   │   │
│  └────────┘ │      │ └────────┘   │
│             │      │              │
└──────────────┘      └──────────────┘

web ──×── db   (隔离！)
web ──✓── api  (frontend_net)
api ──✓── db   (backend_net)
```

### 实战 3：清理

```bash
# 删除网络（需要先移除关联的容器）
docker rm -f app postgres redis api web db
docker network rm app_network frontend_net backend_net
```

---

## 常见问题与踩坑

### 1. 容器之间 ping 不通

**原因**：容器在默认 bridge 网络，没有 DNS，只能用 IP。

```bash
# 检查是否在同一个网络
docker inspect --format '{{.NetworkSettings.Networks}}' container_a
docker inspect --format '{{.NetworkSettings.Networks}}' container_b
```

**解决**：使用自定义网络。

### 2. 端口映射了但访问不了

```bash
# 检查容器是否在运行
docker ps | grep my_container

# 检查容器内服务是否监听了正确端口
docker exec my_container ss -tlnp

# 常见坑：服务监听 127.0.0.1 而不是 0.0.0.0
# 在容器内 127.0.0.1 只接受容器内部连接！
```

**解决**：确保容器内服务监听 `0.0.0.0` 而不是 `127.0.0.1`。

### 3. 自定义网络里用容器名访问失败

```bash
# 检查容器是否真的加入了该网络
docker network inspect my_network --format '{{range .Containers}}{{.Name}}{{end}}'
```

**常见原因**：容器启动时没有指定 `--network`，后来用 `docker network connect` 连接，但容器内的 DNS 缓存了旧结果。重启容器即可。

### 4. 容器无法访问外网

```bash
# 检查 DNS
docker exec my_container nslookup baidu.com

# 检查宿主机的 IP 转发是否开启
sysctl net.ipv4.ip_forward
```

```
net.ipv4.ip_forward = 1    # 必须是 1
```

如果为 0，编辑 `/etc/docker/daemon.json`：

```json
{
    "ip-forward": true
}
```

然后 `sudo systemctl restart docker`。

### 5. 多个容器绑定同一端口

```bash
# 错误做法：都映射到宿主机 8080
docker run -d -p 8080:80 nginx
docker run -d -p 8080:80 apache  # ❌ 端口冲突

# 正确做法：用不同宿主机端口
docker run -d -p 8080:80 nginx
docker run -d -p 8081:80 apache  # ✅
```

### 6. docker network rm 失败

```bash
docker network rm my_network
```

```
Error response from daemon: network my_network id ... has active endpoints
```

**原因**：还有容器连接在这个网络上。

```bash
# 查看哪些容器还在用
docker network inspect my_network --format '{{range .Containers}}{{.Name}} {{end}}'

# 断开或删除容器后再删除网络
docker rm -f $(docker ps -aq --filter network=my_network)
docker network rm my_network
```

---

## 速查表

```bash
# 网络管理
docker network ls                            # 列出所有网络
docker network create my_net                 # 创建自定义网络
docker network create -d bridge --subnet 10.0.0.0/24 my_net  # 自定义子网
docker network inspect my_net                # 查看详情
docker network rm my_net                     # 删除网络
docker network prune                         # 清理未使用的网络

# 容器网络操作
docker network connect my_net container      # 接入网络
docker network disconnect my_net container   # 断开网络
docker run --network my_net ...              # 启动时指定网络
docker run --network host ...                # host 模式
docker run --network none ...                # 无网络

# 端口映射
docker run -p 8080:80 ...                    # 映射端口
docker run -p 127.0.0.1:8080:80 ...         # 只允许本机
docker run -p 8080:80 -p 8443:443 ...        # 多端口映射
docker port container                        # 查看端口映射

# 调试
docker exec container ping target            # 测试连通性
docker exec container nslookup hostname      # 测试 DNS
docker exec container cat /etc/resolv.conf   # 查看 DNS 配置
```

---

> **下一篇**：[04-Docker数据管理](04-Docker数据管理.md) —— 容器中的数据如何持久化？
