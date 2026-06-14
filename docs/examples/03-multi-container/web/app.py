"""
Web 应用 - 多容器示例
前端 Web 服务，通过消息队列与 Worker 通信
"""
import os
import time
import json
import uuid
import threading
import pika
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# 任务存储（内存中，演示用）
tasks = {}

# RabbitMQ 连接配置
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
TASK_QUEUE = "task_queue"
RESULT_QUEUE = "result_queue"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>多容器应用</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; padding: 20px; }
        .task-form { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .task-list { margin: 20px 0; }
        .task-item { background: #fff; border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .status-pending { color: #ff9800; }
        .status-processing { color: #2196f3; }
        .status-completed { color: #4caf50; }
        button { background: #4caf50; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #45a049; }
        input, textarea { padding: 8px; width: 100%; margin: 5px 0; box-sizing: border-box; }
    </style>
</head>
<body>
    <h1>📦 多容器任务处理系统</h1>
    <p>Web 前端 + Worker 后端，通过 RabbitMQ 消息队列通信</p>

    <div class="task-form">
        <h3>提交新任务</h3>
        <form id="taskForm">
            <input type="text" id="taskName" placeholder="任务名称" required>
            <textarea id="taskData" placeholder="任务数据（JSON 格式）" rows="3">{"key": "value"}</textarea>
            <button type="submit">提交任务</button>
        </form>
    </div>

    <div class="task-list">
        <h3>任务列表</h3>
        <div id="tasks">加载中...</div>
    </div>

    <script>
        document.getElementById('taskForm').onsubmit = async (e) => {
            e.preventDefault();
            const name = document.getElementById('taskName').value;
            let data;
            try {
                data = JSON.parse(document.getElementById('taskData').value);
            } catch {
                data = {raw: document.getElementById('taskData').value};
            }
            const resp = await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, data})
            });
            const result = await resp.json();
            if (result.task_id) {
                document.getElementById('taskName').value = '';
                loadTasks();
            }
        };

        async function loadTasks() {
            const resp = await fetch('/api/tasks');
            const data = await resp.json();
            const container = document.getElementById('tasks');
            if (Object.keys(data).length === 0) {
                container.innerHTML = '<p>暂无任务</p>';
                return;
            }
            container.innerHTML = Object.entries(data).map(([id, task]) => `
                <div class="task-item">
                    <strong>${task.name}</strong>
                    <span class="status-${task.status}">[${task.status}]</span>
                    <br><small>ID: ${id}</small>
                    ${task.result ? '<br><code>' + JSON.stringify(task.result) + '</code>' : ''}
                </div>
            `).join('');
        }

        loadTasks();
        setInterval(loadTasks, 3000);
    </script>
</body>
</html>
"""


def get_rabbitmq_connection():
    """获取 RabbitMQ 连接"""
    for i in range(10):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"⏳ 等待 RabbitMQ 就绪... ({i + 1}/10)")
            time.sleep(3)
    raise Exception("无法连接到 RabbitMQ")


def publish_task(task_id, task_data):
    """将任务发布到消息队列"""
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=TASK_QUEUE, durable=True)
        message = json.dumps({"task_id": task_id, **task_data})
        channel.basic_publish(
            exchange="",
            routing_key=TASK_QUEUE,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),  # 持久化消息
        )
        connection.close()
        print(f"📤 任务已发布: {task_id}")
    except Exception as e:
        print(f"❌ 发布任务失败: {e}")


def start_result_consumer():
    """在后台线程中监听结果队列"""
    def callback(ch, method, properties, body):
        try:
            result = json.loads(body)
            task_id = result.get("task_id")
            if task_id in tasks:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = result.get("result")
                print(f"✅ 任务完成: {task_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"❌ 处理结果失败: {e}")

    def consume():
        for i in range(10):
            try:
                connection = get_rabbitmq_connection()
                channel = connection.channel()
                channel.queue_declare(queue=RESULT_QUEUE, durable=True)
                channel.basic_consume(queue=RESULT_QUEUE, on_message_callback=callback)
                print("📥 结果监听器已启动")
                channel.start_consuming()
            except Exception as e:
                print(f"⏳ 结果监听器重试中... ({i + 1}/10): {e}")
                time.sleep(3)

    thread = threading.Thread(target=consume, daemon=True)
    thread.start()


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.json
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {
        "name": data.get("name", "未命名任务"),
        "data": data.get("data", {}),
        "status": "pending",
        "created_at": time.time(),
        "result": None,
    }
    # 发布任务到消息队列
    publish_task(task_id, tasks[task_id])
    tasks[task_id]["status"] = "processing"
    return jsonify({"task_id": task_id, "status": "processing"})


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "web"})


if __name__ == "__main__":
    print("🚀 Web 应用启动中...")
    start_result_consumer()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
