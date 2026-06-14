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
    link: /01-Docker基础入门
---

## 学习路线

| 阶段 | 内容 | 文档 |
|------|------|------|
| 第一阶段 | Docker 基础（Day 1-2） | [Docker 基础入门](/01-Docker基础入门) · [Dockerfile 最佳实践](/02-Dockerfile最佳实践) |
| 第二阶段 | Docker 进阶（Day 3-4） | [Docker 网络](/03-Docker网络) · [Docker 存储](/04-Docker存储) |
| 第三阶段 | Docker Compose（Day 5-6） | [Compose 入门](/05-Docker-Compose入门) · [Compose 实战](/06-Docker-Compose实战项目) |
| 第四阶段 | Kubernetes（Day 7-10） | [K8s 基础](/07-Kubernetes基础概念) · [K8s 核心资源](/08-Kubernetes核心资源) · [K8s 部署](/10-Kubernetes实战部署) |
