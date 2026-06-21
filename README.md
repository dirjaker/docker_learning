<div align="center">

<img src="assets/banner.svg" width="100%" alt="Docker 学习笔记">

<br>

### 🐳 Docker 学习笔记

[![Stars](https://img.shields.io/github/stars/dirjaker/docker_learning?style=flat-square&label=Stars&color=FFD700)](https://github.com/dirjaker/docker_learning/stargazers)
[![Forks](https://img.shields.io/github/forks/dirjaker/docker_learning?style=flat-square&label=Forks&color=4A90D9)](https://github.com/dirjaker/docker_learning/network/members)
[![Contributors](https://img.shields.io/github/contributors/dirjaker/docker_learning?style=flat-square&label=Contributors&color=8B4513)](https://github.com/dirjaker/docker_learning/graphs/contributors)
[![License](https://img.shields.io/github/license/dirjaker/docker_learning?style=flat-square&label=License&color=20B2AA)](https://github.com/dirjaker/docker_learning/blob/dev/LICENSE)

</div>

---

> 📖 一份从 Docker 入门到 Kubernetes 实战的完整学习教程，涵盖 11 篇系统文档、6 个可运行示例、3 份命令速查表，由 VitePress 驱动并部署到 GitHub Pages。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 📚 **系统文档** | 11 篇从入门到进阶的完整文档 |
| 💻 **实战示例** | 6 个可直接运行的 Docker Compose 示例 |
| 📋 **速查表** | Docker、K8s、Compose 命令速查 |
| 🔧 **最佳实践** | Dockerfile 编写和镜像优化技巧 |
| 🚀 **CI/CD** | Docker 在持续集成中的实际应用 |
| 📊 **架构图解** | 容器编排和微服务架构可视化 |

## 📖 在线文档

<div align="center">

**📚 [点击访问在线文档](https://dirjaker.github.io/docker_learning/)**

</div>

## 📁 项目结构

```
docker_learning/
├── README.md                          # 项目说明
├── LICENSE                            # MIT 开源协议
├── requirements.txt                   # Python 依赖
├── assets/
│   └── banner.svg                     # 项目 Banner
│
├── 01-Docker基础入门.md               # Docker 入门：镜像、容器、仓库
├── 02-Dockerfile最佳实践.md           # Dockerfile 指令详解与优化
├── 03-Docker网络.md                   # bridge/host/overlay 网络
├── 04-Docker存储.md                   # Volume/Bind Mount 持久化
├── 05-Docker-Compose入门.md           # Compose 基础语法与使用
├── 06-Docker-Compose实战项目.md       # 博客、监控、微服务网关
├── 07-Kubernetes基础概念.md           # K8s 架构、Pod、Namespace
├── 08-Kubernetes核心资源.md           # Deployment/Service/ConfigMap
├── 09-Kubernetes网络与存储.md         # CNI 网络与 PV/PVC 存储
├── 10-Kubernetes实战部署.md           # 全栈应用从零到部署
├── 11-Docker-vs-K8s选型指南.md        # 技术选型与对比
│
├── cheatsheets/
│   ├── docker-cheatsheet.md           # Docker 命令速查
│   ├── compose-cheatsheet.md          # Compose 命令速查
│   └── k8s-cheatsheet.md              # K8s 命令速查
│
├── examples/
│   ├── 01-hello-docker/               # Hello Docker 示例
│   ├── 02-python-app/                 # Flask 多阶段构建
│   ├── 03-multi-container/            # 多容器编排示例
│   ├── 04-docker-compose/             # Compose 完整示例
│   ├── 05-k8s-basic/                  # K8s 基础部署
│   └── 06-k8s-production/             # K8s 生产级部署
│
└── docs/                              # VitePress 站点源码
    ├── index.md                       # 首页
    ├── .vitepress/config.mts          # VitePress 配置
    ├── 01-11*.md                      # 文档（与顶层同步）
    ├── cheatsheets/                   # 速查表
    └── examples/                      # 实战示例
```

## 📚 文档目录

### Docker 基础（第一阶段）

| 序号 | 章节 | 内容简介 |
|------|------|---------|
| 01 | [Docker 基础入门](01-Docker基础入门.md) | Docker 核心概念、安装、镜像与容器操作、Dockerfile 基础 |
| 02 | [Dockerfile 最佳实践](02-Dockerfile最佳实践.md) | 指令详解、多阶段构建、镜像优化、安全实践 |
| 03 | [Docker 网络](03-Docker网络.md) | bridge/host/overlay/macvlan 网络、DNS 服务发现 |
| 04 | [Docker 存储](04-Docker存储.md) | Volume、Bind Mount、tmpfs、数据持久化方案 |

### Docker Compose（第二阶段）

| 序号 | 章节 | 内容简介 |
|------|------|---------|
| 05 | [Docker Compose 入门](05-Docker-Compose入门.md) | YAML 语法、服务编排、环境变量、健康检查 |
| 06 | [Docker Compose 实战项目](06-Docker-Compose实战项目.md) | 博客系统、监控系统、微服务网关完整案例 |

### Kubernetes（第三阶段）

| 序号 | 章节 | 内容简介 |
|------|------|---------|
| 07 | [Kubernetes 基础概念](07-Kubernetes基础概念.md) | K8s 架构、安装、Pod、Namespace |
| 08 | [Kubernetes 核心资源](08-Kubernetes核心资源.md) | Label/Deployment/Service/ConfigMap/Secret |
| 09 | [Kubernetes 网络与存储](09-Kubernetes网络与存储.md) | CNI 网络模型、Service/Ingress、PV/PVC/StorageClass |
| 10 | [Kubernetes 实战部署](10-Kubernetes实战部署.md) | 全栈应用从零部署：前端+后端+数据库+缓存 |
| 11 | [Docker vs K8s 选型指南](11-Docker-vs-K8s选型指南.md) | Docker/Compose/K8s 对比与技术选型 |

### 速查表

| 速查表 | 链接 |
|--------|------|
| Docker 命令速查 | [docker-cheatsheet.md](cheatsheets/docker-cheatsheet.md) |
| Docker Compose 速查 | [compose-cheatsheet.md](cheatsheets/compose-cheatsheet.md) |
| Kubernetes 速查 | [k8s-cheatsheet.md](cheatsheets/k8s-cheatsheet.md) |

## 💻 实战示例

| 示例 | 说明 | 关联章节 |
|------|------|---------|
| [01-hello-docker](examples/01-hello-docker/) | 最简 Docker 镜像，Python HTTP 服务器 | Docker 基础入门 |
| [02-python-app](examples/02-python-app/) | Flask 应用，多阶段构建优化镜像 | Dockerfile 最佳实践 |
| [03-multi-container](examples/03-multi-container/) | Web + Worker + RabbitMQ 多容器编排 | Docker Compose 入门 |
| [04-docker-compose](examples/04-docker-compose/) | Flask + Redis 完整 Compose 示例 | Compose 入门 |
| [05-k8s-basic](examples/05-k8s-basic/) | K8s 核心资源对象演示 | K8s 基础概念 |
| [06-k8s-production](examples/06-k8s-production/) | PostgreSQL + Redis + API 生产级部署 | K8s 实战部署 |

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/dirjaker/docker_learning.git
cd docker_learning

# 创建虚拟环境
conda create -n docker_learning python=3.12 -y
conda activate docker_learning

# 安装依赖
pip install -r requirements.txt

# 运行项目
python main.py
```

## 📖 学习路线

| 阶段 | 内容 | 天数 | 文档 |
|------|------|------|------|
| **第一阶段** | Docker 基础 | Day 1-2 | [Docker 基础入门](01-Docker基础入门.md) · [Dockerfile 最佳实践](02-Dockerfile最佳实践.md) |
| **第二阶段** | Docker 进阶 | Day 3-4 | [Docker 网络](03-Docker网络.md) · [Docker 存储](04-Docker存储.md) |
| **第三阶段** | Docker Compose | Day 5-6 | [Compose 入门](05-Docker-Compose入门.md) · [Compose 实战](06-Docker-Compose实战项目.md) |
| **第四阶段** | Kubernetes 基础 | Day 7-8 | [K8s 基础概念](07-Kubernetes基础概念.md) · [K8s 核心资源](08-Kubernetes核心资源.md) |
| **第五阶段** | Kubernetes 进阶 | Day 9-10 | [K8s 网络与存储](09-Kubernetes网络与存储.md) · [K8s 实战部署](10-Kubernetes实战部署.md) |
| **总结** | 技术选型 | Day 10 | [Docker vs K8s 选型指南](11-Docker-vs-K8s选型指南.md) |

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **文档引擎** | VitePress |
| **容器** | Docker, Docker Compose |
| **编排** | Kubernetes |
| **部署** | GitHub Pages |

## 📝 开发日志

- [x] 11 篇核心文档
- [x] 6 个实战示例
- [x] 3 个速查表
- [x] GitHub Pages 部署
- [x] VitePress 搜索
- [ ] 视频教程
- [ ] 互动实验环境
- [ ] 认证考试指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -m 'feat: add my feature'`
4. 推送分支：`git push origin feature/my-feature`
5. 提交 Pull Request

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/docker_learning](https://github.com/dirjaker/docker_learning)

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

</div>
