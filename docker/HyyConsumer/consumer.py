import pika
import time


connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
# Ensure fair dispatch
channel.basic_qos(prefetch_count=1)

def process_data(ch, method, properties, body):
    # Your data processing logic here
    print(f"Processing: {body}")
    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)
    
    # Simulate a long task
    time.sleep(0.4)

channel.basic_consume(queue='task_queue', on_message_callback=process_data)
channel.start_consuming()