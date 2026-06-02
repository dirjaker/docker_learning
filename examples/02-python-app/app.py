"""
Flask 应用示例
演示如何将一个标准 Flask 应用 Docker 化
"""
import os
import time
import platform
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# 记录启动时间
START_TIME = time.time()

# HTML 模板
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Flask Docker App</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .card { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .endpoint { background: #e8f5e9; padding: 10px; border-left: 4px solid #4caf50; margin: 10px 0; }
        code { background: #fff; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🐍 Flask Docker App</h1>
    <p>这是一个 Docker 化的 Flask 应用示例。</p>

    <div class="card">
        <h3>📋 可用端点</h3>
        <div class="endpoint">
            <code>GET /</code> - 此页面
        </div>
        <div class="endpoint">
            <code>GET /api/info</code> - 系统信息
        </div>
        <div class="endpoint">
            <code>GET /api/health</code> - 健康检查
        </div>
        <div class="endpoint">
            <code>GET /api/stats</code> - 运行统计
        </div>
    </div>

    <div class="card">
        <h3>📊 环境信息</h3>
        <ul>
            <li>Python: {{ python_version }}</li>
            <li>Platform: {{ platform }}</li>
            <li>Hostname: {{ hostname }}</li>
            <li>Environment: {{ env }}</li>
        </ul>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    """首页"""
    return render_template_string(
        HOME_TEMPLATE,
        python_version=platform.python_version(),
        platform=platform.platform(),
        hostname=os.environ.get("HOSTNAME", "unknown"),
        env=os.environ.get("FLASK_ENV", "production"),
    )


@app.route("/api/info")
def info():
    """系统信息接口"""
    return jsonify(
        {
            "application": "Flask Docker App",
            "version": "1.0.0",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": os.environ.get("HOSTNAME", "unknown"),
            "environment": os.environ.get("FLASK_ENV", "production"),
        }
    )


@app.route("/api/health")
def health():
    """健康检查接口"""
    return jsonify({"status": "healthy", "timestamp": time.time()})


@app.route("/api/stats")
def stats():
    """运行统计接口"""
    uptime = time.time() - START_TIME
    return jsonify(
        {
            "uptime_seconds": round(uptime, 2),
            "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"🚀 Flask 应用启动在 http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
