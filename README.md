# Docker & Kubernetes 从零到实战

> 从 Docker 基础到 Kubernetes 集群部署，手把手教你掌握容器化技术栈

---

## 项目定位

| 维度 | 说明 |
|------|------|
| 目标人群 | 后端开发者、DevOps 初学者 |
| 学习方式 | 理论 + 实操，每个概念都有可运行的示例 |
| 覆盖范围 | Docker → Docker Compose → Kubernetes |
| 深度 | 从入门到生产级实战 |

---

## 目录结构

```
docker_learning/
├── README.md                              # 本文件
├── 01-Docker基础入门.md                    # 镜像、容器、Dockerfile
├── 02-Dockerfile最佳实践.md                # 多阶段构建、镜像优化、安全
├── 03-Docker网络.md                        # bridge、host、overlay、端口映射
├── 04-Docker存储.md                        # volumes、bind mounts、tmpfs
├── 05-Docker-Compose入门.md                # 单机多容器编排
├── 06-Docker-Compose实战项目.md            # 完整项目编排示例
├── 07-Kubernetes基础概念.md                # Pod、Node、Cluster
├── 08-Kubernetes核心资源.md                # Deployment、Service、ConfigMap、Secret
├── 09-Kubernetes网络与存储.md              # Ingress、PV、PVC、StorageClass
├── 10-Kubernetes实战部署.md                # 从零部署一个完整应用
├── 11-Docker-vs-K8s选型指南.md             # 什么时候用什么
├── examples/                              # 可运行的示例代码
│   ├── 01-hello-docker/                   # Docker 入门示例
│   ├── 02-python-app/                     # Python 应用容器化
│   ├── 03-multi-container/                # 多容器应用
│   ├── 04-docker-compose/                 # Compose 示例
│   ├── 05-k8s-basic/                      # K8s 基础示例
│   └── 06-k8s-production/                 # K8s 生产部署
└── cheatsheets/                           # 速查表
    ├── docker-cheatsheet.md
    ├── compose-cheatsheet.md
    └── k8s-cheatsheet.md
```

---

## 学习路线

```
Day 1-2: Docker 基础
  ├── 01-Docker基础入门.md
  ├── 02-Dockerfile最佳实践.md
  └── examples/01-hello-docker/, 02-python-app/

Day 3-4: Docker 进阶
  ├── 03-Docker网络.md
  ├── 04-Docker存储.md
  └── examples/03-multi-container/

Day 5-6: Docker Compose
  ├── 05-Docker-Compose入门.md
  ├── 06-Docker-Compose实战项目.md
  └── examples/04-docker-compose/

Day 7-10: Kubernetes
  ├── 07-Kubernetes基础概念.md
  ├── 08-Kubernetes核心资源.md
  ├── 09-Kubernetes网络与存储.md
  ├── 10-Kubernetes实战部署.md
  └── examples/05-k8s-basic/, 06-k8s-production/
```

---

## 快速开始

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 运行第一个容器
docker run hello-world

# 3. 进入学习
cat 01-Docker基础入门.md
```
