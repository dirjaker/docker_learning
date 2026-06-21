# 更新日志

本文档记录了项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

---

## [v1.1] - 2026-06-22

### 文档优化

- **README.md**：新增项目结构树、完整文档目录表、实战示例表、学习路线（含天数规划）、贡献指南
- **docs/index.md**：新增实战示例列表、学习路线增加天数规划
- **docs/.vitepress/config.mts**：侧边栏新增「实战示例」分类，覆盖 6 个示例项目链接
- **docs/CHANGELOG.md**：创建更新日志文件

---

## [v1.0] - 2026-06-14

### 初始发布

#### 核心文档（11 篇）

| 序号 | 文档 | 内容 |
|------|------|------|
| 01 | Docker 基础入门 | 核心概念、安装、镜像与容器操作、Dockerfile 基础 |
| 02 | Dockerfile 最佳实践 | 指令详解、多阶段构建、镜像优化、安全实践 |
| 03 | Docker 网络 | bridge/host/overlay/macvlan、DNS 服务发现 |
| 04 | Docker 存储 | Volume、Bind Mount、tmpfs、数据持久化 |
| 05 | Docker Compose 入门 | YAML 语法、服务编排、环境变量、健康检查 |
| 06 | Docker Compose 实战项目 | 博客系统、监控系统、微服务网关 |
| 07 | Kubernetes 基础概念 | K8s 架构、安装、Pod、Namespace |
| 08 | Kubernetes 核心资源 | Label/Deployment/Service/ConfigMap/Secret |
| 09 | Kubernetes 网络与存储 | CNI 网络、Service/Ingress、PV/PVC/StorageClass |
| 10 | Kubernetes 实战部署 | 全栈应用从零部署 |
| 11 | Docker vs K8s 选型指南 | 技术对比与选型建议 |

#### 速查表（3 份）

- Docker 命令速查表
- Docker Compose 命令与配置速查表
- Kubernetes 常用命令速查表

#### 实战示例（6 个）

- 01 - Hello Docker：最简镜像示例
- 02 - Python Flask 应用：多阶段构建
- 03 - 多容器应用：Web + Worker + RabbitMQ
- 04 - Docker Compose 示例：Flask + Redis
- 05 - K8s 基础部署：核心资源对象演示
- 06 - K8s 生产级部署：PostgreSQL + Redis + API

#### 基础设施

- VitePress 文档站点配置与本地搜索
- GitHub Pages 自动部署
- SVG Banner 设计
- MIT 开源协议
