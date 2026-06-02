"""
Worker 后台任务处理器
从 RabbitMQ 消费任务，处理后将结果发送回结果队列
"""
import os
import time
import json
import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
TASK_QUEUE = "task_queue"
RESULT_QUEUE = "result_queue"


def get_connection():
    """获取 RabbitMQ 连接，带重试机制"""
    for i in range(20):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"⏳ 等待 RabbitMQ 就绪... ({i + 1}/20)")
            time.sleep(3)
    raise Exception("无法连接到 RabbitMQ")


def process_task(task_data):
    """
    处理任务的业务逻辑
    这里模拟一个耗时任务
    """
    task_id = task_data.get("task_id")
    task_name = task_data.get("name", "未知任务")
    print(f"⚙️  正在处理任务: {task_name} (ID: {task_id})")

    # 模拟处理时间
    processing_time = 2
    time.sleep(processing_time)

    # 返回处理结果
    result = {
        "task_id": task_id,
        "result": {
            "message": f"任务 '{task_name}' 处理完成",
            "processing_time": processing_time,
            "processed_at": time.time(),
            "worker": os.environ.get("HOSTNAME", "worker"),
        },
    }
    print(f"✅ 任务完成: {task_id}")
    return result


def send_result(channel, result):
    """将结果发送到结果队列"""
    channel.queue_declare(queue=RESULT_QUEUE, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=RESULT_QUEUE,
        body=json.dumps(result),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print(f"📤 结果已发送: {result.get('task_id')}")


def main():
    """主函数：监听任务队列并处理任务"""
    print("🔧 Worker 启动中...")

    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=TASK_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)  # 一次只处理一个任务

    def callback(ch, method, properties, body):
        try:
            task_data = json.loads(body)
            print(f"📥 收到任务: {task_data.get('task_id')}")

            # 处理任务
            result = process_task(task_data)

            # 发送结果
            send_result(ch, result)

            # 确认消息已处理
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"❌ 处理任务失败: {e}")
            # 拒绝消息，重新入队
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=TASK_QUEUE, on_message_callback=callback)

    print(f"🚀 Worker 已就绪，等待任务...")
    print(f"   RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print(f"   监听队列: {TASK_QUEUE}")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n🛑 Worker 已停止")
        channel.stop_consuming()
        connection.close()


if __name__ == "__main__":
    main()
