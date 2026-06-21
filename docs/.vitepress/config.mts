import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/docker_learning/',
  title: 'Docker Learning',
  description: 'Docker & Kubernetes 学习实战',
  lang: 'zh-CN',
  ignoreDeadLinks: true,
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: 'Docker', link: '/01-Docker基础入门' },
      { text: 'Docker Compose', link: '/05-Docker-Compose入门' },
      { text: 'Kubernetes', link: '/07-Kubernetes基础概念' },
      { text: '速查表', link: '/cheatsheets/docker-cheatsheet' },
      { text: '更新日志', link: '/CHANGELOG' },
      { text: 'GitHub', link: 'https://github.com/dirjaker/docker_learning' }
    ],
    sidebar: [
      {
        text: 'Docker 基础',
        items: [
          { text: 'Docker 基础入门', link: '/01-Docker基础入门' },
          { text: 'Dockerfile 最佳实践', link: '/02-Dockerfile最佳实践' },
          { text: 'Docker 网络', link: '/03-Docker网络' },
          { text: 'Docker 存储', link: '/04-Docker存储' },
        ]
      },
      {
        text: 'Docker Compose',
        items: [
          { text: 'Compose 入门', link: '/05-Docker-Compose入门' },
          { text: 'Compose 实战项目', link: '/06-Docker-Compose实战项目' },
        ]
      },
      {
        text: 'Kubernetes',
        items: [
          { text: 'K8s 基础概念', link: '/07-Kubernetes基础概念' },
          { text: 'K8s 核心资源', link: '/08-Kubernetes核心资源' },
          { text: 'K8s 网络与存储', link: '/09-Kubernetes网络与存储' },
          { text: 'K8s 实战部署', link: '/10-Kubernetes实战部署' },
          { text: 'Docker vs K8s 选型指南', link: '/11-Docker-vs-K8s选型指南' },
        ]
      },
      {
        text: '速查表',
        items: [
          { text: 'Docker 速查', link: '/cheatsheets/docker-cheatsheet' },
          { text: 'Compose 速查', link: '/cheatsheets/compose-cheatsheet' },
          { text: 'K8s 速查', link: '/cheatsheets/k8s-cheatsheet' },
        ]
      },
      {
        text: '实战示例',
        items: [
          { text: '01 - Hello Docker', link: '/examples/01-hello-docker/' },
          { text: '02 - Python Flask 应用', link: '/examples/02-python-app/' },
          { text: '03 - 多容器应用', link: '/examples/03-multi-container/' },
          { text: '04 - Docker Compose 示例', link: '/examples/04-docker-compose/' },
          { text: '05 - K8s 基础部署', link: '/examples/05-k8s-basic/' },
          { text: '06 - K8s 生产级部署', link: '/examples/06-k8s-production/' },
        ]
      }
    ],
    socialLinks: [
      { icon: 'github', link: 'https://github.com/dirjaker/docker_learning' }
    ],
    outline: {
      label: '页面导航'
    },
    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索文档', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' }
          }
        }
      }
    },
    footer: {
      message: 'Docker & Kubernetes 学习实战',
      copyright: '© 2026 dirjaker'
    }
  }
})
