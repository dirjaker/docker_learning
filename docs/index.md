---
layout: home

hero:
  name: "Docker Learning"
  text: "Docker & Kubernetes 学习实战"
  tagline: 从 Docker 基础到 Kubernetes 集群部署，手把手教你掌握容器化技术栈
  actions:
    - theme: brand
      text: 开始学习
      link: /01-Docker基础入门
    - theme: alt
      text: Docker 速查
      link: /cheatsheets/docker-cheatsheet

features:
  - title: 🐳 Docker 基础
    details: 容器 vs 虚拟机、镜像管理、容器生命周期、Dockerfile 编写与优化
    link: /01-Docker基础入门
  - title: 🌐 网络与存储
    details: bridge/host/overlay 网络、数据卷、bind mount、数据持久化方案
    link: /03-Docker网络
  - title: 📦 Docker Compose
    details: 多服务编排、依赖管理、环境变量、健康检查、多环境配置
    link: /05-Docker-Compose入门
  - title: ☸️ Kubernetes
    details: Pod、Deployment、Service、Ingress、HPA、从零到生产部署
    link: /07-Kubernetes基础概念
  - title: 📋 速查表
    details: Docker、Docker Compose、Kubernetes 常用命令速查
    link: /cheatsheets/docker-cheatsheet
  - title: 🔧 实战示例
    details: 6 个可运行的完整项目，从 hello-world 到生产级部署
    link: /examples/01-hello-docker/
---

## 学习路线

| 阶段 | 内容 | 天数 | 文档 |
|------|------|------|------|
| **第一阶段** | Docker 基础 | Day 1-2 | [Docker 基础入门](/01-Docker基础入门) · [Dockerfile 最佳实践](/02-Dockerfile最佳实践) |
| **第二阶段** | Docker 进阶 | Day 3-4 | [Docker 网络](/03-Docker网络) · [Docker 存储](/04-Docker存储) |
| **第三阶段** | Docker Compose | Day 5-6 | [Compose 入门](/05-Docker-Compose入门) · [Compose 实战](/06-Docker-Compose实战项目) |
| **第四阶段** | Kubernetes 基础 | Day 7-8 | [K8s 基础概念](/07-Kubernetes基础概念) · [K8s 核心资源](/08-Kubernetes核心资源) |
| **第五阶段** | Kubernetes 进阶 | Day 9-10 | [K8s 网络与存储](/09-Kubernetes网络与存储) · [K8s 实战部署](/10-Kubernetes实战部署) |
| **总结** | 技术选型 | Day 10 | [Docker vs K8s 选型指南](/11-Docker-vs-K8s选型指南) |

## 实战示例

| 示例 | 说明 | 关联章节 |
|------|------|---------|
| [01 - Hello Docker](/examples/01-hello-docker/) | 最简 Docker 镜像，Python HTTP 服务器 | Docker 基础入门 |
| [02 - Python Flask 应用](/examples/02-python-app/) | Flask 应用，多阶段构建优化镜像 | Dockerfile 最佳实践 |
| [03 - 多容器应用](/examples/03-multi-container/) | Web + Worker + RabbitMQ 多容器编排 | Docker Compose 入门 |
| [04 - Docker Compose 示例](/examples/04-docker-compose/) | Flask + Redis 完整 Compose 示例 | Compose 入门 |
| [05 - K8s 基础部署](/examples/05-k8s-basic/) | K8s 核心资源对象演示 | K8s 基础概念 |
| [06 - K8s 生产级部署](/examples/06-k8s-production/) | PostgreSQL + Redis + API 生产级部署 | K8s 实战部署 |
