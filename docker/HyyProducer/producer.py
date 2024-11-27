import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

# Create a durable queue
channel.queue_declare(queue='task_queue', durable=True)

# Send different data tasks
def send_task(data):
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=data,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        )
    )
    
    
list_to_send = []
for i in range(100):
    temp = []
    for j in range(3):
        temp.append(i * 3 + j)
    list_to_send.append(temp)
    
    
for data in list_to_send:
    send_task(str(data))
    print(f"Sent: {data}")
