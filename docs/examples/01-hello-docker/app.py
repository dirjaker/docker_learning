"""
最简单的 Docker 应用示例
一个基本的 Python HTTP 服务器，无需任何外部依赖
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys


class HelloHandler(BaseHTTPRequestHandler):
    """处理 HTTP 请求的处理器"""

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/" or self.path == "/hello":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            hostname = os.environ.get("HOSTNAME", "unknown")
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Hello Docker</title></head>
            <body>
                <h1>🐳 Hello, Docker!</h1>
                <p>这是一个运行在 Docker 容器中的简单 Web 应用。</p>
                <p>容器主机名: <strong>{hostname}</strong></p>
                <p>Python 版本: <strong>{sys.version.split()[0]}</strong></p>
                <hr>
                <p><a href="/info">查看系统信息</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif self.path == "/info":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            info = {
                "hostname": os.environ.get("HOSTNAME", "unknown"),
                "python_version": sys.version,
                "platform": sys.platform,
                "message": "Hello from Docker! 🐳",
            }
            self.wfile.write(json.dumps(info, indent=2, ensure_ascii=False).encode("utf-8"))

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 - Page Not Found")

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HelloHandler)
    print(f"🚀 服务器启动在 http://0.0.0.0:{port}")
    print("按 Ctrl+C 停止服务器")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
