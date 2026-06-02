# Docker Compose 实战项目

## 目录

- [实战项目 1：博客系统](#实战项目-1博客系统)
- [实战项目 2：监控系统](#实战项目-2监控系统)
- [实战项目 3：微服务网关](#实战项目-3微服务网关)
- [Compose 高级特性](#compose-高级特性)
- [最佳实践](#最佳实践)

---

## 实战项目 1：博客系统

### 技术栈

| 组件       | 用途       |
| ---------- | ---------- |
| Next.js    | 前端 + API |
| PostgreSQL | 数据库     |
| Redis      | 缓存       |
| Nginx      | 反向代理   |

### 项目结构

```
blog-system/
├── docker-compose.yml
├── .env
├── .env.example
├── app/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   └── api/
│       │       ├── health/route.ts
│       │       ├── posts/route.ts
│       │       └── posts/[id]/route.ts
│       └── lib/
│           ├── db.ts
│           └── redis.ts
├── nginx/
│   ├── Dockerfile
│   └── conf.d/
│       └── default.conf
├── db/
│   └── init.sql
└── scripts/
    ├── backup.sh
    └── restore.sh
```

### 环境变量文件 .env

```bash
# 应用配置
APP_NAME=my-blog
APP_PORT=3000
NODE_ENV=production

# PostgreSQL 配置
POSTGRES_USER=bloguser
POSTGRES_PASSWORD=Change-Me-In-Production-2024!
POSTGRES_DB=blogdb
POSTGRES_PORT=5432

# Redis 配置
REDIS_PASSWORD=Redis-Change-Me-2024!
REDIS_PORT=6379

# Nginx 配置
NGINX_PORT=80
NGINX_SSL_PORT=443
SERVER_NAME=localhost

# 数据持久化路径
DATA_DIR=./data
```

### .env.example

```bash
# 复制为 .env 并修改为实际值
APP_NAME=my-blog
APP_PORT=3000
NODE_ENV=production
POSTGRES_USER=bloguser
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_DB=blogdb
POSTGRES_PORT=5432
REDIS_PASSWORD=your-redis-password
REDIS_PORT=6379
NGINX_PORT=80
NGINX_SSL_PORT=443
SERVER_NAME=your-domain.com
DATA_DIR=./data
```

### 数据库初始化脚本 db/init.sql

```sql
-- 创建文章表
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt VARCHAR(500),
    author VARCHAR(100) DEFAULT 'Admin',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    tags TEXT[] DEFAULT '{}',
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建评论表
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    author VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_posts_slug ON posts(slug);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_comments_post_id ON comments(post_id);

-- 插入示例数据
INSERT INTO posts (title, slug, content, excerpt, author, status, tags)
VALUES
    ('Docker 入门指南', 'docker-getting-started', 
     '# Docker 入门指南\n\nDocker 是一个开源的容器化平台...\n\n## 安装 Docker\n\n```bash\nsudo apt install docker.io\n```\n\n## 第一个容器\n\n```bash\ndocker run hello-world\n```',
     '本文介绍 Docker 的基本概念和使用方法。',
     'Admin', 'published', ARRAY['docker', 'devops', 'tutorial']),
    
    ('Docker Compose 实战', 'docker-compose-practice',
     '# Docker Compose 实战\n\nDocker Compose 用于定义和运行多容器应用...\n\n## 基本语法\n\n```yaml\nversion: "3.8"\nservices:\n  web:\n    image: nginx\n```',
     '通过实战项目学习 Docker Compose 的使用。',
     'Admin', 'published', ARRAY['docker-compose', 'devops']),
    
    ('Nginx 反向代理配置', 'nginx-reverse-proxy',
     '# Nginx 反向代理\n\nNginx 是一个高性能的 Web 服务器...\n\n## 基本配置\n\n```nginx\nserver {\n    listen 80;\n    location / {\n        proxy_pass http://backend:3000;\n    }\n}\n```',
     '学习如何使用 Nginx 配置反向代理。',
     'Admin', 'draft', ARRAY['nginx', 'devops']);
```

### 应用 Dockerfile app/Dockerfile

```dockerfile
# ========== 构建阶段 ==========
FROM node:20-alpine AS builder

WORKDIR /app

# 安装依赖（利用 Docker 缓存层）
COPY package.json package-lock.json ./
RUN npm ci --only=production && \
    cp -R node_modules /tmp/prod_modules && \
    npm ci

# 复制源代码并构建
COPY . .
RUN npm run build

# ========== 生产阶段 ==========
FROM node:20-alpine AS production

WORKDIR /app

# 安全：创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 从构建阶段复制产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 复制生产依赖
COPY --from=builder /tmp/prod_modules ./node_modules

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

EXPOSE 3000

# 切换到非 root 用户
USER nextjs

CMD ["node", "server.js"]
```

### 应用源代码

**app/package.json**

```json
{
  "name": "blog-app",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "pg": "^8.11.0",
    "ioredis": "^5.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/pg": "^8.10.0",
    "typescript": "^5.3.0"
  }
}
```

**app/next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // 在生产环境中通过环境变量配置
  env: {
    DATABASE_URL: process.env.DATABASE_URL,
    REDIS_URL: process.env.REDIS_URL,
  },
};

module.exports = nextConfig;
```

**app/src/lib/db.ts** — 数据库连接

```typescript
import { Pool, QueryResult } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,                    // 最大连接数
  idleTimeoutMillis: 30000,   // 空闲连接超时
  connectionTimeoutMillis: 5000, // 连接超时
});

// 连接池事件监听
pool.on('connect', () => {
  console.log('[DB] New client connected');
});

pool.on('error', (err) => {
  console.error('[DB] Unexpected error on idle client:', err);
});

export async function query<T = any>(text: string, params?: any[]): Promise<QueryResult<T>> {
  const start = Date.now();
  const result = await pool.query<T>(text, params);
  const duration = Date.now() - start;
  console.log('[DB] Query executed', { text: text.substring(0, 80), duration: `${duration}ms`, rows: result.rowCount });
  return result;
}

export async function getClient() {
  return pool.connect();
}

export default pool;
```

**app/src/lib/redis.ts** — Redis 连接

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379', {
  maxRetriesPerRequest: 3,
  retryStrategy(times) {
    if (times > 3) return null;
    return Math.min(times * 200, 2000);
  },
  lazyConnect: true,
});

redis.on('connect', () => console.log('[Redis] Connected'));
redis.on('error', (err) => console.error('[Redis] Error:', err.message));

// 带过期时间的缓存读取
export async function getCache<T>(key: string): Promise<T | null> {
  try {
    const data = await redis.get(key);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

export async function setCache(key: string, value: any, ttl: number = 3600): Promise<void> {
  try {
    await redis.setex(key, ttl, JSON.stringify(value));
  } catch (err) {
    console.error('[Redis] Cache write failed:', err);
  }
}

export async function deleteCache(pattern: string): Promise<void> {
  try {
    const keys = await redis.keys(pattern);
    if (keys.length > 0) {
      await redis.del(...keys);
    }
  } catch (err) {
    console.error('[Redis] Cache delete failed:', err);
  }
}

export default redis;
```

**app/src/app/api/health/route.ts** — 健康检查接口

```typescript
import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import redis from '@/lib/redis';

export async function GET() {
  const checks: Record<string, string> = {};
  let healthy = true;

  // 检查数据库
  try {
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();
    checks.postgres = 'ok';
  } catch {
    checks.postgres = 'error';
    healthy = false;
  }

  // 检查 Redis
  try {
    await redis.ping();
    checks.redis = 'ok';
  } catch {
    checks.redis = 'error';
    healthy = false;
  }

  return NextResponse.json(
    {
      status: healthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      checks,
      uptime: process.uptime(),
    },
    { status: healthy ? 200 : 503 }
  );
}
```

**app/src/app/api/posts/route.ts** — 文章 CRUD 接口

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getCache, setCache, deleteCache } from '@/lib/redis';

// GET /api/posts - 获取文章列表
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '10');
  const status = searchParams.get('status') || 'published';
  const offset = (page - 1) * limit;

  // 尝试从缓存读取
  const cacheKey = `posts:${status}:${page}:${limit}`;
  const cached = await getCache(cacheKey);
  if (cached) {
    return NextResponse.json({ ...cached, source: 'cache' });
  }

  // 从数据库查询
  const [dataResult, countResult] = await Promise.all([
    query(
      `SELECT id, title, slug, excerpt, author, status, tags, view_count, created_at, updated_at
       FROM posts WHERE status = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3`,
      [status, limit, offset]
    ),
    query('SELECT COUNT(*) FROM posts WHERE status = $1', [status]),
  ]);

  const total = parseInt(countResult.rows[0].count);
  const result = {
    posts: dataResult.rows,
    pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
  };

  // 写入缓存（5 分钟）
  await setCache(cacheKey, result, 300);

  return NextResponse.json({ ...result, source: 'database' });
}

// POST /api/posts - 创建文章
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { title, content, excerpt, tags, status } = body;

    if (!title || !content) {
      return NextResponse.json({ error: 'Title and content are required' }, { status: 400 });
    }

    // 生成 slug
    const slug = title
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
      .replace(/(^-|-$)/g, '');

    const result = await query(
      `INSERT INTO posts (title, slug, content, excerpt, tags, status)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [title, slug, content, excerpt || '', tags || [], status || 'draft']
    );

    // 清除列表缓存
    await deleteCache('posts:*');

    return NextResponse.json(result.rows[0], { status: 201 });
  } catch (error: any) {
    if (error.code === '23505') {
      return NextResponse.json({ error: 'A post with this title already exists' }, { status: 409 });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

**app/src/app/api/posts/[id]/route.ts** — 单篇文章接口

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getCache, setCache, deleteCache } from '@/lib/redis';

// GET /api/posts/:id
export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  const { id } = params;

  // 尝试缓存
  const cached = await getCache(`post:${id}`);
  if (cached) return NextResponse.json(cached);

  const result = await query('SELECT * FROM posts WHERE id = $1', [id]);
  if (result.rows.length === 0) {
    return NextResponse.json({ error: 'Post not found' }, { status: 404 });
  }

  // 增加浏览量（异步，不阻塞响应）
  query('UPDATE posts SET view_count = view_count + 1 WHERE id = $1', [id]);

  const post = result.rows[0];
  await setCache(`post:${id}`, post, 600);

  return NextResponse.json(post);
}

// PUT /api/posts/:id
export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  const { id } = params;
  const body = await request.json();
  const { title, content, excerpt, tags, status } = body;

  const result = await query(
    `UPDATE posts SET title = COALESCE($1, title), content = COALESCE($2, content),
     excerpt = COALESCE($3, excerpt), tags = COALESCE($4, tags), status = COALESCE($5, status),
     updated_at = CURRENT_TIMESTAMP
     WHERE id = $6 RETURNING *`,
    [title, content, excerpt, tags, status, id]
  );

  if (result.rows.length === 0) {
    return NextResponse.json({ error: 'Post not found' }, { status: 404 });
  }

  await deleteCache(`post:${id}`);
  await deleteCache('posts:*');

  return NextResponse.json(result.rows[0]);
}

// DELETE /api/posts/:id
export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  const { id } = params;
  const result = await query('DELETE FROM posts WHERE id = $1 RETURNING id', [id]);

  if (result.rows.length === 0) {
    return NextResponse.json({ error: 'Post not found' }, { status: 404 });
  }

  await deleteCache(`post:${id}`);
  await deleteCache('posts:*');

  return NextResponse.json({ message: 'Post deleted', id: parseInt(id) });
}
```

**app/src/app/page.tsx** — 首页

```tsx
export default async function Home() {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
  let posts: any[] = [];
  let error = '';

  try {
    const res = await fetch(`${baseUrl}/api/posts?status=published`, {
      next: { revalidate: 60 },
    });
    if (res.ok) {
      const data = await res.json();
      posts = data.posts || [];
    }
  } catch (e) {
    error = 'Failed to load posts';
  }

  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>📝 我的博客</h1>
      <p>基于 Docker Compose 部署的全栈博客系统</p>
      <hr />
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {posts.length === 0 ? (
        <p>暂无文章</p>
      ) : (
        posts.map((post: any) => (
          <article key={post.id} style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: 8 }}>
            <h2>{post.title}</h2>
            <p style={{ color: '#666' }}>{post.excerpt}</p>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: '#999' }}>
              <span>✍️ {post.author}</span>
              <span>📅 {new Date(post.created_at).toLocaleDateString('zh-CN')}</span>
              <span>👁️ {post.view_count} 次阅读</span>
            </div>
            <div style={{ marginTop: '0.5rem' }}>
              {(post.tags || []).map((tag: string) => (
                <span key={tag} style={{
                  background: '#e8f4f8', padding: '2px 8px', borderRadius: 4,
                  marginRight: 4, fontSize: '0.8rem',
                }}>
                  {tag}
                </span>
              ))}
            </div>
          </article>
        ))
      )}
    </main>
  );
}
```

**app/src/app/layout.tsx** — 布局

```tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '我的博客 - Docker Compose 实战',
  description: '使用 Docker Compose 部署的全栈博客系统',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body style={{ margin: 0, backgroundColor: '#fafafa' }}>
        {children}
      </body>
    </html>
  );
}
```

### Nginx 配置

**nginx/Dockerfile**

```dockerfile
FROM nginx:1.25-alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义配置
COPY conf.d/ /etc/nginx/conf.d/

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80
```

**nginx/conf.d/default.conf**

```nginx
# 限流配置
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

upstream nextjs_app {
    server app:3000;
    keepalive 32;
}

server {
    listen 80;
    server_name _;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Nginx 自身健康检查
    location /health {
        access_log off;
        return 200 'OK';
        add_header Content-Type text/plain;
    }

    # API 请求 - 限流
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://nextjs_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # 静态资源 - 长期缓存
    location /_next/static/ {
        proxy_pass http://nextjs_app;
        proxy_cache_valid 200 365d;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # 其他请求
    location / {
        proxy_pass http://nextjs_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### docker-compose.yml（完整版）

```yaml
# 博客系统 - Docker Compose 配置
# 使用方法: docker compose up -d

name: blog-system

services:
  # ========== 数据库 ==========
  postgres:
    image: postgres:16-alpine
    container_name: blog-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data   # 数据持久化
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # 初始化脚本
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - blog-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ========== 缓存 ==========
  redis:
    image: redis:7-alpine
    container_name: blog-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "${REDIS_PORT:-6379}:6379"
    networks:
      - blog-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 300M

  # ========== 应用 ==========
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
      target: production
      args:
        BUILD_DATE: ${BUILD_DATE:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}
    container_name: blog-app
    restart: unless-stopped
    environment:
      NODE_ENV: ${NODE_ENV:-production}
      PORT: 3000
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - blog-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 5
        window: 120s

  # ========== 反向代理 ==========
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: blog-nginx
    restart: unless-stopped
    ports:
      - "${NGINX_PORT:-80}:80"
      - "${NGINX_SSL_PORT:-443}:443"
    depends_on:
      - app
    networks:
      - blog-network
    deploy:
      resources:
        limits:
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"

# ========== 数据卷 ==========
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

# ========== 网络 ==========
networks:
  blog-network:
    driver: bridge
```

### 启动和使用

```bash
# 1. 进入项目目录
cd blog-system

# 2. 复制并编辑环境变量
cp .env.example .env
vim .env

# 3. 构建并启动（后台运行）
docker compose up -d --build

# 4. 查看运行状态
docker compose ps

# 5. 查看日志
docker compose logs -f app     # 跟踪应用日志
docker compose logs -f --tail=100  # 最近 100 行所有服务日志

# 6. 测试 API
# 获取文章列表
curl http://localhost/api/posts

# 创建文章
curl -X POST http://localhost/api/posts \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello World","content":"# Hello\n\n这是第一篇文章","status":"published","tags":["test"]}'

# 健康检查
curl http://localhost/api/health

# 7. 停止服务
docker compose down

# 8. 停止并删除数据卷（⚠️ 慎用！会删除所有数据）
docker compose down -v
```

---

## 实战项目 2：监控系统

### 技术栈

| 组件          | 用途               |
| ------------- | ------------------ |
| Prometheus    | 指标收集与存储     |
| Grafana       | 可视化仪表盘       |
| Node Exporter | 主机指标采集       |
| cAdvisor      | 容器指标采集       |
| Alertmanager  | 告警管理           |

### 项目结构

```
monitoring/
├── docker-compose.yml
├── .env
├── prometheus/
│   ├── prometheus.yml
│   ├── alert_rules.yml
│   └── targets/
│       └── node_targets.json
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml
│   │   └── dashboards/
│   │       ├── dashboard.yml
│   │       └── json/
│   │           └── node-exporter.json
│   └── grafana.ini
└── alertmanager/
    └── alertmanager.yml
```

### 环境变量 .env

```bash
# Grafana 管理员密码
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=Grafana-Admin-2024!

# 端口配置
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090
ALERTMANAGER_PORT=9093
NODE_EXPORTER_PORT=9100
CADVISOR_PORT=8080

# 数据路径
DATA_DIR=./data
```

### Prometheus 配置

**prometheus/prometheus.yml**

```yaml
# Prometheus 主配置文件
global:
  scrape_interval: 15s          # 全局采集间隔
  evaluation_interval: 15s       # 规则评估间隔
  scrape_timeout: 10s            # 采集超时

# 告警规则文件
rule_files:
  - "alert_rules.yml"

# Alertmanager 配置
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# 采集目标配置
scrape_configs:
  # 1. Prometheus 自身监控
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
        labels:
          instance: "prometheus-server"

  # 2. Node Exporter - 主机指标
  - job_name: "node-exporter"
    scrape_interval: 10s
    static_configs:
      - targets: ["node-exporter:9100"]
        labels:
          instance: "host-01"
    # 也可以使用文件发现
    # file_sd_configs:
    #   - files:
    #       - "targets/node_targets.json"
    #     refresh_interval: 30s

  # 3. cAdvisor - 容器指标
  - job_name: "cadvisor"
    scrape_interval: 10s
    static_configs:
      - targets: ["cadvisor:8080"]
        labels:
          instance: "host-01"

  # 4. Alertmanager 自身
  - job_name: "alertmanager"
    static_configs:
      - targets: ["alertmanager:9093"]

  # 5. Grafana
  - job_name: "grafana"
    static_configs:
      - targets: ["grafana:3000"]
```

**prometheus/alert_rules.yml**

```yaml
groups:
  - name: host_alerts
    rules:
      # CPU 使用率过高
      - alert: HighCpuUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高 (实例: {{ $labels.instance }})"
          description: "CPU 使用率已超过 80%，当前值: {{ $value | printf \"%.1f\" }}%"

      # 内存使用率过高
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高 (实例: {{ $labels.instance }})"
          description: "内存使用率已超过 85%，当前值: {{ $value | printf \"%.1f\" }}%"

      # 磁盘空间不足
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足 (实例: {{ $labels.instance }})"
          description: "根分区剩余空间不足 15%，当前剩余: {{ $value | printf \"%.1f\" }}%"

      # 实例宕机
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "实例宕机: {{ $labels.instance }}"
          description: "{{ $labels.job }} 的 {{ $labels.instance }} 已宕机超过 1 分钟"

  - name: container_alerts
    rules:
      # 容器重启过于频繁
      - alert: ContainerRestartingTooMuch
        expr: increase(container_restart_count[1h]) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "容器频繁重启: {{ $labels.name }}"
          description: "容器 {{ $labels.name }} 在过去 1 小时内重启了 {{ $value }} 次"
```

**prometheus/targets/node_targets.json**

```json
[
  {
    "targets": ["node-exporter:9100"],
    "labels": {
      "instance": "host-01",
      "env": "production",
      "region": "cn-east"
    }
  }
]
```

### Grafana 配置

**grafana/provisioning/datasources/prometheus.yml**

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
```

**grafana/provisioning/dashboards/dashboard.yml**

```yaml
apiVersion: 1

providers:
  - name: "Default"
    orgId: 1
    folder: "Docker Monitor"
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards/json
      foldersFromFilesStructure: false
```

**grafana/provisioning/dashboards/json/node-exporter.json**（简化版仪表盘）

```json
{
  "annotations": { "list": [] },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 1,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "title": "CPU 使用率",
      "type": "gauge",
      "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
      "datasource": { "type": "prometheus", "uid": "PBFA97CFB590B2093" },
      "targets": [
        {
          "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
          "legendFormat": "CPU"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "min": 0,
          "max": 100,
          "thresholds": {
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 60 },
              { "color": "red", "value": 80 }
            ]
          }
        }
      }
    },
    {
      "title": "内存使用率",
      "type": "gauge",
      "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
      "datasource": { "type": "prometheus", "uid": "PBFA97CFB590B2093" },
      "targets": [
        {
          "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
          "legendFormat": "Memory"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "min": 0,
          "max": 100,
          "thresholds": {
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 70 },
              { "color": "red", "value": 85 }
            ]
          }
        }
      }
    },
    {
      "title": "磁盘使用率",
      "type": "gauge",
      "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
      "datasource": { "type": "prometheus", "uid": "PBFA97CFB590B2093" },
      "targets": [
        {
          "expr": "(1 - (node_filesystem_avail_bytes{mountpoint=\"/\"} / node_filesystem_size_bytes{mountpoint=\"/\"})) * 100",
          "legendFormat": "Disk"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "min": 0,
          "max": 100,
          "thresholds": {
            "steps": [
              { "color": "green", "value": null },
              { "color": "yellow", "value": 70 },
              { "color": "red", "value": 85 }
            ]
          }
        }
      }
    },
    {
      "title": "CPU 使用趋势",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 8 },
      "datasource": { "type": "prometheus", "uid": "PBFA97CFB590B2093" },
      "targets": [
        {
          "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
          "legendFormat": "{{ instance }}"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "custom": { "fillOpacity": 20, "lineWidth": 2 }
        }
      }
    },
    {
      "title": "内存使用趋势",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 16 },
      "datasource": { "type": "prometheus", "uid": "PBFA97CFB590B2093" },
      "targets": [
        {
          "expr": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes",
          "legendFormat": "已用内存"
        },
        {
          "expr": "node_memory_MemTotal_bytes",
          "legendFormat": "总内存"
        }
      ],
      "fieldConfig": {
        "defaults": { "unit": "bytes" }
      }
    },
    {
      "title": "网络流量",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 16 },
      "datasource": { "type": "prometheus", "uid": "PBFA97CFB590B2093" },
      "targets": [
        {
          "expr": "rate(node_network_receive_bytes_total{device!=\"lo\"}[5m])",
          "legendFormat": "{{ device }} 接收"
        },
        {
          "expr": "rate(node_network_transmit_bytes_total{device!=\"lo\"}[5m])",
          "legendFormat": "{{ device }} 发送"
        }
      ],
      "fieldConfig": {
        "defaults": { "unit": "Bps", "custom": { "fillOpacity": 10 } }
      }
    }
  ],
  "refresh": "30s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": ["node-exporter", "docker"],
  "templating": { "list": [] },
  "time": { "from": "now-1h", "to": "now" },
  "title": "Node Exporter 监控",
  "uid": "node-exporter-overview",
  "version": 1
}
```

### Alertmanager 配置

**alertmanager/alertmanager.yml**

```yaml
global:
  resolve_timeout: 5m

# 告警路由
route:
  group_by: ['alertname', 'instance']
  group_wait: 30s           # 等待 30s 聚合同组告警
  group_interval: 5m        # 同组告警发送间隔
  repeat_interval: 4h       # 重复告警间隔
  receiver: 'default-receiver'
  
  routes:
    - match:
        severity: critical
      receiver: 'critical-receiver'
      group_wait: 10s
      repeat_interval: 1h
    
    - match:
        severity: warning
      receiver: 'warning-receiver'
      repeat_interval: 4h

# 接收器配置
receivers:
  - name: 'default-receiver'
    webhook_configs:
      - url: 'http://host.docker.internal:5001/webhook/alert'
        send_resolved: true

  - name: 'critical-receiver'
    webhook_configs:
      - url: 'http://host.docker.internal:5001/webhook/alert'
        send_resolved: true
    # 如果配置了邮件:
    # email_configs:
    #   - to: 'admin@example.com'
    #     from: 'alertmanager@example.com'
    #     smarthost: 'smtp.example.com:587'
    #     auth_username: 'alertmanager@example.com'
    #     auth_password: 'smtp-password'

  - name: 'warning-receiver'
    webhook_configs:
      - url: 'http://host.docker.internal:5001/webhook/alert'
        send_resolved: true

# 抑制规则
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

### docker-compose.yml

```yaml
# 监控系统 - Docker Compose 配置
name: monitoring

services:
  # ========== Prometheus ==========
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    restart: unless-stopped
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=30d"        # 数据保留 30 天
      - "--storage.tsdb.retention.size=10GB"        # 最大存储 10GB
      - "--web.console.libraries=/usr/share/prometheus/console_libraries"
      - "--web.console.templates=/usr/share/prometheus/consoles"
      - "--web.enable-lifecycle"                    # 支持热重载
      - "--web.enable-admin-api"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    networks:
      - monitoring-net
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 15s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  # ========== Grafana ==========
  grafana:
    image: grafana/grafana:10.2.0
    container_name: grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_USER: ${GF_SECURITY_ADMIN_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GF_SECURITY_ADMIN_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_SERVER_ROOT_URL: "http://localhost:${GRAFANA_PORT:-3000}"
      GF_INSTALL_PLUGINS: ""  # 可在此添加插件
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    networks:
      - monitoring-net
    depends_on:
      prometheus:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 15s
      timeout: 10s
      retries: 3

  # ========== Node Exporter ==========
  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: node-exporter
    restart: unless-stopped
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--path.rootfs=/rootfs"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "${NODE_EXPORTER_PORT:-9100}:9100"
    networks:
      - monitoring-net
    pid: host
    deploy:
      resources:
        limits:
          memory: 128M

  # ========== cAdvisor ==========
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.2
    container_name: cadvisor
    restart: unless-stopped
    privileged: true
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "${CADVISOR_PORT:-8080}:8080"
    networks:
      - monitoring-net
    devices:
      - /dev/kmsg
    deploy:
      resources:
        limits:
          memory: 256M

  # ========== Alertmanager ==========
  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: alertmanager
    restart: unless-stopped
    command:
      - "--config.file=/etc/alertmanager/alertmanager.yml"
      - "--storage.path=/alertmanager"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    ports:
      - "${ALERTMANAGER_PORT:-9093}:9093"
    networks:
      - monitoring-net
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9093/-/healthy"]
      interval: 15s
      timeout: 10s
      retries: 3

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  monitoring-net:
    driver: bridge
```

### 启动和使用

```bash
# 进入项目目录
cd monitoring

# 启动所有服务
docker compose up -d

# 查看状态
docker compose ps

# 访问地址
# Prometheus:   http://localhost:9090
# Grafana:      http://localhost:3000  (admin / Grafana-Admin-2024!)
# Node Exporter: http://localhost:9100/metrics
# cAdvisor:     http://localhost:8080
# Alertmanager: http://localhost:9093

# 在 Grafana 中导入更多仪表盘
# 推荐 Dashboard ID:
#   - 1860  (Node Exporter Full)
#   - 893   (Docker & System Monitoring)
#   - 14282 (Cadvisor Exporter)

# 热重载 Prometheus 配置（无需重启）
curl -X POST http://localhost:9090/-/reload
```

---

## 实战项目 3：微服务网关

### 技术栈

| 组件          | 用途                 |
| ------------- | -------------------- |
| User Service  | 用户服务 (Python)    |
| Order Service | 订单服务 (Python)    |
| Product Service| 商品服务 (Python)   |
| Nginx         | API 网关 + 负载均衡  |
| Redis         | 共享缓存 / 会话存储  |

### 项目结构

```
microservices/
├── docker-compose.yml
├── .env
├── shared/
│   └── requirements.txt
├── user-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── order-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── product-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
└── gateway/
    ├── Dockerfile
    └── nginx.conf
```

### 共享依赖 shared/requirements.txt

```
flask==3.0.0
gunicorn==21.2.0
redis==5.0.1
requests==2.31.0
psutil==5.9.6
```

### User Service

**user-service/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--threads", "4", "--timeout", "30", "app:app"]
```

**user-service/requirements.txt**

```
flask==3.0.0
gunicorn==21.2.0
redis==5.0.1
```

**user-service/app.py**

```python
"""用户服务 - 管理用户信息"""

import os
import time
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
import redis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('user-service')

app = Flask(__name__)

# Redis 连接
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', ''),
    decode_responses=True,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)

# 模拟用户数据
USERS_DB = {
    "u001": {"id": "u001", "name": "张三", "email": "zhangsan@example.com", "role": "admin", "created_at": "2024-01-15"},
    "u002": {"id": "u002", "name": "李四", "email": "lisi@example.com", "role": "user", "created_at": "2024-02-20"},
    "u003": {"id": "u003", "name": "王五", "email": "wangwu@example.com", "role": "user", "created_at": "2024-03-10"},
}

SERVICE_NAME = "user-service"
SERVICE_VERSION = "1.0.0"
start_time = time.time()


@app.route('/health')
def health():
    """健康检查"""
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        pass

    status = "healthy" if redis_ok else "degraded"
    return jsonify({
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": status,
        "uptime": round(time.time() - start_time, 2),
        "checks": {
            "redis": "ok" if redis_ok else "error",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }), 200 if redis_ok else 503


@app.route('/api/users', methods=['GET'])
def list_users():
    """获取用户列表（支持缓存）"""
    # 尝试从缓存读取
    cache_key = "users:list"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info("Cache hit for user list")
            return jsonify({"data": json.loads(cached), "source": "cache"})
    except Exception:
        pass

    users = list(USERS_DB.values())

    # 写入缓存（60 秒）
    try:
        redis_client.setex(cache_key, 60, json.dumps(users))
    except Exception:
        pass

    return jsonify({"data": users, "source": "database"})


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id: str):
    """获取单个用户"""
    # 缓存
    cache_key = f"users:{user_id}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify({"data": json.loads(cached), "source": "cache"})
    except Exception:
        pass

    user = USERS_DB.get(user_id)
    if not user:
        return jsonify({"error": "User not found", "code": 404}), 404

    try:
        redis_client.setex(cache_key, 120, json.dumps(user))
    except Exception:
        pass

    return jsonify({"data": user, "source": "database"})


@app.route('/api/users', methods=['POST'])
def create_user():
    """创建用户"""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({"error": "name and email are required"}), 400

    user_id = f"u{uuid.uuid4().hex[:6]}"
    user = {
        "id": user_id,
        "name": data['name'],
        "email": data['email'],
        "role": data.get('role', 'user'),
        "created_at": datetime.utcnow().strftime('%Y-%m-%d'),
    }
    USERS_DB[user_id] = user

    # 清除列表缓存
    try:
        redis_client.delete("users:list")
    except Exception:
        pass

    logger.info(f"Created user: {user_id} ({user['name']})")
    return jsonify({"data": user}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=os.getenv('FLASK_DEBUG', '0') == '1')
```

### Order Service

**order-service/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5002/health')" || exit 1

EXPOSE 5002

CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "2", "--threads", "4", "--timeout", "30", "app:app"]
```

**order-service/requirements.txt**

```
flask==3.0.0
gunicorn==21.2.0
redis==5.0.1
requests==2.31.0
```

**order-service/app.py**

```python
"""订单服务 - 管理订单"""

import os
import time
import uuid
import json
import logging
import requests
from datetime import datetime
from flask import Flask, jsonify, request
import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('order-service')

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', ''),
    decode_responses=True,
)

# 服务发现：通过环境变量获取其他服务地址
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5001')
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:5003')

ORDERS_DB = {}

SERVICE_NAME = "order-service"
SERVICE_VERSION = "1.0.0"
start_time = time.time()


def call_service(url: str, timeout: int = 5) -> dict | None:
    """调用其他微服务（带重试）"""
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Service call failed (attempt {attempt + 1}): {url} - {e}")
            time.sleep(0.5 * (attempt + 1))
    return None


@app.route('/health')
def health():
    # 检查依赖服务
    checks = {"redis": "error", "user-service": "error", "product-service": "error"}

    try:
        checks["redis"] = "ok" if redis_client.ping() else "error"
    except Exception:
        pass

    try:
        resp = requests.get(f"{USER_SERVICE_URL}/health", timeout=3)
        checks["user-service"] = "ok" if resp.status_code == 200 else "error"
    except Exception:
        pass

    try:
        resp = requests.get(f"{PRODUCT_SERVICE_URL}/health", timeout=3)
        checks["product-service"] = "ok" if resp.status_code == 200 else "error"
    except Exception:
        pass

    all_ok = all(v == "ok" for v in checks.values())
    return jsonify({
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "healthy" if all_ok else "degraded",
        "uptime": round(time.time() - start_time, 2),
        "checks": checks,
    }), 200 if all_ok else 503


@app.route('/api/orders', methods=['GET'])
def list_orders():
    """获取订单列表"""
    user_id = request.args.get('user_id')
    orders = list(ORDERS_DB.values())
    if user_id:
        orders = [o for o in orders if o['user_id'] == user_id]
    return jsonify({"data": orders, "total": len(orders)})


@app.route('/api/orders', methods=['POST'])
def create_order():
    """创建订单"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id are required"}), 400

    # 验证用户存在
    user_resp = call_service(f"{USER_SERVICE_URL}/api/users/{user_id}")
    if not user_resp or 'error' in user_resp:
        return jsonify({"error": "User not found or user service unavailable"}), 400

    # 获取商品信息
    product_resp = call_service(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}")
    if not product_resp or 'error' in product_resp:
        return jsonify({"error": "Product not found or product service unavailable"}), 400

    product = product_resp.get('data', {})
    total_price = product.get('price', 0) * quantity

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    order = {
        "id": order_id,
        "user_id": user_id,
        "user_name": user_resp.get('data', {}).get('name', 'Unknown'),
        "product_id": product_id,
        "product_name": product.get('name', 'Unknown'),
        "quantity": quantity,
        "unit_price": product.get('price', 0),
        "total_price": total_price,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    ORDERS_DB[order_id] = order

    logger.info(f"Order created: {order_id} by {user_id}, total: ¥{total_price}")
    return jsonify({"data": order}), 201


@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id: str):
    """获取订单详情"""
    order = ORDERS_DB.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"data": order})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=os.getenv('FLASK_DEBUG', '0') == '1')
```

### Product Service

**product-service/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5003/health')" || exit 1

EXPOSE 5003

CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers", "2", "--threads", "4", "--timeout", "30", "app:app"]
```

**product-service/requirements.txt**

```
flask==3.0.0
gunicorn==21.2.0
redis==5.0.1
```

**product-service/app.py**

```python
"""商品服务 - 管理商品信息"""

import os
import time
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('product-service')

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', ''),
    decode_responses=True,
)

PRODUCTS_DB = {
    "p001": {"id": "p001", "name": "Docker 实战指南", "price": 89.00, "stock": 100, "category": "books"},
    "p002": {"id": "p002", "name": "Kubernetes 权威教程", "price": 129.00, "stock": 50, "category": "books"},
    "p003": {"id": "p003", "name": "机械键盘", "price": 599.00, "stock": 30, "category": "electronics"},
    "p004": {"id": "p004", "name": "显示器支架", "price": 199.00, "stock": 200, "category": "accessories"},
    "p005": {"id": "p005", "name": "USB-C 扩展坞", "price": 349.00, "stock": 80, "category": "electronics"},
}

SERVICE_NAME = "product-service"
SERVICE_VERSION = "1.0.0"
start_time = time.time()


@app.route('/health')
def health():
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        pass
    return jsonify({
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "healthy" if redis_ok else "degraded",
        "uptime": round(time.time() - start_time, 2),
        "checks": {"redis": "ok" if redis_ok else "error"},
    }), 200 if redis_ok else 503


@app.route('/api/products', methods=['GET'])
def list_products():
    """获取商品列表"""
    category = request.args.get('category')
    cache_key = f"products:list:{category or 'all'}"

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify({"data": json.loads(cached), "source": "cache"})
    except Exception:
        pass

    products = list(PRODUCTS_DB.values())
    if category:
        products = [p for p in products if p['category'] == category]

    try:
        redis_client.setex(cache_key, 120, json.dumps(products))
    except Exception:
        pass

    return jsonify({"data": products, "source": "database"})


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id: str):
    """获取单个商品"""
    cache_key = f"products:{product_id}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify({"data": json.loads(cached), "source": "cache"})
    except Exception:
        pass

    product = PRODUCTS_DB.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        redis_client.setex(cache_key, 120, json.dumps(product))
    except Exception:
        pass

    return jsonify({"data": product, "source": "database"})


@app.route('/api/products', methods=['POST'])
def create_product():
    """创建商品"""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('price'):
        return jsonify({"error": "name and price are required"}), 400

    product_id = f"p{uuid.uuid4().hex[:6]}"
    product = {
        "id": product_id,
        "name": data['name'],
        "price": float(data['price']),
        "stock": int(data.get('stock', 0)),
        "category": data.get('category', 'general'),
    }
    PRODUCTS_DB[product_id] = product

    try:
        redis_client.delete("products:list:all")
    except Exception:
        pass

    logger.info(f"Product created: {product_id} ({product['name']})")
    return jsonify({"data": product}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=os.getenv('FLASK_DEBUG', '0') == '1')
```

### Nginx 网关

**gateway/Dockerfile**

```dockerfile
FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80
```

**gateway/nginx.conf**

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/json;

    log_format gateway '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       'upstream=$upstream_addr '
                       'response_time=$upstream_response_time '
                       'request_time=$request_time';

    access_log /var/log/nginx/access.log gateway;

    sendfile on;
    keepalive_timeout 65;

    # 请求限流
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;

    # ========== 上游服务定义（负载均衡） ==========
    upstream user_service {
        least_conn;                    # 最少连接算法
        server user-service:5001;
        keepalive 16;
    }

    upstream order_service {
        least_conn;
        server order-service:5002;
        keepalive 16;
    }

    upstream product_service {
        least_conn;
        server product-service:5003;
        keepalive 16;
    }

    server {
        listen 80;
        server_name _;

        # 全局限流
        limit_req zone=api_limit burst=50 nodelay;

        # ========== 网关健康检查 ==========
        location /health {
            access_log off;
            return 200 '{"status":"healthy","service":"api-gateway"}';
            add_header Content-Type application/json;
        }

        # ========== 服务状态总览 ==========
        location /api/status {
            default_type application/json;
            content_by_lua_block {
                -- 简单的状态页面（如果需要，可以使用 Lua 扩展）
            }
            # 作为替代方案，直接代理到一个服务
            proxy_pass http://user_service/health;
        }

        # ========== 路由规则 ==========

        # 用户服务: /api/users/**
        location /api/users {
            proxy_pass http://user_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;
            proxy_http_version 1.1;
            proxy_set_header Connection "";

            # 超时设置
            proxy_connect_timeout 5s;
            proxy_read_timeout 30s;
            proxy_send_timeout 30s;

            # 错误处理
            proxy_next_upstream error timeout http_502 http_503;
            proxy_next_upstream_tries 2;
        }

        # 订单服务: /api/orders/**
        location /api/orders {
            proxy_pass http://order_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;
            proxy_http_version 1.1;
            proxy_set_header Connection "";

            proxy_connect_timeout 5s;
            proxy_read_timeout 30s;
            proxy_send_timeout 30s;

            proxy_next_upstream error timeout http_502 http_503;
            proxy_next_upstream_tries 2;
        }

        # 商品服务: /api/products/**
        location /api/products {
            proxy_pass http://product_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;
            proxy_http_version 1.1;
            proxy_set_header Connection "";

            proxy_connect_timeout 5s;
            proxy_read_timeout 30s;
            proxy_send_timeout 30s;

            proxy_next_upstream error timeout http_502 http_503;
            proxy_next_upstream_tries 2;
        }

        # 默认路由
        location / {
            return 404 '{"error":"Route not found","hint":"Available: /api/users, /api/orders, /api/products, /health"}';
            add_header Content-Type application/json;
        }
    }
}
```

### docker-compose.yml

```yaml
# 微服务网关 - Docker Compose 配置
name: microservices

services:
  # ========== 共享缓存 ==========
  redis:
    image: redis:7-alpine
    container_name: ms-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:-micro-redis-2024} --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - ms-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-micro-redis-2024}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ========== 用户服务 ==========
  user-service:
    build:
      context: ./user-service
    container_name: user-service
    restart: unless-stopped
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD:-micro-redis-2024}
      FLASK_DEBUG: "0"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - ms-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

  # ========== 订单服务 ==========
  order-service:
    build:
      context: ./order-service
    container_name: order-service
    restart: unless-stopped
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD:-micro-redis-2024}
      USER_SERVICE_URL: http://user-service:5001
      PRODUCT_SERVICE_URL: http://product-service:5003
      FLASK_DEBUG: "0"
    depends_on:
      redis:
        condition: service_healthy
      user-service:
        condition: service_started
      product-service:
        condition: service_started
    networks:
      - ms-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

  # ========== 商品服务 ==========
  product-service:
    build:
      context: ./product-service
    container_name: product-service
    restart: unless-stopped
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD:-micro-redis-2024}
      FLASK_DEBUG: "0"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - ms-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

  # ========== API 网关 ==========
  gateway:
    build:
      context: ./gateway
    container_name: ms-gateway
    restart: unless-stopped
    ports:
      - "${GATEWAY_PORT:-8080}:80"
    depends_on:
      - user-service
      - order-service
      - product-service
    networks:
      - ms-network
    deploy:
      resources:
        limits:
          memory: 128M

volumes:
  redis_data:

networks:
  ms-network:
    driver: bridge
```

### 启动和使用

```bash
# 启动
cd microservices
docker compose up -d --build

# 查看所有服务
docker compose ps

# ========== API 测试 ==========

# 通过网关访问用户服务
curl http://localhost:8080/api/users
curl http://localhost:8080/api/users/u001

# 获取商品列表
curl http://localhost:8080/api/products
curl http://localhost:8080/api/products?category=books

# 创建订单（会调用用户服务和商品服务做验证）
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u001", "product_id": "p001", "quantity": 2}'

# 查看订单
curl http://localhost:8080/api/orders

# 网关健康检查
curl http://localhost:8080/health

# 直接访问某个服务（绕过网关，用于调试）
curl http://localhost:8080/api/users/u001

# 查看服务日志
docker compose logs -f order-service
```

---

## Compose 高级特性

### 多环境配置（dev / staging / prod）

通过**多个 Compose 文件叠加**实现环境差异化。

**docker-compose.yml** — 基础配置（所有环境共享）

```yaml
name: myapp

services:
  app:
    image: myapp:${APP_VERSION:-latest}
    environment:
      - APP_ENV
      - DATABASE_URL
    networks:
      - app-net

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-app}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-appdb}
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - app-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-app}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  db_data:

networks:
  app-net:
```

**docker-compose.dev.yml** — 开发环境

```yaml
# 开发环境：热重载、调试端口、暴露所有服务端口
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./src:/app/src              # 代码挂载，支持热重载
      - /app/node_modules           # 排除 node_modules
    environment:
      APP_ENV: development
      FLASK_DEBUG: "1"
      LOG_LEVEL: debug
    ports:
      - "3000:3000"
      - "9229:9229"                 # Node.js 调试端口
    command: npm run dev

  db:
    ports:
      - "5432:5432"                 # 开发环境暴露数据库端口

  # 开发专用工具
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    networks:
      - app-net

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"                 # SMTP
      - "8025:8025"                 # Web UI
    networks:
      - app-net
```

**docker-compose.staging.yml** — 预发布环境

```yaml
services:
  app:
    environment:
      APP_ENV: staging
      LOG_LEVEL: info
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '1.0'

  db:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # 从 CI/CD 注入
    deploy:
      resources:
        limits:
          memory: 512M
```

**docker-compose.prod.yml** — 生产环境

```yaml
services:
  app:
    environment:
      APP_ENV: production
      LOG_LEVEL: warning
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 5
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"

  db:
    ports: []                        # 生产环境不暴露端口
    deploy:
      resources:
        limits:
          memory: 2G
```

**环境专属 .env 文件**

```bash
# .env.dev
APP_VERSION=latest
DB_USER=devuser
DB_PASSWORD=devpassword123
DB_NAME=devdb

# .env.staging
APP_VERSION=1.2.0-rc1
DB_USER=staginguser
DB_PASSWORD=${STAGING_DB_PASSWORD}   # 从 CI/CD 注入

# .env.prod
APP_VERSION=1.2.0
DB_USER=produser
DB_PASSWORD=${PROD_DB_PASSWORD}      # 从密钥管理服务注入
```

**使用方法**

```bash
# 开发环境：基础 + 开发覆盖
docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d

# 预发布环境
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up -d

# 生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

# 简化方式：使用环境变量 COMPOSE_FILE
export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
export COMPOSE_ENV_FILE=.env.dev
docker compose up -d
```

### Profiles — 按需启动服务

```yaml
services:
  # 核心服务（始终启动）
  app:
    image: myapp:latest
    ports: ["3000:3000"]

  db:
    image: postgres:16-alpine

  redis:
    image: redis:7-alpine

  # 开发调试工具（仅 dev profile 启动）
  debug-tools:
    image: busybox
    profiles: ["dev"]
    command: sh -c "while true; do echo 'debug tool running'; sleep 60; done"

  # 仅在 debug profile 启动
  mailhog:
    image: mailhog/mailhog
    profiles: ["dev", "debug"]
    ports: ["1025:1025", "8025:8025"]

  # 仅在 test profile 启动
  selenium:
    image: selenium/standalone-chrome
    profiles: ["test"]
    ports: ["4444:4444"]

  # 监控（仅 monitoring profile）
  prometheus:
    image: prom/prometheus
    profiles: ["monitoring", "prod"]
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana
    profiles: ["monitoring", "prod"]
    ports: ["3001:3000"]
```

```bash
# 默认只启动无 profile 的核心服务
docker compose up -d

# 启动核心服务 + 开发工具
docker compose --profile dev up -d

# 启动核心服务 + 测试工具
docker compose --profile test up -d

# 启动所有
docker compose --profile dev --profile monitoring up -d

# 查看哪些服务属于哪个 profile
docker compose config --profiles
```

### extends — 服务配置复用

```yaml
# docker-compose.yml
services:
  # 基础服务模板（不会被实际创建，因为没有 image 或 build）
  base-service:
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - app-net

  # 继承基础配置
  web:
    extends:
      service: base-service
    image: nginx:alpine
    ports: ["80:80"]

  api:
    extends:
      service: base-service
    image: myapi:latest
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL

  worker:
    extends:
      service: base-service
    image: myworker:latest
    command: python worker.py

networks:
  app-net:
```

### 健康检查详解

```yaml
services:
  # PostgreSQL 健康检查
  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s        # 检查间隔
      timeout: 5s          # 超时时间
      retries: 5           # 重试次数
      start_period: 30s    # 启动宽限期（此期间失败不计入 retries）

  # Redis 健康检查
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass mypassword
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "mypassword", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # HTTP 服务健康检查
  api:
    image: myapi:latest
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 15s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 自定义脚本健康检查
  worker:
    image: myworker:latest
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import requests; r=requests.get('http://localhost:8080/health'); exit(0 if r.status_code==200 else 1)\""]
      interval: 30s
      timeout: 10s
      retries: 3

  # 依赖健康检查的启动顺序
  dashboard:
    image: mydashboard:latest
    depends_on:
      api:
        condition: service_healthy    # 等待 api 健康后才启动
      db:
        condition: service_healthy
      redis:
        condition: service_started    # 只要启动了就行（不要求健康）
```

### 优雅关闭

```yaml
services:
  app:
    image: myapp:latest
    # 默认 stop_grace_period: 10s
    # 也可以自定义：
    stop_grace_period: 30s
    stop_signal: SIGTERM
    # 应用中处理 SIGTERM 信号：
    #   - 停止接收新请求
    #   - 完成正在处理的请求
    #   - 关闭数据库连接
    #   - 退出

  # Node.js 应用示例
  node-app:
    image: mynodeapp:latest
    stop_grace_period: 15s
    stop_signal: SIGTERM
    # 在应用中：
    # process.on('SIGTERM', async () => {
    #   server.close();
    #   await db.end();
    #   process.exit(0);
    # });

  # Python 应用示例
  python-app:
    image: mypythonapp:latest
    stop_grace_period: 20s
    # gunicorn 默认会处理 SIGTERM
    # flask 开发服务器可能不会，生产环境务必使用 gunicorn
```

---

## 最佳实践

### 环境变量管理

```yaml
# 推荐的环境变量管理方式

services:
  app:
    image: myapp:latest

    # ✅ 方式 1：使用 .env 文件（自动加载）
    # .env 文件在项目根目录，Compose 自动读取

    # ✅ 方式 2：显式指定 env_file
    env_file:
      - .env                       # 默认环境变量
      - .env.local                 # 本地覆盖（加入 .gitignore）

    # ✅ 方式 3：environment 显式定义（优先级最高）
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      # 使用 ${VAR:-default} 设置默认值
      LOG_LEVEL: ${LOG_LEVEL:-info}

    # ✅ 方式 4：从文件读取单个变量（适合密码）
    secrets:
      db_password:
        file: ./secrets/db_password.txt

# Docker secrets（Swarm 模式下更安全）
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

**敏感信息管理最佳实践**

```bash
# .gitignore 中必须排除的文件
.env
.env.local
.env.*.local
secrets/
```

### 数据备份脚本

**scripts/backup.sh**

```bash
#!/bin/bash
# 数据库备份脚本

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAX_BACKUPS=${MAX_BACKUPS:-7}    # 保留最近 7 天的备份

# PostgreSQL 备份
backup_postgres() {
    local container="$1"
    local db_user="$2"
    local db_name="$3"
    local backup_file="${BACKUP_DIR}/postgres_${db_name}_${TIMESTAMP}.sql.gz"

    echo "[$(date)] Backing up PostgreSQL: ${db_name}..."
    
    docker compose exec -T "$container" \
        pg_dump -U "$db_user" -d "$db_name" --clean --if-exists \
        | gzip > "$backup_file"

    local size=$(du -h "$backup_file" | cut -f1)
    echo "[$(date)] Backup saved: ${backup_file} (${size})"
}

# Redis 备份
backup_redis() {
    local container="$1"
    local password="$2"
    local backup_file="${BACKUP_DIR}/redis_${TIMESTAMP}.rdb"

    echo "[$(date)] Backing up Redis..."

    docker compose exec -T "$container" redis-cli -a "$password" BGSAVE
    sleep 2
    docker compose exec -T "$container" cat /data/dump.rdb > "$backup_file"
    
    local size=$(du -h "$backup_file" | cut -f1)
    echo "[$(date)] Backup saved: ${backup_file} (${size})"
}

# 清理旧备份
cleanup_old_backups() {
    echo "[$(date)] Cleaning up backups older than ${MAX_BACKUPS} days..."
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$MAX_BACKUPS" -delete
    find "$BACKUP_DIR" -name "*.rdb" -mtime +"$MAX_BACKUPS" -delete
    echo "[$(date)] Cleanup complete."
}

# 主流程
main() {
    mkdir -p "$BACKUP_DIR"

    echo "========================================="
    echo "  Docker 数据备份 - $(date)"
    echo "========================================="

    # 从 .env 读取配置
    source .env 2>/dev/null || true

    backup_postgres "postgres" "${POSTGRES_USER:-bloguser}" "${POSTGRES_DB:-blogdb}"
    backup_redis "redis" "${REDIS_PASSWORD:-}"
    cleanup_old_backups

    echo "========================================="
    echo "  备份完成！"
    echo "  备份目录: ${BACKUP_DIR}"
    echo "  备份文件数: $(ls -1 "${BACKUP_DIR}" | wc -l)"
    echo "========================================="
}

main "$@"
```

**scripts/restore.sh**

```bash
#!/bin/bash
# 数据库恢复脚本

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"

# 列出可用备份
list_backups() {
    echo "可用备份文件："
    echo "-------------"
    ls -lhtr "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "没有找到 PostgreSQL 备份"
    echo ""
    ls -lhtr "$BACKUP_DIR"/*.rdb 2>/dev/null || echo "没有找到 Redis 备份"
}

# 恢复 PostgreSQL
restore_postgres() {
    local backup_file="$1"
    local container="${2:-postgres}"
    local db_user="${3:-${POSTGRES_USER:-bloguser}}"
    local db_name="${4:-${POSTGRES_DB:-blogdb}}"

    if [ ! -f "$backup_file" ]; then
        echo "错误：备份文件不存在: $backup_file"
        exit 1
    fi

    echo "⚠️  即将恢复数据库 ${db_name}，现有数据将被覆盖！"
    read -p "确认继续？(y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "已取消"
        exit 0
    fi

    echo "[$(date)] Restoring PostgreSQL from: ${backup_file}..."
    gunzip -c "$backup_file" | docker compose exec -T "$container" psql -U "$db_user" -d "$db_name"
    echo "[$(date)] Restore complete!"
}

# 主流程
if [ $# -eq 0 ]; then
    list_backups
    echo ""
    echo "用法: $0 <backup_file.sql.gz>"
    exit 0
fi

source .env 2>/dev/null || true
restore_postgres "$1"
```

### 日志管理

```yaml
# 生产级日志配置
services:
  app:
    image: myapp:latest
    logging:
      driver: "json-file"
      options:
        max-size: "50m"       # 单个日志文件最大 50MB
        max-file: "5"         # 最多保留 5 个文件（总计 250MB）
        compress: "true"      # 压缩轮转的日志
    # 环境变量控制日志级别
    environment:
      LOG_LEVEL: ${LOG_LEVEL:-info}    # debug|info|warn|error
      LOG_FORMAT: json                  # json 格式便于解析

  # 集中式日志收集（可选）
  # 使用 Loki + Promtail
  loki:
    image: grafana/loki:2.9.0
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki_data:/loki
    networks:
      - monitoring-net

  promtail:
    image: grafana/promtail:2.9.0
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
    networks:
      - monitoring-net
```

### 综合监控方案

```yaml
# 在生产项目中集成监控
services:
  app:
    image: myapp:latest
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=3000"
      - "prometheus.path=/metrics"

  # 定期健康检查 + 自动重启
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

### 生产环境 Checklist

```
✅ 环境变量
   □ 所有密码已更换默认值
   □ .env 文件已加入 .gitignore
   □ 敏感信息使用 Docker Secrets 或密钥管理服务

✅ 数据持久化
   □ 所有数据库使用命名卷
   □ 已设置定期备份脚本
   □ 已测试恢复流程

✅ 安全
   □ 服务不暴露不必要的端口
   □ 使用非 root 用户运行容器
   □ 已设置资源限制（memory/cpus）
   □ 已配置网络隔离

✅ 可靠性
   □ 所有服务已配置 healthcheck
   □ 服务间使用 depends_on + condition
   □ 已配置 restart: unless-stopped
   □ 已设置优雅关闭（stop_grace_period）

✅ 可观测性
   □ 日志使用 JSON 格式
   □ 已配置日志轮转（max-size + max-file）
   □ 已集成监控系统
   □ 已配置告警规则

✅ 性能
   □ 镜像使用多阶段构建
   □ 使用 alpine 基础镜像
   □ 合理设置缓存策略
   □ 已配置负载均衡
```

---

> **下一步：** 有了这些实战基础后，可以继续学习 [07-Docker安全最佳实践.md](./07-Docker安全最佳实践.md) 了解如何加固容器安全。
