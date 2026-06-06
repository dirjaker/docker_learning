# Docker & Kubernetes 从零到实战

> 从 Docker 基础到 Kubernetes 集群部署，手把手教你掌握容器化技术栈

---

## 项目概述

本项目是一套系统化的 Docker & Kubernetes 学习资源，包含 **11 篇文档**、**6 个可运行示例** 和 **3 份速查表**。内容从最基础的容器概念讲起，逐步深入到生产级 Kubernetes 集群部署，覆盖容器化技术栈的核心知识体系。

| 维度 | 说明 |
|------|------|
| 目标人群 | 后端开发者、DevOps 初学、运维工程师 |
| 学习方式 | 理论 + 实操，每个概念都有可运行的示例 |
| 覆盖范围 | Docker → Docker Compose → Kubernetes |
| 内容深度 | 从入门到生产级实战 |
| 预计时长 | 10 天完成全部内容（每天 2-3 小时） |

---

## 项目结构总览

| 类别 | 数量 | 说明 |
|------|------|------|
| 学习文档 | 11 篇 | 涵盖 Docker 基础、Dockerfile、Compose、K8s 核心资源、网络、存储、部署实战、选型指南 |
| 实战示例 | 6 个 | 可直接运行的完整项目，从 hello-world 到生产部署 |
| 速查表 | 3 份 | Docker、Docker Compose、Kubernetes 常用命令速查 |

---

## 目录结构

```
docker_learning/
├── README.md                              # 本文件
├── 01-Docker基础入门.md                    # 镜像、容器、Dockerfile 入门
├── 02-Dockerfile最佳实践.md                # 多阶段构建、镜像优化、安全加固
├── 03-Docker网络.md                        # bridge、host、overlay、端口映射
├── 04-Docker存储.md                        # volumes、bind mounts、tmpfs
├── 05-Docker-Compose入门.md                # 单机多容器编排基础
├── 06-Docker-Compose实战项目.md            # 完整项目编排示例
├── 07-Kubernetes基础概念.md                # Pod、Node、Cluster 核心概念
├── 08-Kubernetes核心资源.md                # Deployment、Service、ConfigMap、Secret
├── 09-Kubernetes网络与存储.md              # Ingress、PV、PVC、StorageClass
├── 10-Kubernetes实战部署.md                # 从零部署一个完整应用
├── 11-Docker-vs-K8s选型指南.md             # 技术选型与决策依据
├── examples/                              # 可运行的示例代码
│   ├── 01-hello-docker/                   # Docker 入门示例
│   ├── 02-python-app/                     # Python 应用容器化
│   ├── 03-multi-container/                # 多容器应用示例
│   ├── 04-docker-compose/                 # Docker Compose 示例
│   ├── 05-k8s-basic/                      # K8s 基础资源示例
│   └── 06-k8s-production/                 # K8s 生产部署示例
└── cheatsheets/                           # 速查表
    ├── docker-cheatsheet.md               # Docker 命令速查
    ├── compose-cheatsheet.md              # Compose 命令速查
    └── k8s-cheatsheet.md                  # K8s 命令速查
```

---

## 学习路线

建议按以下顺序学习，每个阶段配合对应文档和示例动手实操。

### 第一阶段：Docker 基础（Day 1-2）

| 学习内容 | 文档 | 示例 |
|----------|------|------|
| 镜像与容器基本概念 | 01-Docker基础入门.md | 01-hello-docker |
| Dockerfile 编写与优化 | 02-Dockerfile最佳实践.md | 02-python-app |

**学习目标：** 理解容器与虚拟机的区别，掌握镜像拉取、容器运行、Dockerfile 编写。

### 第二阶段：Docker 进阶（Day 3-4）

| 学习内容 | 文档 | 示例 |
|----------|------|------|
| Docker 网络模型 | 03-Docker网络.md | 03-multi-container |
| 数据卷与存储管理 | 04-Docker存储.md | 03-multi-container |

**学习目标：** 掌握容器间网络通信、数据持久化方案，能独立搭建多容器应用。

### 第三阶段：Docker Compose（Day 5-6）

| 学习内容 | 文档 | 示例 |
|----------|------|------|
| Compose 语法与基础 | 05-Docker-Compose入门.md | 04-docker-compose |
| 完整项目编排实战 | 06-Docker-Compose实战项目.md | 04-docker-compose |

**学习目标：** 使用 Compose 编排多容器应用，掌握依赖管理、环境变量、健康检查。

### 第四阶段：Kubernetes（Day 7-10）

| 学习内容 | 文档 | 示例 |
|----------|------|------|
| K8s 架构与核心概念 | 07-Kubernetes基础概念.md | 05-k8s-basic |
| 核心资源对象 | 08-Kubernetes核心资源.md | 05-k8s-basic |
| 网络与存储 | 09-Kubernetes网络与存储.md | 05-k8s-basic |
| 生产级部署实战 | 10-Kubernetes实战部署.md | 06-k8s-production |
| 技术选型指南 | 11-Docker-vs-K8s选型指南.md | — |

**学习目标：** 掌握 K8s 核心资源管理，能独立完成应用部署、扩缩容、滚动更新。

---

## 文档清单

| 编号 | 文件名 | 主题 | 核心内容 |
|------|--------|------|----------|
| 01 | 01-Docker基础入门.md | Docker 入门 | 容器 vs 虚拟机、镜像管理、容器生命周期、Docker CLI 基础 |
| 02 | 02-Dockerfile最佳实践.md | Dockerfile 进阶 | 多阶段构建、镜像瘦身、构建缓存、安全扫描、非 root 用户 |
| 03 | 03-Docker网络.md | Docker 网络 | bridge/host/overlay 网络、端口映射、容器间通信、DNS 解析 |
| 04 | 04-Docker存储.md | Docker 存储 | 命名卷、匿名卷、bind mount、tmpfs、数据备份与迁移 |
| 05 | 05-Docker-Compose入门.md | Compose 基础 | docker-compose.yml 语法、服务编排、网络配置、环境变量 |
| 06 | 06-Docker-Compose实战项目.md | Compose 实战 | Web + DB + Cache 完整编排、健康检查、依赖顺序、多环境配置 |
| 07 | 07-Kubernetes基础概念.md | K8s 入门 | K8s 架构、Master/Worker 节点、Pod、Namespace、kubectl 基础 |
| 08 | 08-Kubernetes核心资源.md | K8s 核心资源 | Deployment、Service、ConfigMap、Secret、HPA、RBAC |
| 09 | 09-Kubernetes网络与存储.md | K8s 网络与存储 | Service 网络、Ingress 控制器、PV/PVC、StorageClass、StatefulSet |
| 10 | 10-Kubernetes实战部署.md | K8s 实战 | 从零部署 Web 应用、配置管理、滚动更新、回滚、监控 |
| 11 | 11-Docker-vs-K8s选型指南.md | 技术选型 | 适用场景对比、成本分析、迁移路径、决策树 |

---

## 示例清单

| 编号 | 目录 | 难度 | 说明 | 对应文档 |
|------|------|------|------|----------|
| 01 | examples/01-hello-docker | ⭐ 入门 | 最简单的 Docker 镜像构建与运行 | 01-Docker基础入门.md |
| 02 | examples/02-python-app | ⭐⭐ 初级 | Python Flask 应用容器化，含多阶段构建 | 02-Dockerfile最佳实践.md |
| 03 | examples/03-multi-container | ⭐⭐ 初级 | Web + Redis 多容器网络通信 | 03-Docker网络.md、04-Docker存储.md |
| 04 | examples/04-docker-compose | ⭐⭐⭐ 中级 | Compose 编排 Web + MySQL + Redis | 05/06-Docker-Compose*.md |
| 05 | examples/05-k8s-basic | ⭐⭐⭐ 中级 | K8s 基础资源部署：Deployment + Service + ConfigMap | 07/08-Kubernetes*.md |
| 06 | examples/06-k8s-production | ⭐⭐⭐⭐ 高级 | 生产级部署：Ingress + HPA + PV + 滚动更新 | 09/10-Kubernetes*.md |

---

## 速查表

提供 3 份速查表，覆盖日常开发中最常用的命令和配置：

| 速查表 | 文件 | 覆盖内容 |
|--------|------|----------|
| Docker 速查 | cheatsheets/docker-cheatsheet.md | 镜像管理、容器操作、网络、卷、日志、调试 |
| Compose 速查 | cheatsheets/compose-cheatsheet.md | 服务管理、网络、卷、环境变量、扩展字段 |
| K8s 速查 | cheatsheets/k8s-cheatsheet.md | 资源管理、部署、服务、配置、调试、常用 kubectl 命令 |

---

## 快速开始

### 环境准备

| 工具 | 最低版本 | 安装命令 |
|------|----------|----------|
| Docker Engine | 20.10+ | `curl -fsSL https://get.docker.com \| sh` |
| Docker Compose | v2.0+ | 随 Docker Desktop 自带，或 `docker compose version` |
| kubectl | 1.28+ | `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"` |
| minikube（可选） | 1.30+ | `curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube` |

### 5 分钟快速体验

```bash
# 1. 验证 Docker 安装
docker run hello-world

# 2. 克隆本仓库
git clone <repo-url> && cd docker_learning

# 3. 运行第一个示例
cd examples/01-hello-docker
docker build -t hello-docker .
docker run --rm hello-docker

# 4. 运行 Compose 示例
cd ../04-docker-compose
docker compose up -d
docker compose ps

# 5. （可选）启动 minikube 运行 K8s 示例
minikube start
cd ../05-k8s-basic
kubectl apply -f .
kubectl get pods
```

### 推荐阅读顺序

1. 先通读 `01-Docker基础入门.md`，跑通 `examples/01-hello-docker`
2. 按学习路线依次推进，每篇文档配合对应示例
3. 遇到命令不确定时查阅 `cheatsheets/` 下的速查表
4. 完成全部学习后，参考 `11-Docker-vs-K8s选型指南.md` 做技术选型决策

---

## 知识图谱

| 阶段 | 核心技能 | 掌握标志 |
|------|----------|----------|
| Docker 基础 | 镜像构建、容器管理、Dockerfile 编写 | 能独立编写 Dockerfile 并优化镜像体积 |
| Docker 进阶 | 网络模型、数据持久化 | 能配置多容器网络通信并管理数据卷 |
| Docker Compose | 多服务编排、环境管理 | 能用 Compose 编排完整应用栈 |
| K8s 基础 | Pod、Deployment、Service | 能在 K8s 上部署和暴露应用 |
| K8s 进阶 | 配置管理、网络、存储、扩缩容 | 能完成生产级部署并配置自动扩缩容 |
| 技术选型 | 场景分析、成本评估 | 能根据业务需求选择合适方案 |

---

## 常见问题

| 问题 | 解答 |
|------|------|
| 学习本项目需要什么基础？ | 基本的 Linux 命令行操作和任意一门后端语言的开发经验即可 |
| 需要什么硬件配置？ | 建议 8GB+ 内存，运行 K8s 示例建议 16GB+ 或使用云端虚拟机 |
| Docker Desktop 和 Docker Engine 有什么区别？ | Desktop 是带 GUI 的完整套件（含 Compose、K8s），Engine 是纯命令行服务端 |
| minikube 和 kind 哪个更好？ | minikube 更适合初学者，kind 更轻量适合 CI 测试，本项目默认使用 minikube |
| 生产环境推荐用什么？ | 云厂商托管 K8s（如 EKS/GKE/ACK）+ Helm Charts，详见第 11 篇文档 |

---

## 许可证

本项目采用 MIT 许可证，欢迎自由使用和分享。
