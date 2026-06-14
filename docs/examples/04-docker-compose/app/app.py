"""
Flask + Redis 访问计数器
演示 Docker Compose 编排多服务应用
"""
import os
import time
import socket
from flask import Flask, jsonify, render_template_string
import redis

app = Flask(__name__)

# Redis 连接
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

def get_redis():
    """获取 Redis 连接，带重试"""
    for i in range(10):
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
            r.ping()
            return r
        except (redis.ConnectionError, redis.exceptions.ConnectionError):
            print(f"⏳ 等待 Redis 就绪... ({i + 1}/10)")
            time.sleep(2)
    raise Exception("无法连接到 Redis")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Redis 计数器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 700px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        .counter {
            font-size: 72px;
            font-weight: bold;
            color: #e74c3c;
            margin: 30px 0;
        }
        .info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: left; }
        .info li { margin: 5px 0; }
        .refresh-btn {
            background: #3498db; color: white; border: none;
            padding: 12px 30px; border-radius: 5px; cursor: pointer; font-size: 16px;
        }
        .refresh-btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <h1>🔢 Redis 访问计数器</h1>
    <p>每次刷新页面，计数器加 1</p>
    <div class="counter">{{ count }}</div>
    <button class="refresh-btn" onclick="location.reload()">🔄 刷新页面</button>

    <div class="info">
        <h3>📊 统计信息</h3>
        <ul>
            <li>总访问次数: <strong>{{ count }}</strong></li>
            <li>容器主机名: <strong>{{ hostname }}</strong></li>
            <li>Redis 服务器: <strong>{{ redis_host }}:{{ redis_port }}</strong></li>
            <li>Redis 连接状态: <strong>{{ redis_status }}</strong></li>
        </ul>
    </div>

    <div class="info">
        <h3>🔗 可用端点</h3>
        <ul>
            <li><code>GET /</code> - 此页面（带计数器）</li>
            <li><code>GET /api/count</code> - JSON 格式的计数</li>
            <li><code>GET /api/health</code> - 健康检查</li>
            <li><code>POST /api/reset</code> - 重置计数器</li>
        </ul>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    """首页 - 显示访问计数"""
    r = get_redis()
    count = r.incr("page:home:visits")
    hostname = socket.gethostname()

    try:
        redis_info = r.info("server")
        redis_status = "✅ 已连接"
    except Exception:
        redis_status = "❌ 连接失败"

    return render_template_string(
        HTML_TEMPLATE,
        count=count,
        hostname=hostname,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        redis_status=redis_status,
    )


@app.route("/api/count")
def get_count():
    """获取当前计数"""
    r = get_redis()
    count = r.get("page:home:visits") or 0
    return jsonify({"visits": int(count)})


@app.route("/api/reset", methods=["POST"])
def reset_count():
    """重置计数器"""
    r = get_redis()
    r.set("page:home:visits", 0)
    return jsonify({"message": "计数器已重置", "visits": 0})


@app.route("/api/health")
def health():
    """健康检查"""
    try:
        r = get_redis()
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return jsonify(
        {
            "status": "healthy" if redis_ok else "degraded",
            "redis": "connected" if redis_ok else "disconnected",
            "hostname": socket.gethostname(),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 应用启动在 http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
